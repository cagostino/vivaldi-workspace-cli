# src/vivaldi_workspace_cli/automator.py
import subprocess
import platform
import os
import time
import sys
try:
    import pyautogui
    # Configure PyAutoGUI pauses (optional but can help stability)
    # pyautogui.PAUSE = 0.1 # Pause between all pyautogui calls
    # pyautogui.FAILSAFE = True # Move mouse to corner to abort
except ImportError:
    print("ERROR: PyAutoGUI library not found.", file=sys.stderr)
    print("Please install it: pip install PyAutoGUI", file=sys.stderr)
    print("You might also need OS dependencies (see README/setup-info).", file=sys.stderr)
    sys.exit(1)
except Exception as e:
     # Catch other potential pyautogui import errors (e.g., display issues on Linux)
     print(f"ERROR: Failed to import or initialize PyAutoGUI: {e}", file=sys.stderr)
     print("Ensure you have a graphical environment and necessary OS dependencies.", file=sys.stderr)
     sys.exit(1)


# Delay in seconds to wait for Vivaldi to launch before sending FIRST shortcut
LAUNCH_DELAY = 2.5 # User might want this configurable later
# Short delay between sending workspace switch and next tab shortcut
SWITCH_DELAY = 0.3 # User might want this configurable later

# --- Vivaldi Executable Finder ---
def find_vivaldi_executable():
    """Tries to find the Vivaldi executable path."""
    system = platform.system()
    # Use platform-specific commands first if available
    try:
        if system == "Windows":
             # 'where' is more reliable on Windows for finding executables in PATH
             result = subprocess.run(['where', 'vivaldi'], capture_output=True, text=True, check=True, shell=True)
             paths = result.stdout.strip().split('\n')
             for path in paths:
                 if path and os.path.exists(path.strip()) and path.strip().lower().endswith("vivaldi.exe"):
                      return path.strip()
        elif system == "Darwin":
            # Check default path first
             default_path = "/Applications/Vivaldi.app/Contents/MacOS/Vivaldi"
             if os.path.exists(default_path): return default_path
             # Fallback to 'which'
             result = subprocess.run(['which', 'vivaldi'], capture_output=True, text=True, check=True)
             path = result.stdout.strip()
             if path and os.path.exists(path): return path
        else: # Linux
             # Check common paths first
             common_paths = ["/usr/bin/vivaldi-stable", "/usr/bin/vivaldi", "/snap/bin/vivaldi", "/opt/vivaldi/vivaldi"]
             for path in common_paths:
                 if path and os.path.exists(path): return path
             # Fallback to 'which'
             result = subprocess.run(['which', 'vivaldi'], capture_output=True, text=True, check=True)
             path = result.stdout.strip()
             if path and os.path.exists(path): return path

    except (FileNotFoundError, subprocess.CalledProcessError):
        # which/where not found or vivaldi not found via them
        pass # Proceed to checking hardcoded paths if needed

    # If 'which'/'where' failed, check hardcoded paths (redundant for Linux/Mac if common_paths checked)
    if system == "Windows":
        possible_paths = [
            os.path.join(os.getenv('LOCALAPPDATA', ''), 'Vivaldi\\Application\\vivaldi.exe'),
            os.path.join(os.getenv('ProgramFiles', ''), 'Vivaldi\\Application\\vivaldi.exe'),
            os.path.join(os.getenv('ProgramFiles(x86)', ''), 'Vivaldi\\Application\\vivaldi.exe')
        ]
        for path in possible_paths:
            if path and os.path.exists(path): return path

    # If still not found
    return None


def activate_vivaldi_window():
    """Tries to find and activate a Vivaldi window using PyAutoGUI (best effort)."""
    print("Attempting to activate Vivaldi window (best effort)...")
    system = platform.system()
    try:
        # PyAutoGUI window finding is basic and OS-dependent title matching.
        # Vivaldi's title might change based on active tab or profile.
        # Try common patterns.
        possible_titles = ["Vivaldi"]
        # Add profile name if easily accessible? Hard to do reliably here.
        # Maybe get active window title and check if 'Vivaldi' is in it?

        target_window = None
        all_windows = pyautogui.getAllWindows()
        for window in all_windows:
            # Case-insensitive check
            if window.title and "vivaldi" in window.title.lower():
                # Prioritize non-minimized windows if possible
                if hasattr(window, 'isMinimized') and not window.isMinimized:
                    target_window = window
                    break
                elif target_window is None: # Keep first match if all are minimized/unknown
                    target_window = window

        if target_window:
            print(f"Found potential Vivaldi window: '{target_window.title}'. Activating...")
            # Different ways to activate depending on OS and window state
            try:
                 if system == "Windows" and hasattr(target_window, 'activate'):
                     if hasattr(target_window, 'isMinimized') and target_window.isMinimized:
                         target_window.restore()
                         time.sleep(0.1)
                     target_window.activate()
                 elif system == "Darwin" and hasattr(target_window, 'activate'): # macOS often needs activate
                     target_window.activate()
                 elif hasattr(target_window, 'focus'): # Generic fallback
                     target_window.focus()
                 elif hasattr(target_window, 'click'): # Last resort - click center? Risky.
                     target_window.click(duration=0.1)
                 else:
                     print("  No standard activation method found for this window object.")
                     return False # Indicate failure

                 time.sleep(0.3) # Wait a bit after trying to activate
                 # Verify? Hard to do reliably. Assume it worked for now.
                 print("  Activation attempted.")
                 return True

            except Exception as activate_err:
                 print(f"  Warning: Error during window activation attempt: {activate_err}")
                 return False # Activation likely failed
        else:
            print("Warning: Could not find a suitable Vivaldi window by title.")
            return False # Indicate failure to find window
    except Exception as e:
        print(f"ERROR during window search/activation: {e}")
        return False


def send_shortcut(shortcut_str):
     """Sends a keyboard shortcut using pyautogui."""
     # Expects format like "ctrl+alt+1" or "command+shift+k"
     keys = [key.strip() for key in shortcut_str.lower().split('+')]
     print(f"Sending shortcut via PyAutoGUI: {keys}")
     try:
         # Use press() for single keys, hotkey() for combinations
         if len(keys) == 1:
             pyautogui.press(keys[0])
         else:
             pyautogui.hotkey(*keys) # Unpack keys into hotkey arguments
         print("Shortcut sent.")
         return True
     except Exception as e:
          print(f"ERROR sending shortcut '{shortcut_str}' via PyAutoGUI: {e}", file=sys.stderr)
          # Common issue: KeyNotFoundException if key name is wrong
          if "KeyNotFoundException" in str(e):
              print("      Check key names against PyAutoGUI documentation!", file=sys.stderr)
          return False

# --- Main Automation Action ---
def launch_switch_and_next_tab(workspace_name, shortcut_map):
    """Launches Vivaldi and uses pyautogui to send shortcuts."""

    vivaldi_exe = find_vivaldi_executable()
    if not vivaldi_exe:
        print("ERROR: Vivaldi executable not found.", file=sys.stderr)
        return False

    workspace_shortcut_str = shortcut_map.get(workspace_name)
    if not workspace_shortcut_str:
        print(f"ERROR: Shortcut for workspace '{workspace_name}' not found in config file.", file=sys.stderr)
        return False

    # Define Next Tab shortcut (PyAutoGUI uses lowercase key names)
    system = platform.system()
    if system == "Darwin":
        # macOS convention - 'command' might map to 'cmd' in pyautogui
        # Ctrl+Tab is often secondary binding
        next_tab_shortcut_str = "ctrl+tab" # Test if this works, or try specific key code if needed
    else: # Linux/Windows default
        next_tab_shortcut_str = "ctrl+tab" # Or 'ctrl+pagedown'

    print(f"\nAttempting to launch Vivaldi and switch to '{workspace_name}'...")
    try:
        process = subprocess.Popen([vivaldi_exe])
        print(f"Vivaldi process started. Waiting {LAUNCH_DELAY} seconds...")
    except Exception as e:
        print(f"ERROR launching Vivaldi: {e}", file=sys.stderr)
        return False

    time.sleep(LAUNCH_DELAY)

    # --- Activate Window and Send Shortcuts ---
    if not activate_vivaldi_window():
        print("Warning: Failed to activate Vivaldi window. Shortcuts might go to the wrong place.")
        # Continue anyway, maybe it got focus automatically

    print("\nSending Workspace Shortcut...")
    success_switch = send_shortcut(workspace_shortcut_str)

    if success_switch:
        print(f"Waiting {SWITCH_DELAY}s before sending 'Next Tab'...")
        time.sleep(SWITCH_DELAY)
        print("Sending Next Tab Shortcut...")
        success_next_tab = send_shortcut(next_tab_shortcut_str)
    else:
        success_next_tab = False # Can't send next tab if switch failed

    # --- Report Results ---
    print("\n--- Process Summary ---")
    if success_switch: print(f"[OK] Sent shortcut to switch to '{workspace_name}'.")
    else: print(f"[FAIL] Failed to send shortcut for '{workspace_name}'.")

    if success_next_tab: print(f"[OK] Sent 'Next Tab' shortcut.")
    elif success_switch: print(f"[FAIL] Failed to send 'Next Tab' shortcut.")

    if success_switch and success_next_tab:
        print("\nVivaldi should now be in the correct workspace and focused on a non-trigger tab.")
        return True
    else:
        print("\nSwitch may not have completed successfully.")
        return False