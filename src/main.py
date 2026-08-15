# src/main.py
"""Entry point. Deliberately contains ONLY: imports, the menu_actions
dict, load_registry(), and the main while-True loop — no function
definitions of its own. All real logic lives in patient_ops.py."""
from file_manager import load_registry
from patient_ops import (
    safe_int_input, view_patients, register_new_patient,
    menu_add_allergies, menu_update_fields, transfer_to_new_ward,
    discharge_patient, census_summary, system_status, end_system,
    look_up_patient, search_patient_by_name, schedule_appointment,
)
from config import WIDTH


def main():
    registry = load_registry()

    menu_actions = {
        1: view_patients,
        2: register_new_patient,
        3: menu_add_allergies,
        4: menu_update_fields,
        5: transfer_to_new_ward,
        6: discharge_patient,
        7: census_summary,
        8: system_status,
        9: search_patient_by_name,
        10: look_up_patient,
        11: schedule_appointment,
        12: end_system,
    }

    while True:
        print("=" * WIDTH)
        print("\n🏥 EAZY TECH PATIENT RECORDS SYSTEM - MAIN MENU\n")
        print("=" * WIDTH)
        print("1.  View patients in the system")
        print("2.  Register a new patient")
        print("3.  Add allergies to a patient record")
        print("4.  Change patient details (name or triage level)")
        print("5.  Transfer patient to another ward")
        print("6.  Discharge patient")
        print("7.  Show ward census summary")
        print("8.  Check system status")
        print("9.  Search patients by name")
        print("10. Look up full patient details")
        print("11. Schedule Next Appointment for Patient")
        print("12. Save and close the program")

        choice = safe_int_input("\nEnter selection (1-12): ")
        action = menu_actions.get(choice)

        if action:
            action(registry)
        else:
            print("❌ Invalid choice. Please choose a number between 1 and 12.")


if __name__ == "__main__":
    main()
