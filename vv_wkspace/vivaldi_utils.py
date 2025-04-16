# src/vivaldi_workspace_cli/vivaldi_utils.py
import os
import platform
import json
import re
import sys

def find_profile_path():
    """Finds the default Vivaldi profile path."""
    system = platform.system()
    home = os.path.expanduser("~")
    profile_dir = "Default"
    try:
        if system == "Windows":
            profile_base = os.path.join(os.getenv('LOCALAPPDATA', ''), 'Vivaldi', 'User Data')
        elif system == "Darwin":
            profile_base = os.path.join(home, 'Library', 'Application Support', 'Vivaldi')
        else: # Linux
            profile_base = os.path.join(home, '.config', 'vivaldi')

        path = os.path.join(profile_base, profile_dir)
        if os.path.exists(path):
            return path
        elif os.path.exists(profile_base) and system != "Windows":
            print(f"Warning: Default profile dir not found at '{path}'. Using base: '{profile_base}'. Check profile name.", file=sys.stderr)
            return profile_base # Might need refinement for multi-profile users
        elif not os.path.exists(profile_base):
            print(f"Error: Vivaldi profile base directory not found at '{profile_base}'.", file=sys.stderr)
            return None
        else: # Base exists, but Default doesn't (maybe Windows non-Default?)
             print(f"Error: Default profile directory not found at '{path}'. Specify profile path if needed.", file=sys.stderr)
             return None
    except Exception as e:
        print(f"Error determining profile path: {e}", file=sys.stderr)
        return None

def get_workspaces_from_prefs(profile_path):
    """Reads Preferences file and extracts workspace names only."""
    if not profile_path:
        return None

    prefs_file = os.path.join(profile_path, 'Preferences')
    if not os.path.exists(prefs_file):
        print(f"Warning: Preferences file not found at '{prefs_file}'. Cannot list names from Vivaldi.", file=sys.stderr)
        return None
    try:
        with open(prefs_file, 'r', encoding='utf-8') as f:
            content = f.read()
            # Robust cleaning attempt
            content = ''.join(c for c in content if c.isprintable() or c.isspace())
            content = re.sub(r',\s*([\}\]])', r'\1', content) # Fix trailing commas
            prefs_data = json.loads(content)

        # Safely navigate the dictionary
        workspaces = prefs_data.get("vivaldi", {}).get("workspaces", {}).get("list", [])
        if not isinstance(workspaces, list):
            print(f"Warning: Workspace data in Preferences is not a list.", file=sys.stderr)
            return [] # Return empty list

        names = [ws.get("name") for ws in workspaces if ws.get("name")]
        return names

    except json.JSONDecodeError as e:
         print(f"Warning: Could not decode Preferences JSON: {e}. Ensure Vivaldi is closed?", file=sys.stderr)
         return None
    except Exception as e:
        print(f"Warning: Error reading Preferences for workspace names: {e}", file=sys.stderr)
        return None