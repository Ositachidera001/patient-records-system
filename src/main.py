# Developer: Osita Chidera
# Date: 15/06/2026
width = 50
triage_info = {
    "red"        : "Immediate - Life threatening",
    "yellow"     : "Urgent - Within 1 hour",
    "green"      : "Routine - Can wait."
}
registry = {
    "NHIS-0001": {"name"            : "Amina Bello", 
                  "age"             : 34, 
                  "nhis_number"     : "nhis-0001", 
                  "ward"            : "emergency", 
                  "triage"          : "red", 
                "admission_status"  : True},
    "NHIS-0002": {"name"            : "Ken Okoro", 
                  "age"             : 28, 
                  "nhis_number"     : "nhis-0002", 
                  "ward"            : "cardiology", 
                  "triage"          : "yellow", 
                "admission_status"  : True},
    "NHIS-0003": {"name"            : "Adams Sarah", 
                  "age"             : 26, 
                  "nhis_number"     : "nhis-0003", 
                  "ward"            : "antenatal", 
                  "triage"          : "green", 
                "admission_status"  : False}
}
def view_patients(registry):
    """Display all patients in the registry."""
    print("\n--- ALL PATIENTS ---")
    if not registry:
        print("No patient(s) admitted")
        return
    for nhis_number, p in registry.items():
        status = "Admitted" if p["admission_status"] else "Discharge"
        print(f" {nhis_number} | {p['name']} | Age {p['age']} | {p['ward']} | {p['triage']} | {status}")
def register_new_patient(registry):
    """Collect input, Register a new patient"""
    name = input("Full name: ").strip().title()
    age = int(input("Age: "))
    nhis_number = input("NHIS number: ").strip().upper()
    ward = input("Ward: ").strip().lower()
    triage = input("Enter Triage Colour (RED/YELLOW/GREEN): ").strip().lower()
    if nhis_number in registry:
            print(f"❌ {nhis_number} already exists.")
    else:
        registry[nhis_number] = {
            "name"             :  name,
            "age"              :  age,
            "nhis_number"      :  nhis_number,
            "ward"             :  ward,
            "triage"           :  triage,
            "admission_status" :  True
            }
        print(f"✅ {name.title()} Registered under {nhis_number}")
        print("\n TRIAGE LOOKUP")
        if triage in triage_info:
            print(triage_info.get(triage, "Unknown"))
def find_patient_by_nhis_number(registry):
    """Finding patient by nhis-number"""
    nhis_number = input("Enter NHIS number: ").strip().upper()
    patient = registry.get(nhis_number)
    if patient:
        print(f"Found: {patient['name']}, Age {patient['age']}, Ward {patient['ward']}, Triage {patient['triage']}")
    else:
        print(f"❌ Patient {nhis_number} not found in registry.")
def transfer_to_new_ward(registry):
    """Transferring of patients to a new ward"""
    nhis_number = input("NHIS to transfer: ").strip().upper()
    patient = registry.get(nhis_number)
    if not patient:
        print("❌ Not Found.")
    else:
        new_ward = input(f"Current ward: {patient['ward']}. New Ward: ")
        patient["ward"] = new_ward
        print(f"✅ {patient['name']} transferred to {new_ward}")
def discharge_patient(registry):
    """Discharge patient"""
    nhis_number = input("Nhis to discharge: ").strip().upper()
    if nhis_number in registry:
        registry[nhis_number]["admission_status"] = False
        print(f"🟠 Discharge:  {registry[nhis_number]["name"]}. ")
    else:
        print("❌ Not Found.")
def census_summary(registry):
    """Census summary of registry"""
    total = sum(1 for p in registry.values() if p["admission_status"])
    print(f"\n--- WARD CENSUS ---")
    print(f"Total Patient: {total}")
    ward_count = {}
    occupied_wards = set() 
    for p in registry.values():
        if p["admission_status"]:
            ward = p["ward"]
            occupied_wards.add(ward)
            ward_count[ward] = ward_count.get(ward, 0) + 1
    for ward, count in ward_count.items():
        print(f" {ward}: {count} patient(s)")
    print(f"\n Occupied wards: {occupied_wards}")
    return ward_count, occupied_wards
def end_system(registry):
    """Shutting Down the system"""
    print("\n=== SHUTDOWN ===")
    print(F"Patients remaining in registry: {len(registry)}")
    print("Goodbye, Stay Safe! 🦾")
    return "QUIT"
menu_actions = {
    "1"     :   view_patients,
    "2"     :   register_new_patient,
    "3"     :   find_patient_by_nhis_number,
    "4"     :   transfer_to_new_ward,
    "5"     :   discharge_patient,
    "6"     :   census_summary,
    "7"     :   end_system
}
print('='*width)
print(f"          Eazy Tech Patient Record System")
print('='*width)
menu_options = ("view all patients", 
                "register new patient", 
                "look up patient by nhis-id", 
                "transfer patient to new ward", 
                "discharge patient", 
                "ward census summary", 
                "quit")
while True:
    for option, menu in enumerate(menu_options, start=1):
        print(f"{option}.) {menu}")
    choice = input("Select an option (1 - 7): ").strip()
    func = menu_actions.get(choice)
    if not func:
        print("❌ Invalid! Choose 1 - 7")
        continue
    result = func(registry)
    if result == "QUIT":
        break