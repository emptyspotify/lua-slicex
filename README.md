# lua-slicex

`lua-slicex` is a clean, minimal, and production-ready CLI Lua build automation tool written in Python. It helps you manage project configurations, conditional preprocessing, and generates builds targeted at different level configurations (e.g., stable, beta, debug) from a single codebase.

---

## Features
- **Zero Dependencies**: Powered entirely by the Python standard library.
- **Conditional Preprocessing**: Supports C++ style `-- #ifdef <condition>` and `-- #endif` blocks.
- **Automatic Variables**: Injects a global variable `local _LEVEL = <build_id>` into each build.
- **Windows Integration**: Includes a built-in command to register itself to your system `PATH` for easy execution from anywhere.

---

## Installation

### Prerequisites
Make sure Python 3.9 or higher is installed and added to your system path.

### 1. Download/Clone
Copy the project folder to a directory of your choice on your local machine (e.g. `C:\tools\lua-slicex`).

### 2. Add to PATH (Windows)
Open a terminal in the folder containing `main.py` and run:
```bash
py main.py install
```
This command automatically:
1. Generates a helper executable `lua-slicex.cmd`.
2. Registers the installation directory in your User `PATH` environment variable.

*Note: Restart your terminal/IDE for the changes to take effect.*

---

## CLI Usage

Once added to your PATH, you can run `lua-slicex` from any directory.

### 1. Create or Modify a Project
Initialize or overwrite a project configuration (`config.json`) with your target builds.
```bash
lua-slicex create <project_path> <build_names...>
```
**Example:**
```bash
lua-slicex create my_game stable beta debug
```
This will create a `my_game/config.json` mapping:
```json
{
    "stable": 0,
    "beta": 1,
    "debug": 2
}
```

### 2. Build and Preprocess a File
Generate preprocessed Lua files for each build configured in your project.
```bash
lua-slicex upload <project_path> <file_name>
```
**Example:**
```bash
lua-slicex upload my_game main.lua
```
This generates the following files inside `my_game/builds/`:
- `my_game_stable.lua` (with `_LEVEL = 0`)
- `my_game_beta.lua` (with `_LEVEL = 1`)
- `my_game_debug.lua` (with `_LEVEL = 2`)

---

## Preprocessor Syntax

Conditional statements use the `-- #ifdef <condition>` syntax. Conditions are evaluated safely against the current `_LEVEL` value.

### Syntax Example:
```lua
-- If _LEVEL is not declared in the file, it will be injected automatically.
-- If it is already declared (e.g., local _LEVEL = 0), its value will be updated in-place.
local _LEVEL = 0

local auto_teleport = group:checkbox("Auto teleport")
auto_teleport:disabled(_LEVEL > 0)

-- #ifdef _LEVEL == 0
print("Stable branch functionality activated.")
-- #endif

-- #ifdef _LEVEL > 0
print("Beta/Debug features enabled.")
-- #endif
```

---

## Command Help
You can access details about commands using the `-h` or `--help` flag:
```bash
lua-slicex --help
lua-slicex create --help
lua-slicex upload --help
```
