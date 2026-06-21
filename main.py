import argparse
import json
import os
import re
import sys
import winreg


class LuaBuilder:
    project_path: str
    config_path: str

    def __init__(self, project_path: str) -> None:
        self.project_path = os.path.abspath(project_path)
        self.config_path = os.path.join(self.project_path, "config.json")

    def create_project(self, build_names: list[str]) -> None:
        os.makedirs(self.project_path, exist_ok=True)
        config = {name: idx for idx, name in enumerate(build_names)}

        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)

        print("Generated Configuration:")
        print(json.dumps(config, indent=4))

    def load_config(self) -> dict[str, int]:
        if not os.path.exists(self.config_path):
            print(
                f"Error: Configuration file '{self.config_path}' not found.",
                file=sys.stderr,
            )
            raise SystemExit(1)

        with open(self.config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)

            if not isinstance(config_data, dict):
                print(
                    f"Error: Invalid configuration format in '{self.config_path}'.",
                    file=sys.stderr,
                )
                raise SystemExit(1)

            result: dict[str, int] = {}
            for k, v in config_data.items():
                if isinstance(k, str) and isinstance(v, int):
                    result[k] = v

            return result

    def evaluate_condition(self, condition: str, level: int) -> bool:
        try:
            return bool(eval(condition, {"__builtins__": {}}, {"_LEVEL": level}))
        except Exception as e:
            print(
                f"Error evaluating condition '{condition}' with _LEVEL={level}: {e}",
                file=sys.stderr,
            )

            raise SystemExit(1)

    def preprocess(self, code: str, level: int) -> str:
        pattern = re.compile(
            r"--\s*#ifdef\s+([^\r\n]+?)\r?\n((?:(?!--\s*#ifdef).)*?)\r?\n\s*--\s*#endif",
            re.DOTALL,
        )

        while True:
            match = pattern.search(code)

            if not match:
                break

            condition = match.group(1).strip()
            body = match.group(2)
            replacement = body if self.evaluate_condition(condition, level) else ""
            code = code[: match.start()] + replacement + code[match.end() :]

        return code

    def build_project(self, file_name: str) -> None:
        input_path = os.path.join(self.project_path, file_name)

        if not os.path.exists(input_path):
            print(f"Error: Input file '{input_path}' not found.", file=sys.stderr)
            raise SystemExit(1)

        config = self.load_config()

        with open(input_path, "r", encoding="utf-8") as f:
            code = f.read()

        builds_dir = os.path.join(self.project_path, "builds")
        os.makedirs(builds_dir, exist_ok=True)

        project_name = os.path.basename(self.project_path)

        for build_name, build_id in config.items():
            preprocessed_code = self.preprocess(code, build_id)
            if re.search(r"\blocal\s+_LEVEL\b", preprocessed_code):
                output_code = re.sub(
                    r"\blocal\s+_LEVEL\b(?:\s*=\s*[^\r\n]+)?",
                    f"local _LEVEL = {build_id}",
                    preprocessed_code,
                )
            else:
                output_code = f"local _LEVEL = {build_id}\n\n{preprocessed_code}"

            output_path = os.path.join(builds_dir, f"{project_name}_{build_name}.lua")
            with open(output_path, "w", encoding="utf-8") as f:
                _ = f.write(output_code)
            print(f"Successfully built: {output_path}")

    def install_to_path(self) -> None:
        cmd_path = os.path.join(self.project_path, "lua-slicex.cmd")
        cmd_content = '@echo off\npy "%~dp0main.py" %*\n'

        with open(cmd_path, "w", encoding="utf-8") as f:
            _ = f.write(cmd_content)

        print(f"Created: {cmd_path}")

        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_ALL_ACCESS
            )

            try:
                val, val_type = winreg.QueryValueEx(key, "Path")
            except FileNotFoundError:
                val, val_type = "", winreg.REG_SZ

            if not isinstance(val, str):
                val = ""

            paths = [p.strip() for p in val.split(";") if p.strip()]

            if self.project_path not in paths:
                paths.append(self.project_path)
                new_val = ";".join(paths)
                winreg.SetValueEx(key, "Path", 0, val_type, new_val)

                print(f"Added '{self.project_path}' to User PATH.")
                print(
                    "Please restart your terminal/IDE for the changes to take effect."
                )
            else:
                print(f"'{self.project_path}' is already in User PATH.")
            winreg.CloseKey(key)
        except Exception as e:
            print(f"Failed to add to PATH: {e}", file=sys.stderr)
            raise SystemExit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Lua Build Automation Tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_parser = subparsers.add_parser("create", help="Create or modify project configuration.")
    _ = create_parser.add_argument("project_path", type=str, help="Path to the project directory.")
    _ = create_parser.add_argument("build_names", nargs="+", type=str, help="Names of the builds (e.g., stable beta debug).")

    upload_parser = subparsers.add_parser("upload", help="Build and preprocess a Lua script.")
    _ = upload_parser.add_argument("project_path", type=str, help="Path to the project directory.")
    _ = upload_parser.add_argument("file_name", type=str, help="Name of the file to build.")

    _ = subparsers.add_parser("install", help="Install lua-slicex to user PATH environment variable.")

    args = parser.parse_args()

    command = args.command
    if not isinstance(command, str):
        return

    if command == "install":
        builder = LuaBuilder(os.path.dirname(os.path.abspath(__file__)))
        builder.install_to_path()
        return

    project_path = getattr(args, "project_path", None)
    if not isinstance(project_path, str):
        return

    builder = LuaBuilder(project_path)
    if command == "create":
        build_names = getattr(args, "build_names", None)
        if not isinstance(build_names, list):
            return
        builder.create_project([name for name in build_names if isinstance(name, str)])
    elif command == "upload":
        file_name = getattr(args, "file_name", None)
        if not isinstance(file_name, str):
            return
        builder.build_project(file_name)


if __name__ == "__main__":
    main()
