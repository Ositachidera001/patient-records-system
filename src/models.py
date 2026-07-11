class Patient:
    """Represents a single hospital patient with all clinical attributes."""
    def __init__(self, name, age, nhis_number, ward, triage):
        """constructor - runs automatically when a patient is called"""
        self.name = name.strip().title()
        self.age = age
        self.nhis_number = nhis_number.strip().upper()
        self.ward = ward.strip().lower()
        self.triage = triage.strip().upper()
        self.admission_status = True
        self.allergies = []

    def __str__(self):
        """Human - readable summary -- what print(patient shows."""
        status = "Admitted" if self.admission_status else "Discharge"
        return (f"[{self.nhis_number}] {self.name} | {self.ward.title()} "
                f"| {self.triage.upper()} | {status}")

    def __repr__(self):
        """Developer-facing representation -- enough detail to reconstruct the object."""
        return (f"Patient(name={self.name!r}, age={self.age!r}, "
                f"nhis_number={self.nhis_number!r}, ward={self.ward!r}, "
                f"triage={self.triage!r})")

    # build the methods from the previous functions
    def admit(self):
        """Mark this patient as admitted."""
        self.admission_status = True
        print(f"✅ {self.name} admitted.")

    def discharge(self):
        """Mark this patient as admitted."""
        self.admission_status = False
        print(f"🟠 {self.name} discharged.")

    def add_allergy(self, *new_allergies):
        """Add one or more allergies to this patient's record"""
        existing = set(self.allergies)
        added = [allergy.strip() for allergy in new_allergies if allergy.strip() not in existing]
        self.allergies.extend(added)
        return added
    
    def transfer(self, new_ward):
        """Move this patients to a new ward"""
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
            "name" : self.name,
            "age"  : self.age,
            "nhis_number"  : self.nhis_number,
            "ward"  : self.ward,
            "triage"  : self.triage,
            "admission_status"  : self.admission_status,
            "allergies"  : self.allergies
        }
    @classmethod
    def from_dict(cls, data):
        """Create a patient instance from a dictionary (for JSON loading)"""
        p = cls(data["name"], data["age"], data["nhis_number"], data["ward"], data["triage"])
        p.admission_status = data.get("admission_status", True)
        p.allergies = data.get("allergies", [])
        return p
    
class PaediatricPatient(Patient):
    """A child patient. is a Patient, with extra weight and guardian tracking."""

    def __init__(self, name, age, nhis_number, ward, triage, weight_kg, guardian_name):
        """Build a PaediatricPatient, reusing Patient's setup via super()."""
        super().__init__(name, age, nhis_number, ward, triage)
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
        """
Override of a weight-based dose calculation that uses THIS patient's own weight.
Args:
drug_mg_per_kg (float): dosage rate in mg per kilogram of body weight.
Returns:
str: a formatted dose string, e.g. "220.0 mg for Chidi Okeke (22kg)".
"""
        dose = drug_mg_per_kg * self.weight_kg
        return f"{dose:.1f} mg for {self.name} ({self.weight_kg}kg)"
    
    def to_dict(self):
        """convert this paediatric patient to a dict, including paediatric-only fields."""
        data = super().to_dict()
        data["weight_kg"] = self.weight_kg
        data["guardian_name"] = self.guardian_name
        return data
    
    @classmethod
    def from_dict(cls, data):
        """Build a PaediatricPatient instance from a dictionary (for json loading)."""
        p = cls(data["name"], data["age"], data["nhis_number"], data["ward"], data["triage"], data["weight_kg"], data["guardian_name"])
        p.admission_status = data.get("admission_status", True)
        p.allergies = data.get("allergies", [])
        return p
    
class PatientRegistry:
    """Wraps a collection of patient objects and offers registry-level operations. 
    this is an object-oriented analogue of the plain 'registry' dict used previous"""
    def __init__(self):
        """start with an empty registry, keyed by nhis_number."""
        self._patients = {}

    def add(self, patient):
        """Add a patient (adult or padiatric) to the registry, keyed by its nhis_number"""
        self._patients[patient.nhis_number] = patient
        print(f"✅ {patient.name} added to registry as {patient.nhis_number}.")

    def find(self, nhis_number):
        """Look up a patient by nhis number. Returns none if not found."""
        return self._patients.get(nhis_number.strip().upper())
    
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
        """convert the whole registry into a plain dict of dicts (for JSON saving)."""
        return {nhis: patient.to_dict() for nhis, patient in self._patients.items()}
    
    @classmethod
    def from_dict(cls, data):
        """Rebuild a PatientRegistry from a dict of dicts (for JSON loading).
        Records conataining a 'weight_kg' field are restored as PaediatricPatient; everything else is restored as plain patient."""
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
        """Developer representation showing how many patients are registereed."""
        return f"PatientRegistry({len(self._patients)} patients)"