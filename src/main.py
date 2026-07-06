# src/main.py
from file_manager import load_registry
from patient_ops import (safe_int_input, view_patients, register_new_patient,
    menu_add_allergies, menu_update_fields, transfer_to_new_ward,
    discharge_patient, census_summary, end_system)
from config import WIDTH

def main():
    # Active runtime persistence mapping data load routine
    registry = load_registry()

    menu_actions = {
        1: view_patients,
        2: register_new_patient,
        3: menu_add_allergies,
        4: menu_update_fields,
        5: transfer_to_new_ward,
        6: discharge_patient,
        7: census_summary,
        8: lambda r: print(f"\n🔍 Active Registry Database Verification Size: {len(r)} keys loaded."),
        9: end_system
    }

    while True:
        print("=" * WIDTH)
        print("\n🏥EAZY TECH PATIENT RECORDS SYSTEM - MAIN MENU\n")
        print("=" * WIDTH)
        print("1. View patients in the system")
        print("2. Register a new patient")
        print("3. Add allergies to a patient record")
        print("4. Change patient details (name or triage level)")
        print("5. Transfer patient to a another ward")
        print("6. Discharge patient")
        print("7. Show how many patients are in each ward")
        print("8. Check system status")
        print("9. Save and close the program")
        choice = safe_int_input("\nEnter processing selection choice (1-9): ")
        
        action = menu_actions.get(choice)
        if action:
            action(registry)
        else:
            print("❌ Input validation boundary error. Choose option commands between 1 and 9 values.")

if __name__ == "__main__":
    main()