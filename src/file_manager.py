import json
import datetime
import os

from config import registry_file, audit_log_file

# Create data directory if it doesn't exist
os.makedirs(os.path.dirname(registry_file), exist_ok=True)

def save_registry(registry, filepath=registry_file):
    """Save the patient registry to a JSON file"""
    try:
        with open(filepath, "w") as f:
            json.dump(registry, f, indent=4)
        print(f"✅ Registry saved to {filepath}")
        return True
    except FileNotFoundError:
        print(f"❌ Saved failed: folder for '{filepath}' does not exist.")
        return False
    except Exception as e:
        print(f"❌ Save failed: {e}")
        return False

def load_registry(filepath=registry_file):
    """Load the patient registry from a JSON file.
    return an empty dict if the file doesn't exist yet"""
    try:
        with open(filepath, "r") as f:
            registry = json.load(f)
        print(f"✅ Registry loaded from {filepath} ({len(registry)} patients)")
        return registry
    except FileNotFoundError:
        print(f"⚠ No saved registry found at {filepath}. Starting fresh.")
        return {}
    except json.JSONDecodeError:
        print(f"❌ registry file is corrupted. Starting fresh.")
        return {}
    except Exception as e:
        print(f"❌ Load failed: {e}")
        return {}
  
def log_action(action_description):
    """Append a timestamped action to the medical audit log."""
    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(audit_log_file, "a") as f:
            f.write(f"[{timestamp}] {action_description}\n")
        return True
    except Exception as e:
        print(f"⚠  Audit log failed: {e}")
        return False