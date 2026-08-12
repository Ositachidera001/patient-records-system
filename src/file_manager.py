"""
file_manager.py

Handles all reading/writing to disk: the patient registry (JSON) and the
audit log (plain text). Every function here fails *safely* — errors are
caught, reported, and the program keeps running instead of crashing.
"""
import json
from datetime import datetime
import os
import shutil

from pathlib import Path

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

def backup_registry(src_path: Path, backup_dir: Path) -> Path | None:
    """Create a timestamped copy of the registry JSON using shutil.copy2().
    
    Preserves original file creation and modification metadata.
    """
    try:
        if not src_path.exists():
            raise FileNotFoundError(f"Registry source missing: {src_path}")

        backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        dest_filename = f"{src_path.stem}_{timestamp}{src_path.suffix}"
        dest_path = backup_dir / dest_filename

        shutil.copy2(src_path, dest_path)
        print(f"✅ [Backup] Registry copied to: {dest_path.name}")
        log_action("✅ [Backup] Registry copied to: {dest_path.name}")
        return dest_path

    except FileNotFoundError as err:
        print(f"❌ [Backup Error] {err}")
        log_action("❌ [Backup Error] {err}")
    except PermissionError:
        print(f"❌ [Backup Error] Permission denied accessing {src_path}")
    except Exception as err:
        print(f"❌ [Backup Error] Unexpected error during registry backup: {err}")
    return None


def full_backup(data_dir: Path, backup_root: Path) -> Path | None:
    """Create a full recursive snapshot copy of the patient data folder."""
    try:
        if not data_dir.exists():
            raise FileNotFoundError(f"Data directory missing: {data_dir}")

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        dest_dir = backup_root / f"full_backup_{timestamp}"

        # Copy directory tree
        shutil.copytree(data_dir, dest_dir, dirs_exist_ok=False)
        print(f"✅ [Full Backup] Snapshot created: {dest_dir.name}")
        return dest_dir

    except FileExistsError:
        print(f"❌ [Full Backup Error] Target folder already exists: {dest_dir}")
    except FileNotFoundError as err:
        print(f"❌ [Full Backup Error] {err}")
    except Exception as err:
        print(f"❌ [Full Backup Error] Operation failed: {err}")
    return None


def archive_old_backups(backup_root: Path, keep_latest: int = 3) -> None:
    """List backup folders sorted by creation time, keep the 3 most recent,
    and convert older directories into compressed ZIP archives before removal.
    """
    try:
        if not backup_root.exists():
            return

        # Find all backup directories
        backup_folders = [
            p for p in backup_root.iterdir() 
            if p.is_dir() and p.name.startswith("full_backup_")
        ]
        
        # Sort by creation time (oldest first)
        backup_folders.sort(key=lambda p: p.stat().st_mtime)

        if len(backup_folders) <= keep_latest:
            print(f"ℹ️  [Archive] Total backups ({len(backup_folders)}) <= limit ({keep_latest}). No archiving needed.")
            return

        folders_to_archive = backup_folders[:-keep_latest]

        for folder in folders_to_archive:
            archive_target = backup_root / folder.name
            
            # Zip the directory
            shutil.make_archive(
                base_name=str(archive_target),
                format="zip",
                root_dir=str(backup_root),
                base_dir=folder.name
            )
            
            # Safely remove uncompressed directory
            shutil.rmtree(folder)
            print(f"📦 [Archive] Compressed and pruned old backup: {folder.name}.zip")

    except PermissionError:
        print("❌ [Archive Error] Deletion blocked due to insufficient permissions.")
    except Exception as err:
        print(f"❌ [Archive Error] Failed during archive rotation: {err}")


def get_disk_status(path: Path) -> dict:
    """Retrieve disk space statistics using shutil.disk_usage()."""
    try:
        usage = shutil.disk_usage(path)
        total_gb = usage.total / (1024 ** 3)
        used_gb = usage.used / (1024 ** 3)
        free_gb = usage.free / (1024 ** 3)
        
        print("\n💾 --- System Disk Usage Report ---")
        print(f" Location   : {path.resolve()}")
        print(f" Total Space: {total_gb:.2f} GB")
        print(f" Used Space : {used_gb:.2f} GB ({(used_gb/total_gb)*100:.1f}%)")
        print(f" Free Space : {free_gb:.2f} GB")
        print("-----------------------------------")
        
        return {"total": total_gb, "used": used_gb, "free": free_gb}
    except Exception as err:
        print(f"❌ [Disk Report Error] Could not read disk stats: {err}")
        return {}