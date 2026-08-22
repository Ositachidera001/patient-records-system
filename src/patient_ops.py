"""
patient_ops.py

All menu-action functions live here. Each one is called with the single
shared `registry` dict (NHIS number -> patient-detail dict) and does one
job: view, register, update, transfer, discharge, or report.

The registry dict's shape is kept in sync with Patient.to_dict() from
models.py:
    {
        "name": str, "age": int, "nhis_number": str, "ward": str,
        "triage": str, "admission_status": bool, "allergies": [str, ...]
    }
"""
from datetime import datetime, date, timedelta
import os

from pathlib import Path

from config import WIDTH, TRIAGE_INFO, VALID_TRIAGE_COLOURS, registry_file
from file_manager import save_registry, log_action, backup_registry, full_backup, archive_old_backups, get_disk_status
from models import Patient, PaediatricPatient
from utils import print_patient_table, calculate_patient_age
from validators import validate_nhis
from api_client import lookup_drug
from news_scraper import scrape_health_books, scrape_health_quotes, save_quotes_to_json, load_quotes_from_json

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
REGISTRY_FILE = DATA_DIR / "registry.json"
BACKUP_ROOT = BASE_DIR / "backups"

def safe_int_input(prompt):
    """Force a valid integer selection, retrying forever on bad input.

    This is the one place ALL menu-number input goes through, so every
    call site automatically gets the same validation + retry behaviour.
    """
    while True:
        try:
            return int(input(prompt))
        except ValueError:
            print("❌ Invalid input. Please enter a whole number.")


def generate_next_nhis(registry):
    """Auto-increment a zero-padded NHIS ID string from existing registry keys."""
    if not registry:
        return "NHIS-0001"

    numeric_ids = []
    for key in registry.keys():
        try:
            num_part = int(key.split("-")[1])
            numeric_ids.append(num_part)
        except (IndexError, ValueError):
            continue

    next_id = max(numeric_ids) + 1 if numeric_ids else 1
    return f"NHIS-{next_id:04d}"


def view_patients(registry):
    """Option 1: display every patient, sorted by triage severity."""
    print_patient_table(registry)


def register_new_patient(registry):
    """Option 2: intake a new patient.

    Builds a real Patient object (Lesson 14 OOP), validates age with a
    custom business-rule ValueError, then stores patient.to_dict() in the
    registry so JSON persistence keeps working unchanged.
    """
    print("\n--- NEW PATIENT INTAKE ---")

    name = input("Enter Patient Full Name: ").strip()
    if not name:
        print("❌ Registration failed: a name is required.")
        return

    while True:
        # optional collection and validation of date of birth
        date_input = str(input("Enter Patient Date of Birth (YYYY-MM-DD): click enter to skip: ").strip())
        if date_input == "":
            birth_date_str = "Not Provided"
            date_of_birth = birth_date_str
            try:
                age = int(input("Enter Patient Age: ").strip())
                if age < 0 or age > 130:
                    # Custom business rule: not a Python TypeError, a rule WE define.
                    raise ValueError("age must be between 0 and 130.")
                print(f"Age of {name.title()}: {age}years. Date of Birth: Not Provided ⚠")
                break
            except ValueError as e:
                print(f"❌ Invalid age — {e}")
        else:
            birth_date_str = date_input
            age, date_of_birth = calculate_patient_age(birth_date_str)
            print(f"Age of {name.title()}: {age}years. Date of Birth: {date_of_birth} ")
            break


    print("\nTriage Options:")
    for color, desc in TRIAGE_INFO.items():
        print(f" - [{color.upper()}]: {desc}")

    triage = input("Assign Initial Triage Colour: ").strip().lower()
    if triage not in VALID_TRIAGE_COLOURS:
        print("❌ Invalid triage colour. Falling back to GREEN.")
        triage = "green"

    ward = input("Assign Initial Ward: ").strip()
    if not ward:
        ward = "Outpatient"

    allergy_input = input("Enter allergies, comma-separated (blank if none): ").strip()
    allergies = [a.strip() for a in allergy_input.split(",") if a.strip()] if allergy_input else []

    nhis_id = generate_next_nhis(registry)

    # --- validate the NHIS ID before it ever touches the registry -----
    # Even though nhis_id came from OUR OWN generate_next_nhis() function
    # (not raw user typing), we still validate it here. This is a
    # defensive-programming habit: don't assume data is clean just
    # because you trust the code that produced it -- validate at the
    # boundary where the data is ABOUT TO BE STORED, not just at the
    # boundary where a human typed something. If generate_next_nhis()
    # is ever changed, or a future menu option lets staff type a manual
    # NHIS number instead of auto-generating one, this same check
    # protects the registry either way.
    if not validate_nhis(nhis_id):
        print(f"❌ Registration failed: '{nhis_id}' is not a valid NHIS "
              f"number (expected format NHIS-XXXX, e.g. NHIS-0001).")
        return

    # --- build the actual OOP Patient object -------------------------
    patient = Patient(name, age, date_of_birth, nhis_id, ward, triage)
    if allergies:
        patient.add_allergy(*allergies)

    # Store the plain-dict form (backward-compatible JSON storage)
    registry[nhis_id] = patient.to_dict()

    if save_registry(registry):
        log_action(f"Registered {name.upper()} as {nhis_id} to {ward.title()} "
                    f"Ward [Triage: {triage.upper()}] Age: {age}, DoB: {date_of_birth}.")
        print(f"\n✅ Registered. Patient {name.upper()} assigned ID: {nhis_id}")


def find_patient_by_nhis_number(registry):
    """Prompt for and validate an NHIS ID, returning it if found else None."""
    try:
        raw = input("\nEnter Patient NHIS ID (e.g. NHIS-0001): ").strip()
    except Exception as e:
        print(f"❌ Could not read input: {e}")
        return None

    nhis_id = raw.upper()
    if nhis_id not in registry:
        print("❌ No patient found with that NHIS ID.")
        return None
    return nhis_id


def menu_add_allergies(registry):
    """Option 3: attach new allergies to an existing patient, de-duplicated.

    Rebuilds a temporary Patient/PaediatricPatient object purely so we can
    reuse add_allergy(*args)'s built-in de-dup logic instead of writing it
    twice.
    """
    nhis_id = find_patient_by_nhis_number(registry)
    if not nhis_id:
        return

    raw = input("Enter new allergies, comma-separated: ").strip()
    if not raw:
        print("⚠️ Nothing entered — no changes made.")
        return

    new_allergies = [a.strip() for a in raw.split(",") if a.strip()]

    data = registry[nhis_id]
    if "weight_kg" in data:
        temp_patient = PaediatricPatient.from_dict(data)
    else:
        temp_patient = Patient.from_dict(data)

    added = temp_patient.add_allergy(*new_allergies)
    registry[nhis_id]["allergies"] = temp_patient.allergies

    if save_registry(registry):
        log_action(f"Allergy update for {nhis_id}: added {added}")
        if added:
            print(f"✅ Added: {added}")
        else:
            print("⚠️ All entered allergies were already on file — nothing new added.")


def update_patient_fields(patient_dict, **kwargs):
    """Apply an arbitrary set of field updates to a patient dict.

    Uses **kwargs so the caller decides which fields to touch:
        update_patient_fields(record, name="New Name")
        update_patient_fields(record, triage="red")

    Raises ValueError if an unknown field name is passed in (custom
    business rule: you may only update fields that actually exist).
    Returns the list of field names that were changed.
    """
    updated = []
    for field, value in kwargs.items():
        if value is None:
            continue
        if field not in patient_dict:
            raise ValueError(f"'{field}' is not a valid patient field.")
        patient_dict[field] = value
        updated.append(field)
    return updated


def menu_update_fields(registry):
    """Option 4: update a patient's name or triage level via update_patient_fields(**kwargs)."""
    nhis_id = find_patient_by_nhis_number(registry)
    if not nhis_id:
        return

    print(f"\nUpdating {nhis_id} ({registry[nhis_id]['name']})")
    print("1. Update Patient Name")
    print("2. Re-evaluate Triage Level")
    choice = safe_int_input("Choice: ")

    kwargs = {}
    if choice == 1:
        new_name = input("Enter corrected full name: ").strip()
        if new_name:
            kwargs["name"] = new_name.title()
    elif choice == 2:
        print("\nTriage Options:")
        for color, desc in TRIAGE_INFO.items():
            print(f" - [{color.upper()}]: {desc}")
        new_triage = input("New triage colour: ").strip().lower()
        if new_triage not in VALID_TRIAGE_COLOURS:
            print("❌ Invalid triage colour — no change made.")
            return
        kwargs["triage"] = new_triage
    else:
        print("❌ Invalid selection.")
        return

    try:
        updated = update_patient_fields(registry[nhis_id], **kwargs)
    except ValueError as e:
        print(f"❌ Update rejected: {e}")
        return

    if updated and save_registry(registry):
        log_action(f"Field update for {nhis_id}: {kwargs}")
        print(f"✅ Updated: {', '.join(updated)}")


def transfer_to_new_ward(registry):
    """Option 5: move a patient to a new ward."""
    nhis_id = find_patient_by_nhis_number(registry)
    if not nhis_id:
        return

    old_ward = registry[nhis_id]["ward"]
    new_ward = input(f"Enter destination ward (current: {old_ward}): ").strip()
    if not new_ward:
        print("⚠️ No ward entered — no change made.")
        return

    registry[nhis_id]["ward"] = new_ward
    if save_registry(registry):
        log_action(f"Transferred {nhis_id} from {old_ward} Ward to {new_ward} Ward.")
        print(f"✅ Transferred from {old_ward} to {new_ward} Ward.")


def discharge_patient(registry):
    """Option 6: mark a patient as discharged (admission_status -> False)."""
    nhis_id = find_patient_by_nhis_number(registry)
    if not nhis_id:
        return

    if not registry[nhis_id].get("admission_status", True):
        print("⚠️ Patient is already discharged.")
        return

    registry[nhis_id]["admission_status"] = False
    if save_registry(registry):
        log_action(f"Discharged patient {nhis_id}.")
        print("✅ Patient discharged.")


def census_summary(registry):
    """Option 7: ward + triage breakdown of currently admitted patients.

    Uses a finally block so a timestamp is ALWAYS printed at the end,
    even if something in the try block goes wrong.
    """
    print("\n" + "=" * WIDTH + f"\n{'WARD CENSUS SUMMARY':^{WIDTH}}\n" + "=" * WIDTH)
    try:
        if not registry:
            print("⚠️ No patients currently in the system.")
            return

        wards = {}
        triage_counts = {"red": 0, "yellow": 0, "green": 0}
        occupied_wards = set()

        for p in registry.values():
            if p.get("admission_status", True):
                w = p["ward"]
                wards[w] = wards.get(w, 0) + 1
                occupied_wards.add(w)
                t = p["triage"]
                if t in triage_counts:
                    triage_counts[t] += 1

        total_admitted = sum(wards.values())

        print(f"\n📍 Total Admitted: {total_admitted}")
        print("\n📍 Per-Ward Breakdown:")
        for w_name, count in wards.items():
            print(f"  • {w_name:<18}: {count} Patient(s)")

        print(f"\n📍 Occupied Wards ({len(occupied_wards)}): {sorted(occupied_wards)}")

        print("\n🚨 Triage Risk Matrix:")
        print(f"  🔴 [RED] Critical   : {triage_counts['red']}")
        print(f"  🟡 [YELLOW] Urgent  : {triage_counts['yellow']}")
        print(f"  🟢 [GREEN] Routine  : {triage_counts['green']}")
    finally:
        timestamp = datetime.now().strftime("%A, %d %B %Y at %H:%M:%S")
        print(f"\n🕒 Report generated: {timestamp}")
        print("=" * WIDTH)


def system_status(registry):
    """Option 8: quick health-check of the in-memory registry and the JSON file on disk."""
    print(f"\n🔍 Active registry: {len(registry)} patient(s) loaded in memory.")
    if os.path.exists(registry_file):
        size = os.path.getsize(registry_file)
        print(f"📄 Data file OK: {registry_file} ({size} bytes)")
        get_disk_status(BASE_DIR)
    else:
        print(f"⚠️ Data file not found yet at {registry_file} — it will be created on first save.")

def schedule_appointment(registry) -> bool:
    """computes an appointment date 'days_from_now' into the future and stores it in 
    the patient's record."""
    nhis_number = str(input("Enter Patient's NHIS number"))
    if nhis_number not in registry:
        print(f" Patient with NHIS {nhis_number} not found.")
        return False
    while True:
        try:
            appointment_date = str(input("Enter appointment date (YYYY-MM-DD) or click Enter to enter Number of days instead: "))
            if appointment_date == "":
                days_from_now = safe_int_input("Enter number of days: ")
                # calcuate future date using timedelta
                future_date = date.today() + timedelta(days=days_from_now)
            else:
                appointment_date_formatted = datetime.strptime(appointment_date, "%Y-%m-%d").date()
                days_from_now = (appointment_date_formatted - date.today()).days
                # use inputted appointment date
                future_date = appointment_date_formatted

            # format to human-readable string
            formatted_date = f"{future_date.strftime('%A, %d %B %Y.')} {days_from_now} days from today: - {date.today()}" # e.g "Friday, 28 August 2026"

            # store on patient record
            registry[nhis_number]["appointment_date"] = formatted_date
            print(f"✅ Appointment scheduled for {registry[nhis_number]["name"]} on {formatted_date}.")
            return True
        except ValueError:
            print(f"Invalid date format '{appointment_date}' -- usr YYYY-MM-DD")
            continue


def end_system(registry):
    """Option 9: save the registry, log the shutdown, and exit."""
    print("\nClosing down... saving final state.")
    save_registry(registry)

    # backup single registry JSON file 
    backup_registry(REGISTRY_FILE, BACKUP_ROOT / "registry_daily")

    # backup entire data folder after 30 days.
    if len(os.listdir(BACKUP_ROOT/"registry_daily")) >= 1:  # changed to 1 so i can get a full backup
        full_backup(DATA_DIR, BACKUP_ROOT)

    # Archive older backups (keep 3 latest)
    if len(os.listdir(BACKUP_ROOT)) >= 3:
        archive_old_backups(BACKUP_ROOT, keep_latest=3)

    log_action("System shut down normally by user.")
    print("👋 System offline.")
    exit()


def look_up_patient(registry):
    """Bonus: show every field for a single patient, including all allergies."""
    nhis_id = find_patient_by_nhis_number(registry)
    if not nhis_id:
        return

    p = registry[nhis_id]
    status = "Admitted" if p.get("admission_status", True) else "Discharged"
    known_fields = {"name", "age", "nhis_number", "ward", "triage", "admission_status", "allergies"}

    print("\n" + "-" * WIDTH)
    print(f"NHIS ID    : {nhis_id}")
    print(f"Name       : {p['name']}")
    print(f"Age        : {p.get('age', 'N/A')}")
    print(f"Ward       : {p['ward'].title()}")
    print(f"Triage     : {p['triage'].upper()} — {TRIAGE_INFO.get(p['triage'], 'Unknown')}")
    print(f"Status     : {status}")
    print(f"Allergies  : {', '.join(p.get('allergies', [])) or 'None'}")
    # Show any extra fields (e.g. weight_kg/guardian_name for paediatric patients)
    for key, value in p.items():
        if key not in known_fields:
            print(f"{key.replace('_', ' ').title():<11}: {value}")
    print("-" * WIDTH)


def search_patient_by_name(registry):
    """Bonus: partial, case-insensitive name search across the whole registry."""
    query = input("Enter (part of) the patient's name: ").strip()
    if not query:
        print("⚠️ Empty search — nothing to look for.")
        return

    matches = {nhis: p for nhis, p in registry.items() if query.lower() in p["name"].lower()}
    if not matches:
        print(f"❌ No patients found matching '{query.title()}'.")
        return

    print(f"\n🔎 {len(matches)} match(es) found:")
    print_patient_table(matches)

def menu_drug_lookup(registry):
    """Option 13: query OpenFDA for information about a drug by name.

    `registry` is accepted (like every other menu action, so main.py can
    call every action the same way: action(registry)) but isn't actually
    used here -- this lookup is a reference tool, not something that
    reads or writes patient data. Keeping the same signature as every
    other menu function matters more than trimming an unused parameter:
    it means main.py's menu_actions dict never needs a special case.
    """
    drug_name = input("\nEnter drug name to look up (brand or generic): ").strip()
    if not drug_name:
        print("⚠️ Empty search — nothing to look for.")
        return

    print(f"\n🔎 Searching OpenFDA for '{drug_name}'...")
    results = lookup_drug(drug_name, limit=3)

    if not results:
        # lookup_drug() already printed the specific reason (network
        # failure, no match, etc.) -- nothing more to add here.
        return

    print("\n" + "-" * WIDTH)
    print(f"{'Brand Name':<20}{'Generic Name':<20}")
    print("-" * WIDTH)
    for drug in results:
        print(f"{drug['brand_name']:<20}{drug['generic_name']:<20}")
    print("-" * WIDTH)

    # Show full purpose/warnings for each result underneath the table --
    # these fields are often long free-text, so a fixed-width table
    # column would just truncate them illegibly.
    for drug in results:
        print(f"\n💊 {drug['brand_name']} ({drug['generic_name']})")
        print(f"   Purpose : {drug['purpose']}")
        print(f"   Warnings: {drug['warnings']}")
    print("-" * WIDTH)

def menu_health_qoutes(registry):
    """option 14: show saved health quotes, or scrape fresh ones if no saved exists yet.
    """
    if saved := load_quotes_from_json():
        quotes = saved['quotes']
        print(f"\n 📜 Showing saved quotes from {saved['scraped_at']}")
        for quote in quotes:
            print(f"\n\"{quote['text']}\n -- {quote['author']}")
            print(f" tags: {','.join(quote.get('tags'))}")
            print(f"\n\U0001F4DA Health-related books:")   
    else:
        print(f"\n 📜 No saved quotes found -- scraping fresh from the web...")
        if quotes := scrape_health_quotes(page_number=safe_int_input(input("Enter number of page. Click enter to use default: "))):
            save_quotes_to_json(quotes)
            for quote in quotes:
                print(f"\n\"{quote['text']}\n -- {quote['author']}")
                print(f" tags: {','.join(quote.get('tags'))}")
                print(f"\n\U0001F4DA Health-related books:")
        else:
            print(f"No health-related quotes available right now.")
        if books := scrape_health_books():
            for book in books:
                print(f"{book['title']} -- \u00a3{float(book['price']):.2f}")
        else:
            print(f"No matching books found right now.")


