# developer: Osita Chidera
# date: 23/06/2026
import datetime

width = 50
triage_info = {
    "red":    "Immediate - Life threatening",
    "yellow": "Urgent - Within 1 hour",
    "green":  "Routine - Can wait."
}

# Initialize registry with consistent schema — ALL patients have 'allergies' key (list)
registry = {
    "NHIS-0001": {
        "name":             "Amina Bello",
        "age":              34,
        "nhis_number":      "NHIS-0001",
        "ward":             "emergency",
        "triage":           "red",
        "admission_status": True,
        "allergies":        []
    },
    "NHIS-0002": {
        "name":             "Ken Okoro",
        "age":              28,
        "nhis_number":      "NHIS-0002",
        "ward":             "cardiology",
        "triage":           "yellow",
        "admission_status": True,
        "allergies":        []
    },
    "NHIS-0003": {
        "name":             "Adams Sarah",
        "age":              26,
        "nhis_number":      "NHIS-0003",
        "ward":             "antenatal",
        "triage":           "green",
        "admission_status": False,
        "allergies":        []
    }
}


def safe_int_input(prompt, min_val=0, max_val=150):
    """Safely collect an integer from the user within a valid range.

    Uses a while loop with try/except to catch ValueError when the user
    types non-numeric input. Also enforces a minimum and maximum value
    using raise ValueError for business rule validation.

    Args:
        prompt: The message to show the user.
        min_val: The lowest acceptable integer (default 0).
        max_val: The highest acceptable integer (default 150).

    Returns:
        A valid integer between min_val and max_val.
    """
    while True:
        try:
            raw = input(prompt).strip()
            value = int(raw)

            # Business rule: age must be within clinical range
            if value < min_val:
                raise ValueError(f"Value too low. Minimum accepted is {min_val}.")
            if value > max_val:
                raise ValueError(f"Value too high. Maximum accepted is {max_val}.")

            return value

        except ValueError as e:
            print(f"❌ Invalid input: {e}")
            print(f"   Please enter a whole number between {min_val} and {max_val}.\n")


def view_patients(registry):
    """Display all patients sorted by triage severity (RED → YELLOW → GREEN)."""
    print("\n--- ALL PATIENTS ---")

    if not registry:
        print("No patient(s) admitted")
        return

    rank = {"red": 1, "yellow": 2, "green": 3}
    sorted_patients = sorted(
        registry.items(),
        key=lambda x: rank.get(x[1]["triage"], 4)
    )

    for nhis_number, p in sorted_patients:
        status = "Admitted" if p["admission_status"] else "Discharged"
        allergy_note = f" | Allergies: {len(p.get('allergies', []))}"
        print(f" {nhis_number} | {p['name']} | Age {p['age']} | {p['ward']} | {p['triage'].upper()} | {status}{allergy_note}")


def register_new_patient(registry):
    """Collect input and register a new patient with validated triage and error handling.

    Now uses safe_int_input for age collection and raises ValueError
    to enforce business rules (e.g., name cannot be empty).
    """
    name = input("Full name: ").strip().title()

    # Business rule: name must not be empty
    if not name or len(name) < 2:
        raise ValueError("Patient name must contain at least 2 characters.")

    # Use safe_int_input instead of raw int(input(...))
    age = safe_int_input("Age: ", min_val=0, max_val=150)

    nhis_number = input("NHIS number: ").strip().upper()
    ward = input("Ward: ").strip().lower()

    while True:
        triage = input("Enter Triage Colour (RED/YELLOW/GREEN): ").strip().lower()
        if triage in triage_info:
            break
        print("❌ Invalid triage. Use RED, YELLOW, or GREEN.")

    if nhis_number in registry:
        print(f"❌ {nhis_number} already exists.")
    else:
        registry[nhis_number] = {
            "name":             name,
            "age":              age,
            "nhis_number":      nhis_number,
            "ward":             ward,
            "triage":           triage,
            "admission_status": True,
            "allergies":        []
        }
        print(f"✅ {name} registered under {nhis_number}")
        print(f"\n📋 TRIAGE: {triage_info[triage]}")


def add_allergies(registry, nhis_number, *allergies):
    """Add any number of allergies to a patient's record using *args.

    Args:
        registry: The patient dictionary database.
        nhis_number: The patient's NHIS identifier.
        *allergies: Variable number of allergy strings.
    """
    patient = registry.get(nhis_number)
    if not patient:
        print("❌ Patient not found.")
        return

    if not allergies:
        print(f"⚠️ No allergies provided for {patient['name']}.")
        return

    cleaned = [a.strip() for a in set(allergies) if a.strip()]
    existing = set(patient["allergies"])
    new_allergies = [a for a in cleaned if a not in existing]
    skipped = len(cleaned) - len(new_allergies)
    patient["allergies"].extend(new_allergies)

    if new_allergies:
        print(f"✅ Added {len(new_allergies)} new allergy(ies) for {patient['name']}: {new_allergies}")
    if skipped:
        print(f"⚠ {skipped} allergy(ies) already on record - skipped.")


def update_patient_fields(registry, nhis_number, **fields):
    """Add or update any combination of fields on a patient record using **kwargs.

    Args:
        registry: The patient dictionary database.
        nhis_number: The patient's NHIS identifier.
        **fields: Keyword arguments for new fields to add (diagnosis, notes, etc.).
    """
    patient = registry.get(nhis_number)
    if not patient:
        print("❌ Patient not found.")
        return

    added = []
    for key, value in fields.items():
        patient[key] = value
        added.append(f"{key}={value}")

    print(f"✅ Added/Updated fields for {patient['name']}: {', '.join(added)}")


def find_patient_by_nhis_number(registry):
    """Find and display a patient by their NHIS number."""
    nhis_number = input("Enter NHIS number: ").strip().upper()
    patient = registry.get(nhis_number)
    if patient:
        allergies = patient.get("allergies", [])
        allergy_str = f" | Allergies: {allergies}" if allergies else ""
        print(f"Found: {patient['name']}, Age {patient['age']}, Ward {patient['ward']}, Triage {patient['triage'].upper()}{allergy_str}")
    else:
        print(f"❌ Patient {nhis_number} not found in registry.")


def transfer_to_new_ward(registry):
    """Transfer a patient to a new ward."""
    nhis_number = input("NHIS to transfer: ").strip().upper()
    patient = registry.get(nhis_number)
    if not patient:
        print("❌ Not Found.")
        return

    new_ward = input(f"Current ward: {patient['ward']}. New Ward: ").strip().lower()
    patient["ward"] = new_ward
    print(f"✅ {patient['name']} transferred to {new_ward.title()}")


def discharge_patient(registry):
    """Discharge a patient from the registry."""
    nhis_number = input("NHIS to discharge: ").strip().upper()
    if nhis_number in registry:
        registry[nhis_number]["admission_status"] = False
        print(f"🟠 Discharged: {registry[nhis_number]['name']}.")
    else:
        print("❌ Not Found.")


def census_summary(registry):
    """Generate a ward census summary of admitted patients.

    Now includes a finally block that always prints a completion timestamp,
    ensuring the audit trail is maintained even if an error occurs.
    """
    total = 0
    ward_count = {}
    occupied_wards = set()

    try:
        total = sum(1 for p in registry.values() if p["admission_status"])
        print("\n--- WARD CENSUS ---")
        print(f"Total Admitted: {total}")

        for p in registry.values():
            if p["admission_status"]:
                ward = p["ward"]
                occupied_wards.add(ward)
                ward_count[ward] = ward_count.get(ward, 0) + 1

        for ward, count in sorted(ward_count.items()):
            print(f" {ward}: {count} patient(s)")

        print(f"\nOccupied wards: {occupied_wards}")

    except Exception as e:
        print(f"❌ Error generating census: {e}")

    finally:
        # This ALWAYS runs — success or error
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"Census complete — {timestamp}")

    return ward_count, occupied_wards


def end_system(registry):
    """Shutdown the patient records system."""
    print("\n=== SHUTDOWN ===")
    print(f"Patients remaining in registry: {len(registry)}")
    print("Goodbye, Stay Safe! 🦾")
    return "QUIT"


# ── MENU DISPATCH TABLE ──────────────────────────────────────────

def menu_add_allergies(registry):
    """Wrapper to collect allergies from user input for menu option 8.

    Now includes try/except to handle NHIS lookup failures gracefully,
    catching KeyError separately from other unexpected exceptions.
    """
    nhis = input("NHIS number: ").strip().upper()

    try:
        # Direct dictionary access can raise KeyError if NHIS is missing
        patient = registry[nhis]

        allergy_input = input("Allergies (comma-separated, or leave blank for none): ").strip()

        if allergy_input:
            allergies = [a.strip() for a in allergy_input.split(",") if a.strip()]
            allergies = set(allergies)
            add_allergies(registry, nhis, *allergies)
        else:
            add_allergies(registry, nhis)

    except KeyError:
        print(f"❌ Patient {nhis} not found in registry. (KeyError)")

    except Exception as e:
        print(f"❌ Unexpected error during allergy update: {e}")


def menu_update_fields(registry):
    """Wrapper to collect NEW fields to add to a patient record for menu option 9.

    Asks the user for field names and values dynamically, allowing any number
    of new fields to be added (e.g., diagnosis, notes, next_of_kin, etc.).
    """
    nhis = input("NHIS number: ").strip().upper()

    patient = registry.get(nhis)
    if not patient:
        print("❌ Patient not found.")
        return

    print(f"\n📋 Current fields for {patient['name']}: {list(patient.keys())}")
    print("Enter new fields to add. Press Enter on field name to finish.\n")

    fields = {}
    while True:
        field_name = input("  Field to be added? ").strip().lower()
        if not field_name:
            break
        if field_name in patient:
            print(f"  ⚠️ '{field_name}' already exists. Current value: {patient[field_name]}")
            overwrite = input("  Overwrite? (yes/no): ").strip().lower()
            if overwrite not in ("yes", "y"):
                print("  Skipped.")
                continue
        field_value = input(f"  Value for '{field_name}': ").strip()
        fields[field_name] = field_value
        print(f"  ➕ Queued: {field_name} = {field_value}\n")

    if fields:
        update_patient_fields(registry, nhis, **fields)
    else:
        print("⚠️ No new fields to add.")


menu_actions = {
    "1": view_patients,
    "2": register_new_patient,
    "3": find_patient_by_nhis_number,
    "4": transfer_to_new_ward,
    "5": discharge_patient,
    "6": census_summary,
    "7": menu_add_allergies,      # ✅ Option 7: Add allergies
    "8": menu_update_fields,      # ✅ Option 8: Add new fields
    "9": end_system     
}


# ── MAIN PROGRAM ─────────────────────────────────────────────────
print("=" * width)
print(f"{'Eazy Tech Patient Record System':^{width}}")
print("=" * width)

menu_options = (
    "View all patients",
    "Register new patient",
    "Look up patient by NHIS-ID",
    "Transfer patient to new ward",
    "Discharge patient",
    "Ward census summary",
    "Add allergies to patient",
    "Add new/updates fields to patient record",
    "Quit"
)

while True:
    print()
    for i, option in enumerate(menu_options, start=1):
        print(f"  {i}.) {option}")

    choice = input("\nSelect an option (1 - 9): ").strip()
    func = menu_actions.get(choice)

    if not func:
        print("❌ Invalid! Choose 1 - 9")
        continue

    try:
        result = func(registry)
        if result == "QUIT":
            break
    except ValueError as e:
        print(f"❌ Registration error: {e}")
    except Exception as e:
        print(f"❌ System error: {e}")
