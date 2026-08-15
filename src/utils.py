"""
utils.py

Shared display/formatting helpers. Kept separate from patient_ops.py so
that "how do we show a patient" is decoupled from "what menu action are
we running" — a classic separation-of-concerns split.
"""
from datetime import datetime, date

from config import TRIAGE_RANK


def format_table_row(nhis, name, triage, status, ward, allergies):
    """Build one aligned row string for the patient table."""
    allergy_str = ", ".join(allergies) if allergies else "None"
    return (f"|| {nhis:<10} | {name:<18} | {triage.upper():<8} | "
            f"{status:<10} | {ward:<12} | {allergy_str:<20} ||")


def print_patient_table(registry, width=60):
    """Print every patient in `registry` (dict keyed by NHIS number) as a
    formatted table, sorted so the most urgent triage colour is shown
    first: RED, then YELLOW, then GREEN.

    This is a plain sorted() call with a key function — the same pattern
    from Lesson 9, applied to registry.items() instead of a simple list.
    """
    if not registry:
        print("\n" + "=" * width + "\n⚠️ No patients currently active.\n" + "=" * width)
        return

    header = "|| {:<10} | {:<18} | {:<8} | {:<10} | {:<12} | {:<20} ||".format(
        "NHIS-ID", "PATIENT NAME", "TRIAGE", "STATUS", "WARD", "ALLERGIES"
    )
    sep = "=" * len(header)

    # key=lambda item: TRIAGE_RANK.get(item[1]["triage"], 4)
    #   item is an (nhis_id, patient_dict) tuple from registry.items()
    #   item[1]["triage"] pulls out "red"/"yellow"/"green"
    #   TRIAGE_RANK maps that to 1/2/3 (unknown values sort last, as 4)
    sorted_patients = sorted(
        registry.items(),
        key=lambda item: TRIAGE_RANK.get(item[1]["triage"], 4)
    )

    print("\n" + sep)
    print(f"|| {'PATIENT REGISTRY (sorted: RED first)':^{len(header) - 6}} ||")
    print(sep)
    print(header)
    print(sep)

    for nhis_id, p in sorted_patients:
        status = "Admitted" if p.get("admission_status", True) else "Discharged"
        print(format_table_row(
            nhis_id, p["name"].upper(), p["triage"].upper(), status.upper(),
            p["ward"].upper(), p.get("allergies", [])
        ))

    print(sep)

def calculate_patient_age(birth_date_str : str) -> tuple[int, str]:
    """calculate's patient's age in whole years from a date string YYYY-MM-DD.
    And returns both age and the orignial  dob string. returns (0, "Not Provided")
    if birth_date_str is empty.
    """
    if not birth_date_str:
        return 0, "Not Provided"
    try:
        birth_date = datetime.strptime(birth_date_str, "%Y-%m-%d").date()
        today = date.today()
        age = today.year - birth_date.year

        # adjustment if birthday hasn't happened yet this year.
        birthday_this_year = birth_date.replace(year=today.year)
        # if today < birthday_this_year:
        #     age -= 1
        # return age
        adjusted_age = age -1, birth_date_str if today < birthday_this_year else age
        return adjusted_age, birth_date_str
    except ValueError:
        raise ValueError(f"Invalid date format '{birth_date_str}' -- usr YYYY-MM-DD")

def check_drug_expiry(drug_name: str, expiry_str: str) -> int:
    """Returns days remaining for a drug.
    Prints color-coded warnings based on status.
    """
    try:
        expiry_date = datetime.strptime(expiry_str, "%Y-%m-%d").date()
        days_left = (expiry_date - date.today()).days

        if days_left < 0:
            print(f"🔴 Expired: {drug_name} expired {abs(days_left)} day(s) ago!")
        elif days_left < 30:
            print(f"🟡 Warning: {drug_name} expires in {days_left} day(s)!")
        else:
            print(f"🟢 Safe: {drug_name} is safe ({days_left} days remaining).")

        return days_left
    except ValueError:
        print(f"❌ Invalid expiry date format for {drug_name}: '{expiry_str}'. ")
        return None

def scan_patient_expiries(patient_record: dict) -> None:
    """
    Scans a patient record dictionary for any key containing ''expiry' 
    and triggers check_drug_expiry automatically.
    """
    for key, value in patient_record.items():
        if "expiry" in key.lower() and isinstance(value, str):
            drug_label = key.replace("_", " ").title()
            check_drug_expiry(drug_label, value)