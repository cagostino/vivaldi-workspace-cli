# src/vivaldi_workspace_cli/cli.py
import argparse
import sys
import platform # Import platform here as well

# Import functions from our other modules within the package
from . import config
from . import automator
from . import vivaldi_utils

def main():
    parser = argparse.ArgumentParser(
        prog="vivaldi_workspace", # Set the program name for help messages
        description="CLI tool to launch Vivaldi and switch workspaces using assigned keyboard shortcuts via PyAutoGUI.",
        epilog="Requires manual shortcut assignment in Vivaldi Settings and a config file mapping names to shortcuts."
    )

    subparsers = parser.add_subparsers(dest="action", help="Action to perform", required=True)

    # --- Launch Action ---
    parser_launch = subparsers.add_parser("launch", help="Launch Vivaldi and switch to the specified workspace.")
    parser_launch.add_argument("workspace_name", help="Exact name of the workspace (must exist in config file).")
    # Optional flag to specify config file path (useful for testing or non-standard locations)
    parser_launch.add_argument("-c", "--config", default=config.get_config_path(),
                               help=f"Path to config file (default: {config.get_config_path()})")

    # --- List Action ---
    parser_list = subparsers.add_parser("list", help="List workspaces found in Vivaldi Preferences and mapped in the config.")
    parser_list.add_argument("-c", "--config", default=config.get_config_path(),
                             help=f"Path to config file (default: {config.get_config_path()})")
    # Add optional profile path argument? Maybe later if needed.

    # --- Config Action ---
    parser_config = subparsers.add_parser("config", help="Manage the configuration file.")
    config_subparsers = parser_config.add_subparsers(dest="config_action", help="Config action", required=True)
    # 'config init' command
    parser_config_init = config_subparsers.add_parser("init", help="Create a sample config file if one doesn't exist.")
    parser_config_init.add_argument("-f", "--force", action="store_true",
                                   help="Force creation even if config exists (overwrites!). Use with caution.")
    # 'config path' command
    parser_config_path = config_subparsers.add_parser("path", help="Show the path to the configuration file.")


    # --- Setup Info Action ---
    parser_setup = subparsers.add_parser("setup-info", help="Show required manual setup steps.")

    # --- Parse Arguments ---
    args = parser.parse_args()

    # --- Execute Actions ---
    if args.action == "launch":
        print(f"Attempting to launch workspace: {args.workspace_name}")
        shortcut_map = config.load_config() # Load config using default path or specified one
        if shortcut_map:
            automator.launch_switch_and_next_tab(args.workspace_name, shortcut_map)
        else:
            sys.exit(1) # Exit if config loading failed

    elif args.action == "list":
        print("Listing workspaces...")
        shortcut_map = config.load_config()
        profile_path = vivaldi_utils.find_profile_path()
        names_from_prefs = vivaldi_utils.get_workspaces_from_prefs(profile_path) if profile_path else []
        names_from_prefs = names_from_prefs if names_from_prefs is not None else [] # Ensure it's a list

        print("\nWorkspaces found in Vivaldi Preferences:")
        if not profile_path:
            print("  (Could not find profile path to check Preferences)")
        elif not names_from_prefs:
             print("  (None found or error reading Preferences)")
        else:
            for name in names_from_prefs:
                 print(f"  - {name}")

        print("\nWorkspaces mapped in config file:")
        if shortcut_map is None:
             print("  (Error loading config file)")
        elif not shortcut_map:
            print(f"  (None defined in '{config.get_config_path()}')")
        else:
            for name, shortcut in shortcut_map.items():
                status = "[OK]" if name in names_from_prefs else "[Name Mismatch?]"
                if not profile_path: status = "[Prefs unchecked]" # Adjust status if we couldn't read prefs
                print(f"  - '{name}' -> Shortcut: '{shortcut}' {status}")

        print("\nNOTE: Ensure names in config match Preferences & shortcuts are set in Vivaldi.")


    elif args.action == "config":
        if args.config_action == "init":
            print("Initializing configuration...")
            if not args.force and os.path.exists(config.get_config_path()):
                 print(f"Config file already exists at '{config.get_config_path()}'. Use --force to overwrite.")
                 sys.exit(1)

            profile_path = vivaldi_utils.find_profile_path()
            workspace_names = []
            if profile_path:
                 workspace_names = vivaldi_utils.get_workspaces_from_prefs(profile_path)
                 workspace_names = workspace_names if workspace_names is not None else [] # Ensure list

            if not config.init_config(workspace_names):
                 sys.exit(1) # Exit if init failed

        elif args.config_action == "path":
            print(f"Configuration file path: {config.get_config_path()}")

    elif args.action == "setup-info":
        print("\n--- Manual Setup Required ---")
        print("1. Vivaldi Keyboard Shortcuts:")
        print("   - Go to Vivaldi Settings > Keyboard > Window.")
        print("   - Assign unique shortcuts (e.g., Ctrl+Alt+1) to 'Switch to Workspace X' for each workspace you want to launch.")
        print("   - Note the shortcut for 'Next Tab' (Window > Next Tab) if default doesn't work.")
        print("2. Configure This Tool:")
        print(f"   - Run: 'vivaldi_workspace config init'")
        print(f"   - Edit the created config file at: {config.get_config_path()}")
        print("   - Map your EXACT Vivaldi workspace names to the shortcuts you assigned.")
        print("     Format: use '+' like 'ctrl+alt+1'. See pyautogui key names if needed.")
        print("3. Install PyAutoGUI OS Dependencies (if needed):")
        print("   - Linux: May require `sudo apt-get install scrot python3-tk python3-dev` (Debian/Ubuntu) or similar.")
        print("   - macOS: May require accessibility permissions for terminal/python.")
        print("   - Windows: Usually works out of the box after `pip install pyautogui`.")
        print("-----------------------------")

    else:
        parser.print_help()

if __name__ == '__main__':
    # This allows running the script directly (python src/vivaldi_workspace_cli/cli.py ...)
    # although the intended use is via the installed 'vivaldi_workspace' command.
    main()