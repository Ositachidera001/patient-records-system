"""
test_models.py

Standalone demonstration/verification script for src/models.py.
Run with:  python test_models.py   (from the project root)

Creates Patient and PaediatricPatient instances, exercises every method,
and verifies that to_dict() -> from_dict() round-trips correctly.
"""

import sys
import os

# Make sure "src" is importable when this file is run from the project root.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from models import Patient, PaediatricPatient, PatientRegistry  # noqa: E402


def section(title):
    """Print a labelled section divider so terminal output is easy to scan."""
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def main():
    """Run through every required demonstration in order."""

    # ------------------------------------------------------------------
    section("1. CREATE TWO PATIENT INSTANCES")
    # ------------------------------------------------------------------
    amina = Patient("amina bello", 34, "nhis-0001", "emergency", "red")
    ken = Patient("ken okafor", 45, "nhis-0002", "cardiology", "yellow")
    print(amina)   # __str__
    print(ken)     # __str__
    print(repr(amina))  # __repr__
    print(repr(ken))    # __repr__

    # ------------------------------------------------------------------
    section("2. admit() / discharge()")
    # ------------------------------------------------------------------
    amina.discharge()
    print(amina)
    amina.admit()
    print(amina)

    # ------------------------------------------------------------------
    section("3. add_allergy(*allergies)")
    # ------------------------------------------------------------------
    added = amina.add_allergy("Penicillin", "Latex")
    print("Newly added:", added)
    again = amina.add_allergy("Penicillin")  # duplicate, should not re-add
    print("Duplicate attempt added:", again)
    print("amina.allergies:", amina.allergies)
    print("ken.allergies (should be untouched):", ken.allergies)

    # ------------------------------------------------------------------
    section("4. transfer(new_ward)")
    # ------------------------------------------------------------------
    ken.transfer("icu")
    print(ken)

    # ------------------------------------------------------------------
    section("5. to_dict() / from_dict() ROUND TRIP")
    # ------------------------------------------------------------------
    amina_dict = amina.to_dict()
    print("amina.to_dict():", amina_dict)

    rebuilt_amina = Patient.from_dict(amina_dict)
    print("Rebuilt from dict:", repr(rebuilt_amina))

    assert rebuilt_amina.to_dict() == amina_dict, "Round-trip FAILED for Patient!"
    print("✅ Patient round-trip verified: to_dict() -> from_dict() -> to_dict() matches.")

    # ------------------------------------------------------------------
    section("6. PaediatricPatient SUBCLASS + calculate_dose()")
    # ------------------------------------------------------------------
    chidi = PaediatricPatient(
        "chidi okeke", 6, "nhis-0003", "paediatrics", "green",
        weight_kg=22, guardian_name="ngozi okeke",
    )
    print(chidi)          # overridden __str__
    print(repr(chidi))    # overridden __repr__

    print(chidi.calculate_dose(10))  # overridden method, uses chidi's own weight

    # isinstance check to prove the IS-A relationship
    print("isinstance(chidi, Patient):", isinstance(chidi, Patient))
    print("isinstance(chidi, PaediatricPatient):", isinstance(chidi, PaediatricPatient))
    print("isinstance(amina, PaediatricPatient):", isinstance(amina, PaediatricPatient))

    # Round-trip check for the subclass too
    chidi_dict = chidi.to_dict()
    rebuilt_chidi = PaediatricPatient.from_dict(chidi_dict)
    assert rebuilt_chidi.to_dict() == chidi_dict, "Round-trip FAILED for PaediatricPatient!"
    print("✅ PaediatricPatient round-trip verified.")

    # ------------------------------------------------------------------
    section("7. BONUS: PatientRegistry")
    # ------------------------------------------------------------------
    registry = PatientRegistry()
    registry.add(amina)
    registry.add(ken)
    registry.add(chidi)
    print(registry)  # __repr__
    print("len(registry):", len(registry))

    found = registry.find("nhis-0002")
    print("registry.find('nhis-0002'):", found)

    print("Census before discharge:", registry.census())
    registry.discharge("NHIS-0002")
    print("Census after discharging ken:", registry.census())

    registry_dict = registry.to_dict()
    rebuilt_registry = PatientRegistry.from_dict(registry_dict)
    assert rebuilt_registry.to_dict() == registry_dict, "Round-trip FAILED for PatientRegistry!"
    print("✅ PatientRegistry round-trip verified.")
    print("Rebuilt registry contains a PaediatricPatient for NHIS-0003:",
          isinstance(rebuilt_registry.find("NHIS-0003"), PaediatricPatient))

    section("ALL CHECKS PASSED ✅")


if __name__ == "__main__":
    main()
