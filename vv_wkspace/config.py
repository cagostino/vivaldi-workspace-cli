# src/vivaldi_workspace_cli/config.py
import json
import os
import platform
import sys

DEFAULT_CONFIG_FILENAME = "config.json"

def get_config_dir():
    """Gets the platform-specific config directory."""
    system = platform.system()
    if system == "Windows":
        # Use APPDATA for consistency with many user configs
        return os.path.join(os.getenv('APPDATA', ''), "vivaldi-workspace-cli")
    elif system == "Darwin": # macOS
        # Standard macOS user config location
        return os.path.join(os.path.expanduser("~"), "Library", "Application Support", "vivaldi-workspace-cli")
    else: # Linux/Other following XDG Base Directory Specification (usually ~/.config)
        xdg_config_home = os.getenv('XDG_CONFIG_HOME', os.path.join(os.path.expanduser("~"), ".config"))
        return os.path.join(xdg_config_home, "vivaldi-workspace-cli")

def get_config_path():
    """Gets the full path to the config file."""
    return os.path.join(get_config_dir(), DEFAULT_CONFIG_FILENAME)

def load_config():
    """Loads the shortcut map from the config file."""
    config_path = get_config_path()
    if not os.path.exists(config_path):
        print(f"ERROR: Config file not found at '{config_path}'", file=sys.stderr)
        print(f"Please run 'vivaldi_workspace config init' to create a sample.", file=sys.stderr)
        return None

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            # Allow comments starting with //
            lines = [line for line in f if not line.strip().startswith('//')]
            config_data = json.loads("".join(lines))

        if "workspace_shortcuts" not in config_data or not isinstance(config_data["workspace_shortcuts"], dict):
            print(f"ERROR: Config file '{config_path}' is missing or has invalid 'workspace_shortcuts' dictionary.", file=sys.stderr)
            return None

        # Basic validation of shortcuts
        valid_shortcuts = {}
        has_errors = False
        for name, shortcut in config_data["workspace_shortcuts"].items():
            if isinstance(shortcut, str) and shortcut.strip():
                valid_shortcuts[name] = shortcut.strip().lower() # Store lowercase for pyautogui
            else:
                 print(f"Warning: Invalid or empty shortcut for workspace '{name}' in config. Skipping.", file=sys.stderr)
                 has_errors = True

        if has_errors:
             print("Please correct the errors in the config file.", file=sys.stderr)
             # Decide if you want to return None or the partially valid map
             # return None # Stricter
             return valid_shortcuts # More lenient

        return valid_shortcuts

    except json.JSONDecodeError as e:
        print(f"ERROR: Config file '{config_path}' contains invalid JSON: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"ERROR loading config file '{config_path}': {e}", file=sys.stderr)
        return None

def init_config(workspace_names=None):
    """Creates a sample config file if it doesn't exist."""
    config_dir = get_config_dir()
    config_path = get_config_path()

    if os.path.exists(config_path):
        print(f"Config file already exists at '{config_path}'.")
        print("Edit this file to map your workspace names to keyboard shortcuts.")
        return True # Indicate already exists

    print(f"Attempting to create config directory: {config_dir}")
    try:
        os.makedirs(config_dir, exist_ok=True)
    except OSError as e:
        print(f"ERROR: Could not create config directory: {e}", file=sys.stderr)
        return False

    print(f"Creating sample config file: {config_path}")
    # Use triple quotes for multi-line string including comments
    sample_content = """{
    "//": "Map Vivaldi workspace names (case-sensitive) to keyboard shortcuts.",
    "//": "Use '+' to separate keys (e.g., 'ctrl+alt+1', 'command+shift+k').",
    "//": "Keys should be lowercase.",
    "//": "See pyautogui docs for key names: https://pyautogui.readthedocs.io/en/latest/keyboard.html#keyboard-keys",
    "workspace_shortcuts": {
"""
    # Populate with names found in Preferences if available
    shortcuts_dict = {}
    if workspace_names:
        for i, name in enumerate(workspace_names):
             # Use json.dumps to handle escaping quotes in workspace names correctly
             escaped_name = json.dumps(name)
             # Assign a placeholder shortcut - user MUST change this
             placeholder_shortcut = f"ctrl+alt+{i+1}" # Example placeholder
             shortcuts_dict[escaped_name] = json.dumps(placeholder_shortcut)
    else:
         shortcuts_dict['"Example Workspace 1"'] = '"ctrl+alt+1"'
         shortcuts_dict['"Example Workspace 2"'] = '"ctrl+alt+2"'

    # Add entries to sample content string
    shortcut_lines = [f"        {name}: {shortcut}" for name, shortcut in shortcuts_dict.items()]
    sample_content += ",\n".join(shortcut_lines)
    sample_content += "\n    }\n}\n"

    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(sample_content)

        print("\nSample config file created successfully.")
        print(f"IMPORTANT: Edit '{config_path}' and replace placeholder shortcuts")
        print("with the ACTUAL shortcuts (lowercase, '+'-separated) you assigned in Vivaldi settings!")
        return True
    except Exception as e:
        print(f"ERROR writing sample config file: {e}", file=sys.stderr)
        return False