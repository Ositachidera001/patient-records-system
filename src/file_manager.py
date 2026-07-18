"""
file_manager.py

Handles all reading/writing to disk: the patient registry (JSON) and the
audit log (plain text). Every function here fails *safely* — errors are
caught, reported, and the program keeps running instead of crashing.
"""
import json
import datetime
import os

from config import registry_file, audit_log_file, DATA_DIR

# Create the data/ directory up front so save_registry() and log_action()
# never fail just because the folder doesn't exist yet.
os.makedirs(DATA_DIR, exist_ok=True)


def save_registry(registry, filepath=registry_file):
    """Save the patient registry to a JSON file. Returns True/False on success."""
    try:
        with open(filepath, "w") as f:
            json.dump(registry, f, indent=4)
        print(f"✅ Registry saved to {filepath}")
        return True
    except FileNotFoundError:
        print(f"❌ Save failed: folder for '{filepath}' does not exist.")
        return False
    except Exception as e:
        print(f"❌ Save failed: {e}")
        return False


def load_registry(filepath=registry_file):
    """Load the patient registry from a JSON file.

    Returns an empty dict if the file doesn't exist yet, or if it exists
    but is corrupted — either way the app should start rather than crash.
    """
    try:
        with open(filepath, "r") as f:
            registry = json.load(f)
        print(f"✅ Registry loaded from {filepath} ({len(registry)} patients)")
        return registry
    except FileNotFoundError:
        print(f"⚠ No saved registry found at {filepath}. Starting fresh.")
        return {}
    except json.JSONDecodeError:
        print(f"❌ Registry file is corrupted. Starting fresh.")
        return {}
    except Exception as e:
        print(f"❌ Load failed: {e}")
        return {}


def log_action(action_description):
    """Append a timestamped entry to the medical audit log. Returns True/False."""
    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(audit_log_file, "a") as f:
            f.write(f"[{timestamp}] {action_description}\n")
        return True
    except Exception as e:
        print(f"⚠  Audit log failed: {e}")
        return False
