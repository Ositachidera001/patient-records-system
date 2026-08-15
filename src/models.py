"""
models.py

Object-oriented core of the Patient Records System (Lesson 14).

Patient            -- one adult patient, with all clinical attributes.
PaediatricPatient   -- a Patient subclass adding weight + guardian info.
PatientRegistry     -- an OOP wrapper around a collection of Patients
                       (this is the bonus "registry as an object"
                       alternative to the plain dict used elsewhere).
"""


class Patient:
    """Represents a single hospital patient with all clinical attributes."""

    def __init__(self, name, age, date_of_birth, nhis_number, ward, triage):
        """Constructor — runs automatically when Patient(...) is called."""
        self.name = name.strip().title()
        self.age = age
        self.date_of_birth = date_of_birth
        self.nhis_number = nhis_number.strip().upper()
        self.ward = ward.strip().lower()
        # Stored lowercase to match config.TRIAGE_RANK / TRIAGE_INFO / VALID_TRIAGE_COLOURS
        # keys ("red"/"yellow"/"green"). Display code calls .upper() where needed.
        self.triage = triage.strip().lower()
        self.admission_status = True
        self.allergies = []

    def __str__(self):
        """Human-readable summary -- what print(patient) shows."""
        status = "Admitted" if self.admission_status else "Discharged"
        return (f"[{self.nhis_number}] {self.name} | {self.ward.title()} "
                f"| {self.triage.upper()} | {status}")

    def __repr__(self):
        """Developer-facing representation -- enough detail to reconstruct the object."""
        return (f"Patient(name={self.name!r}, age={self.age!r}, "
                f"nhis_number={self.nhis_number!r}, ward={self.ward!r}, "
                f"triage={self.triage!r})")

    def admit(self):
        """Mark this patient as admitted."""
        self.admission_status = True
        print(f"✅ {self.name} admitted.")

    def discharge(self):
        """Mark this patient as discharged."""
        self.admission_status = False
        print(f"🟠 {self.name} discharged.")

    def add_allergy(self, *new_allergies):
        """Add one or more allergies to this patient's record, skipping duplicates.

        Uses *args so callers can pass any number of allergies:
            patient.add_allergy("Penicillin")
            patient.add_allergy("Penicillin", "Latex", "Iodine")

        Returns the list of allergies that were actually newly added.
        """
        existing = set(self.allergies)
        added = [a.strip() for a in new_allergies if a.strip() and a.strip() not in existing]
        self.allergies.extend(added)
        return added

    def transfer(self, new_ward):
        """Move this patient to a new ward."""
        old_ward = self.ward
        self.ward = new_ward.strip().lower()
        print(f"✅ {self.name} transferred from: {old_ward} to {self.ward}.")

    def summary(self):
        """Return a formatted one-line summary of this patient."""
        status = "Admitted" if self.admission_status else "Discharged"
        return (f"{self.nhis_number} | {self.name:20} | {self.triage.upper():6} "
                f"| {status:10} | {self.ward:12} | {self.allergies}")

    def to_dict(self):
        """Convert this patient to a plain dictionary (for JSON saving)."""
        return {
            "name": self.name,
            "age": self.age,
            "date_of_birth" : self.date_of_birth,
            "nhis_number": self.nhis_number,
            "ward": self.ward,
            "triage": self.triage,
            "admission_status": self.admission_status,
            "allergies": self.allergies,
        }

    @classmethod
    def from_dict(cls, data):
        """Create a Patient instance from a dictionary (for JSON loading)."""
        p = cls(data["name"], data["age"], data["date_of_birth"], data["nhis_number"], data["ward"], data["triage"])
        p.admission_status = data.get("admission_status", True)
        p.allergies = data.get("allergies", [])
        return p


class PaediatricPatient(Patient):
    """A child patient. IS-A Patient, with extra weight and guardian tracking."""

    def __init__(self, name, age, date_of_birth, nhis_number, ward, triage, weight_kg, guardian_name):
        """Build a PaediatricPatient, reusing Patient's setup via super()."""
        super().__init__(name, age, date_of_birth, nhis_number, ward, triage)
        self.weight_kg = weight_kg
        self.guardian_name = guardian_name.strip().title()

    def __str__(self):
        """Human-readable summary that also shows the guardian's name."""
        status = "Admitted" if self.admission_status else "Discharged"
        return (f"[PAED][{self.nhis_number}] {self.name} | Guardian: {self.guardian_name} "
                f"| {self.ward.title()} | {self.triage.upper()} | {status}")

    def __repr__(self):
        """Developer-facing representation including the paediatric-only fields."""
        return (f"PaediatricPatient(name={self.name!r}, age={self.age!r}, "
                f"nhis_number={self.nhis_number!r}, ward={self.ward!r}, "
                f"triage={self.triage!r}, weight_kg={self.weight_kg!r}, "
                f"guardian_name={self.guardian_name!r})")

    def calculate_dose(self, drug_mg_per_kg):
        """Override: weight-based dose calculation using THIS patient's own weight.

        Args:
            drug_mg_per_kg (float): dosage rate in mg per kilogram of body weight.
        Returns:
            str: a formatted dose string, e.g. "220.0 mg for Chidi Okeke (22kg)".
        """
        dose = drug_mg_per_kg * self.weight_kg
        return f"{dose:.1f} mg for {self.name} ({self.weight_kg}kg)"

    def to_dict(self):
        """Convert this paediatric patient to a dict, including paediatric-only fields."""
        data = super().to_dict()
        data["weight_kg"] = self.weight_kg
        data["guardian_name"] = self.guardian_name
        return data

    @classmethod
    def from_dict(cls, data):
        """Build a PaediatricPatient instance from a dictionary (for JSON loading)."""
        p = cls(data["name"], data["age"], data["date_of_birth"], data["nhis_number"], data["ward"], data["triage"],
                 data["weight_kg"], data["guardian_name"])
        p.admission_status = data.get("admission_status", True)
        p.allergies = data.get("allergies", [])
        return p


class PatientRegistry:
    """Wraps a collection of Patient objects and offers registry-level operations.

    This is an object-oriented analogue of the plain `registry` dict used
    elsewhere in the app (patient_ops.py uses the plain-dict version for
    simplicity + easy JSON storage; this class is the bonus OOP version).
    """

    def __init__(self):
        """Start with an empty registry, keyed by nhis_number."""
        self._patients = {}

    def add(self, patient):
        """Add a patient (adult or paediatric) to the registry, keyed by its nhis_number."""
        self._patients[patient.nhis_number] = patient
        print(f"✅ {patient.name} added to registry as {patient.nhis_number}.")

    def find(self, nhis_number):
        """Look up a patient by NHIS number. Returns None if not found."""
        return self._patients.get(nhis_number.strip().upper())

    def search_by_name(self, query):
        """Bonus: partial, case-insensitive search by patient name.

        Returns a list of matching Patient (or PaediatricPatient) objects,
        e.g. search_by_name("oke") would match both "Chidi Okeke" and
        "Ken Okafor" would NOT match (only "oke" substrings match).
        """
        query = query.strip().lower()
        return [p for p in self._patients.values() if query in p.name.lower()]

    def discharge(self, nhis_number):
        """Discharge the patient with the given nhis_number, if they exist."""
        patient = self.find(nhis_number)
        if patient is None:
            print(f"❌ No patient found with NHIS number {nhis_number}.")
            return False
        patient.discharge()
        return True

    def census(self):
        """Return a dict of {ward: count_of_currently_admitted_patients}."""
        wards = {}
        for patient in self._patients.values():
            if patient.admission_status:
                wards[patient.ward] = wards.get(patient.ward, 0) + 1
        return wards

    def to_dict(self):
        """Convert the whole registry into a plain dict of dicts (for JSON saving)."""
        return {nhis: patient.to_dict() for nhis, patient in self._patients.items()}

    @classmethod
    def from_dict(cls, data):
        """Rebuild a PatientRegistry from a dict of dicts (for JSON loading).

        Records containing a 'weight_kg' field are restored as
        PaediatricPatient; everything else is restored as a plain Patient.
        """
        registry = cls()
        for nhis, patient_data in data.items():
            if "weight_kg" in patient_data:
                patient = PaediatricPatient.from_dict(patient_data)
            else:
                patient = Patient.from_dict(patient_data)
            registry._patients[nhis] = patient
        return registry

    def __len__(self):
        """Number of patients currently in the registry. Enables len(registry)."""
        return len(self._patients)

    def __repr__(self):
        """Developer representation showing how many patients are registered."""
        return f"PatientRegistry({len(self._patients)} patients)"
