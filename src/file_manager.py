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
import csv

from pathlib import Path

from config import registry_file, audit_log_file, DATA_DIR, VALID_TRIAGE_COLOURS
from validators import validate_nhis

# Create the data/ directory up front so save_registry() and log_action()
# never fail just because the folder doesn't exist yet.
os.makedirs(DATA_DIR, exist_ok=True)
CSV_EXPORT_FIELDNAMES = [
    "nhis_number", "name", "age", "date_of_birth", "ward",
    "triage", "admission_status", "allergies",
]

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
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(audit_log_file, "a", encoding="utf-8") as f:
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

# ---------------------------------------------------------------------------
# CSV EXPORT / IMPORT (Lesson 22A)
# ---------------------------------------------------------------------------

def export_registry_to_csv(registry, output_dir):
    """Export every patient in the registry to a timestamped CSV file.

    Args:
        registry (dict): the patient registry, {nhis_number: patient_dict}.
        output_dir (str | Path): folder to write the CSV into. Created
            automatically if it doesn't exist yet.

    Returns:
        Path | None: the path of the CSV file written, or None if the
        export failed (e.g. permissions problem). Mirrors save_registry()'s
        style: a value the caller can check, rather than an exception the
        caller has to remember to catch.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Timestamped filename: every export gets its own file rather than
    # silently overwriting the last one, so the hospital can keep a
    # history of exactly what was handed to the health authority and when.
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filepath = output_dir / f"patient_export_{timestamp}.csv"

    try:
        # newline="": REQUIRED by Python's own csv module docs when
        # writing CSV files. Without it, on Windows, text-mode file
        # writing translates every "\n" the csv module writes into
        # "\r\n" ITSELF -- but the csv module ALSO writes "\r\n" as its
        # own row terminator, so the two translations stack and you get
        # a doubled "\r\r\n" at the end of every row. Opening with
        # newline="" disables Python's automatic translation and lets
        # the csv module handle line endings entirely on its own,
        # correctly, on every platform.
        #
        # encoding="utf-8": patient names, guardian names, or allergy
        # entries may contain non-ASCII characters (accented letters,
        # etc.). Explicitly requesting UTF-8 means the file opens
        # correctly regardless of what the OS's default encoding
        # happens to be (which varies between Windows/macOS/Linux).
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            # DictWriter maps EACH ROW from a dict (keyed by column name)
            # into the correct CSV columns, in fieldnames order -- so we
            # don't have to manually track which value goes in which
            # column position ourselves.
            writer = csv.DictWriter(f, fieldnames=CSV_EXPORT_FIELDNAMES)
            writer.writeheader()

            for nhis_number, patient_data in registry.items():
                writer.writerow({
                    "nhis_number": patient_data.get("nhis_number", nhis_number),
                    "name": patient_data.get("name", ""),
                    "age": patient_data.get("age", ""),
                    "date_of_birth": patient_data.get("date_of_birth", ""),
                    "ward": patient_data.get("ward", ""),
                    "triage": patient_data.get("triage", ""),
                    "admission_status": patient_data.get("admission_status", ""),
                    # allergies is stored as a LIST in the registry, e.g.
                    # ["Penicillin", "Latex"] -- a single CSV cell can
                    # only hold plain text, so we flatten the list into
                    # ONE string, joined with " | ". That separator is
                    # deliberately unusual so it's very unlikely to ever
                    # collide with a real allergy name that itself
                    # contains a comma or semicolon.
                    "allergies": " | ".join(patient_data.get("allergies", [])),
                })

        print(f"✅ Exported {len(registry)} patient(s) to {filepath}")
        return filepath

    except OSError as e:
        print(f"❌ CSV export failed: {e}")
        return None


def _generate_next_nhis_for_import(registry):
    """Auto-generate the next NHIS-XXXX ID for a CSV row that arrived
    with no usable NHIS number of its own.

    NOTE ON DUPLICATION: patient_ops.py already has a near-identical
    generate_next_nhis() function. It isn't reused here on purpose --
    patient_ops.py imports FROM file_manager.py (for save_registry,
    log_action, etc.), so if file_manager.py imported back FROM
    patient_ops.py, Python would hit a circular import (each module
    would need the other to finish loading before it could finish
    loading itself). Keeping this tiny duplicate here is a small,
    deliberate trade-off to avoid restructuring the whole project's
    import graph for one helper function.
    """
    numeric_ids = []
    for key in registry.keys():
        try:
            numeric_ids.append(int(key.split("-")[1]))
        except (IndexError, ValueError):
            continue

    next_id = max(numeric_ids) + 1 if numeric_ids else 1
    return f"NHIS-{next_id:04d}"


def import_patients_from_csv(filepath, registry):
    """Read a CSV of incoming patients (e.g. a transfer list from another
    hospital), clean and validate each row, and merge every VALID row
    straight into `registry`. Invalid rows are skipped and reported,
    never allowed to corrupt the registry.

    Expected CSV columns (case-sensitive header names):
        name, age, triage, ward, date_of_birth, nhis_number, allergies
    Only "name", "age", and "triage" are REQUIRED per the lesson spec --
    the rest are optional and get sensible defaults if missing.

    Args:
        filepath (str | Path): path to the CSV file to import.
        registry (dict): the patient registry to merge accepted rows
            into, IN PLACE (this function mutates the dict you pass in,
            the same way save_registry()'s callers already expect
            "registry" to be a live, shared dictionary).

    Returns:
        dict: {
            "accepted": int,
            "rejected": list[tuple[int, str, list[str]]],  # (row_number, name, reasons)
            "report_path": Path | None,   # BONUS: where the text report was saved
        }
        Returns {"accepted": 0, "rejected": [], "report_path": None} if
        the file itself couldn't be opened at all -- this function never
        raises out to its caller.
    """
    filepath = Path(filepath)
    accepted_count = 0
    rejected_rows = []  # each entry: (row_number, name_for_display, [reasons])

    try:
        # newline="" here too -- required by the csv module on the READING
        # side as well as writing, for the same "don't let two different
        # layers both try to normalise line endings" reason explained in
        # export_registry_to_csv() above.
        with open(filepath, "r", newline="", encoding="utf-8") as f:
            # DictReader turns each CSV row into a dict keyed by the
            # HEADER ROW's column names, e.g. {"name": "Jane Doe",
            # "age": "34", ...} -- so we access fields by name instead of
            # by a fragile numeric column position.
            reader = csv.DictReader(f)

            # enumerate(..., start=2): row 1 is the header, so the first
            # actual DATA row is row 2 in a text editor / Excel -- this
            # keeps the row numbers we report to the user matching what
            # they'd see if they opened the CSV themselves.
            for row_number, raw_row in enumerate(reader, start=2):
                reasons = []

                # --- CLEAN every field up front (strip/title/lower) ----
                # .get(..., "") guards against a CSV that's missing a
                # column entirely (raw_row.get would otherwise return
                # None, and None has no .strip() method).
                name = (raw_row.get("name") or "").strip().title()
                age_raw = (raw_row.get("age") or "").strip()
                triage = (raw_row.get("triage") or "").strip().lower()
                ward = (raw_row.get("ward") or "outpatient").strip().lower()
                date_of_birth = (raw_row.get("date_of_birth") or "").strip()
                nhis_number = (raw_row.get("nhis_number") or "").strip().upper()
                allergies_raw = (raw_row.get("allergies") or "").strip()
                # Mirrors the " | " separator used by export_registry_to_csv(),
                # so a file we EXPORTED can also be re-IMPORTED correctly.
                allergies = (
                    [a.strip() for a in allergies_raw.split("|") if a.strip()]
                    if allergies_raw else []
                )

                # --- VALIDATE name ---------------------------------------
                if not name:
                    reasons.append("missing name")

                # --- VALIDATE age -----------------------------------------
                age = None
                if not age_raw:
                    reasons.append("missing age")
                else:
                    try:
                        age = int(age_raw)
                        if age < 0 or age > 130:
                            reasons.append(f"age out of realistic range ({age})")
                    except ValueError:
                        # int("thirty") raises ValueError -- this catches
                        # any age field that isn't a plain whole number.
                        reasons.append(f"invalid age '{age_raw}' (not a whole number)")

                # --- VALIDATE triage ---------------------------------------
                if triage not in VALID_TRIAGE_COLOURS:
                    reasons.append(
                        f"invalid triage '{triage}' (must be one of {VALID_TRIAGE_COLOURS})"
                    )

                if reasons:
                    # SKIP this row -- do not touch the registry at all --
                    # and record WHY, for the report. `continue` jumps
                    # straight to the next row of the for loop.
                    rejected_rows.append((row_number, name or "(no name)", reasons))
                    continue

                # --- Resolve the NHIS number -------------------------------
                # Accept the incoming hospital's NHIS number IF it's both
                # correctly formatted AND not already used by someone else
                # in our registry (a collision would silently overwrite an
                # existing patient's record, which is exactly the kind of
                # mistake we validate to prevent). Otherwise, generate a
                # fresh one, the same way a new walk-in registration would.
                if not nhis_number or not validate_nhis(nhis_number) or nhis_number in registry:
                    nhis_number = _generate_next_nhis_for_import(registry)

                registry[nhis_number] = {
                    "name": name,
                    "age": age,
                    "date_of_birth": date_of_birth,
                    "nhis_number": nhis_number,
                    "ward": ward,
                    "triage": triage,
                    "admission_status": True,
                    "allergies": allergies,
                }
                accepted_count += 1

    except FileNotFoundError:
        print(f"❌ Import failed: file not found at {filepath}")
        return {"accepted": 0, "rejected": [], "report_path": None}
    except OSError as e:
        print(f"❌ Import failed: {e}")
        return {"accepted": 0, "rejected": [], "report_path": None}

    # --- Print the summary to the terminal --------------------------------
    print(f"\n📥 CSV Import Summary — {filepath.name}")
    print(f"   Accepted: {accepted_count}")
    print(f"   Rejected: {len(rejected_rows)}")
    for row_number, name, reasons in rejected_rows:
        print(f"   ❌ Row {row_number} ({name}): {', '.join(reasons)}")

    # --- BONUS: save the same report as a text file, next to the CSV ------
    report_path = _save_import_report(filepath, accepted_count, rejected_rows)

    return {
        "accepted": accepted_count,
        "rejected": rejected_rows,
        "report_path": report_path,
    }


def _save_import_report(source_csv_path, accepted_count, rejected_rows):
    """BONUS: write the import results to a .txt file in the SAME folder
    as the CSV that was imported, so there's a permanent, readable record
    of exactly what happened -- useful for the hospital to show the
    sending facility which rows need correcting and why.

    Returns:
        Path | None: where the report was saved, or None if saving failed.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_path = source_csv_path.parent / f"{source_csv_path.stem}_import_report_{timestamp}.txt"

    lines = [
        "Patient CSV Import Report",
        "=" * 40,
        f"Source file : {source_csv_path.name}",
        f"Imported at : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        f"Accepted : {accepted_count}",
        f"Rejected : {len(rejected_rows)}",
        "",
    ]

    if rejected_rows:
        lines.append("Rejected rows:")
        for row_number, name, reasons in rejected_rows:
            lines.append(f"  Row {row_number} ({name}): {', '.join(reasons)}")
    else:
        lines.append("No rejected rows — every row imported cleanly.")

    try:
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        print(f"📝 Import report saved to {report_path}")
        return report_path
    except OSError as e:
        print(f"⚠ Could not save import report: {e}")
        return None


import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
EXPORTS = DATA_DIR / "exports"
EXPORTS.mkdir(parents=True, exist_ok=True)
file_path = EXPORTS / "patient_export_2026-08-25_18-37-48.csv"
# print(EXPORTS)

df = pd.read_csv(file_path, encoding="utf-8")

TRIAGE_SCORE = {
    "red" : 3,
    "yellow": 2,
    "green": 1
    }
df["triage_score"] = df["triage"].map(TRIAGE_SCORE)
df2 = df.drop("allergies", axis=1)
del df2["triage_score"]
admission_status = df2.pop("admission_status")
print(f"{df2} {admission_status}")