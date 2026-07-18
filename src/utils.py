"""
utils.py

Shared display/formatting helpers. Kept separate from patient_ops.py so
that "how do we show a patient" is decoupled from "what menu action are
we running" — a classic separation-of-concerns split.
"""
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
