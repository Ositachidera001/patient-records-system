# src/patient_ops.py
from config import WIDTH, TRIAGE_INFO, VALID_TRIAGE_COLOURS
from file_manager import save_registry, log_action
from utils import format_table_row, print_patient_table

def safe_int_input(prompt):
    """Forces valid integer selection options across user interface choices."""
    while True:
        try:
            return int(input(prompt))
        except ValueError:
            print("❌ Invalid input entry. Please provide a clear numerical option value.")

def generate_next_nhis(registry):
    """Analyzes the current active database keys to auto-increment a zero-padded NHIS ID string."""
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
    """Displays tracking updates inside an organized, human-readable terminal matrix."""
    print_patient_table(registry)

def register_new_patient(registry):
    """Automates initial clinical intake registration pipelines safely."""
    print("\n--- NEW PATIENT INTAKE SEQUENCING ---")
    name = input("Enter Patient Full Name: ").strip()
    if not name:
        print("❌ Patient intake failed. Valid name tracking parameters are required.")
        return

    print(f"\nTriage Options: ")
    for color, desc in TRIAGE_INFO.items():
        print(f" - [{color.upper()}]: {desc}")
        
    triage = input("Assign Initial Triage Colour: ").strip().lower()
    if triage not in VALID_TRIAGE_COLOURS:
        print("❌ Invalid triage color code selected. Falling back to green tracking tier.")
        triage = "green"

    ward = input("Assign Initial Target Ward Destination: ").strip()
    if not ward:
        ward = "Outpatient"

    # Capture allergies at entry point
    allergy_input = input("Enter allergies separated by commas (Leave blank if None): ").strip()
    allergies = [a.strip() for a in allergy_input.split(",") if a.strip()] if allergy_input else []

    nhis_id = generate_next_nhis(registry)
    
    registry[nhis_id] = {
        "name": name,
        "triage": triage,
        "status": "Admitted",
        "ward": ward,
        "allergies": allergies
    }

    if save_registry(registry):
        log_action(f"Registered patient {name.upper()} as {nhis_id} to {ward.title()} Ward [Triage: {triage.upper()}].")
        print(f"\n✅ Intake processing complete. Patient: {name.upper()} assigned ID: {nhis_id}")

def find_patient_by_nhis_number(registry):
    """Locates individual records for inspection."""
    while True:
        try:
            raw = input("\nEnter Target Patient NHIS ID (e.g. NHIS-0001): ").strip()
            nhis_id = raw.upper()
        except Exception as e:
            print(f"Invalid NHIS ID. error due to {e}")
            continue

        if nhis_id not in registry:
            print("❌ Target verification parameter match missing inside local records database.")
            return None
        return nhis_id

def menu_add_allergies(registry):
    """Access point workflow interface targeting clinical allergy updates."""
    nhis_id = find_patient_by_nhis_number(registry)
    if not nhis_id:
        return
        
    new_allergies = input("Enter new allergy warnings to attach (separated by commas): ").strip()
    if new_allergies:
        added_list = [a.strip() for a in new_allergies.split(",") if a.strip()]
        registry[nhis_id]["allergies"].extend(added_list)
        # Ensure values stay unique
        registry[nhis_id]["allergies"] = list(set(registry[nhis_id]["allergies"]))
        
        if save_registry(registry):
            log_action(f"Updated allergy tracking files for {nhis_id}: Added {added_list}")
            print(f"✅ Allergy warnings {added_list} added successfully.")

def menu_update_fields(registry):
    """Dynamic demographic monitoring adjustments handler."""
    nhis_id = find_patient_by_nhis_number(registry)
    if not nhis_id:
        return
        
    print(f"\nUpdating Records for {nhis_id} ({registry[nhis_id]['name']})")
    print("1. Update Patient Name")
    print("2. Re-evaluate Triage Urgency Level")
    choice = safe_int_input("Select target category update field choice: ")
    
    if choice == 1:
        new_name = input("Enter corrected full name: ").strip()
        if new_name:
            old_name = registry[nhis_id]["name"]
            registry[nhis_id]["name"] = new_name
            if save_registry(registry):
                log_action(f"Administrative database correction: {nhis_id} altered from {old_name} to {new_name}")
                print("✅ Identity database values successfully resolved.")
    elif choice == 2:
        print("\nNew Triage Targets: ")
        for color, desc in TRIAGE_INFO.items():
            print(f" - [{color.upper()}]: {desc}")
        new_triage = input("Select updated triage assignment: ").strip().lower()
        if new_triage in VALID_TRIAGE_COLOURS:
            registry[nhis_id]["triage"] = new_triage
            if save_registry(registry):
                log_action(f"Triage modification update for {nhis_id}: Shifted to {new_triage.upper()}")
                print("✅ Patient condition rating adjusted.")

def transfer_to_new_ward(registry):
    """Manages system tracking updates for floor level transfers."""
    nhis_id = find_patient_by_nhis_number(registry)
    if not nhis_id:
        return
        
    old_ward = registry[nhis_id]["ward"]
    new_ward = input(f"Enter target relocation ward (Current: {old_ward}): ").strip()
    if new_ward:
        registry[nhis_id]["ward"] = new_ward
        if save_registry(registry):
            log_action(f"Transferred patient {nhis_id} from {old_ward} Ward to {new_ward} Ward.")
            print(f"✅ Patient successfully checked into {new_ward} Ward units.")

def discharge_patient(registry):
    """Handles discharge sequencing securely while preserving processing history logs."""
    nhis_id = find_patient_by_nhis_number(registry)
    if not nhis_id:
        return
        
    registry[nhis_id]["status"] = "Discharged"
    registry[nhis_id]["ward"] = "None (Discharged)"
    if save_registry(registry):
        log_action(f"Authorized discharge sequencing workflow execution for {nhis_id}.")
        print("✅ Patient files flags finalized for checkout. Discharge tracking processed.")

def census_summary(registry):
    """Compiles operational logistics breakdowns for shift management reporting."""
    print("\n" + "═"*WIDTH + f"\n{'WARD LOCATION LOGISTICS CENSUS SUMMARY':^{WIDTH}}\n" + "═"*WIDTH)
    if not registry:
        print("⚠️ Application reporting engine indicates clean storage files.")
        return
        
    wards = {}
    triage_counts = {"red": 0, "yellow": 0, "green": 0}
    
    for p in registry.values():
        if p["status"] == "Admitted":
            w = p["ward"]
            wards[w] = wards.get(w, 0) + 1
            t = p["triage"]
            if t in triage_counts:
                triage_counts[t] += 1
                
    print("\n📍 Active Patient Counts Across Units:")
    for w_name, count in wards.items():
        print(f"  • {w_name:<18}: {count} Patient(s)")
        
    print("\n🚨 System Risk Tracking Profile Matrix Summary:")
    print(f"  🔴 [RED] Critical   : {triage_counts['red']}")
    print(f"  🟡 [YELLOW] Urgent  : {triage_counts['yellow']}")
    print(f"  🟢 [GREEN] Routine  : {triage_counts['green']}\n" + "═"*WIDTH)

def end_system(registry):
    """Gracefully handles standard exit sequencing."""
    print("\nClosing Clinical Application tracking subsystems... Always double-checking save states.")
    save_registry(registry)
    log_action("System core execution cycle terminated normally by user command input request.")
    print("👋 System offline.")
    exit()