# 🏥 Patient Records System

**Domain badge: 🏥 Health IT**

## 📋 Description

A command-line patient registry and triage system for a hospital front desk.
Patients are registered with a triage colour (RED/YELLOW/GREEN), tracked
through wards, and can be transferred, updated, or discharged — with every
change written straight to disk and to an audit log.

This started as a Lesson 9 (Functions) exercise and has been rebuilt as the
final capstone project, folding in OOP (Lesson 14), error handling
(Lesson 11), and file persistence (Lesson 12) into one production-shaped app.

## 🏗️ Architecture

The project is a proper `src/` package, split by responsibility — no logic
lives in the project root, and no single file is a monolith:

```
patient-records-system/
├── src/
│   ├── __init__.py        # package marker only, no logic
│   ├── config.py          # paths + constants (single source of truth)
│   ├── models.py          # Patient, PaediatricPatient, PatientRegistry (OOP)
│   ├── file_manager.py    # JSON load/save + audit log
│   ├── utils.py           # table formatting / display helpers
│   ├── patient_ops.py     # every menu action lives here
│   ├── main.py            # imports + menu wiring + the while-True loop ONLY
│   └── data/              # registry.json + audit_log.txt (created at runtime)
├── test_models.py         # standalone OOP demo/verification script
├── .gitignore
└── README.md
```

`config.py` builds every path from `os.path.dirname(os.path.abspath(__file__))`,
so it always resolves relative to `src/` itself — it doesn't matter whether
you launch the app from the project root, from inside `src/`, or from
somewhere else entirely.

## 🚀 How to Run

```bash
git clone <this-repo>
cd patient-records-system
python src/main.py
```

To run the standalone OOP verification script instead:

```bash
python test_models.py
```

## 🧰 Technologies Used

| Technique                                   | Lesson Introduced        | Where it lives                                   |
|----------------------------------------------|---------------------------|---------------------------------------------------|
| Functions, default/keyword args              | Lesson 9 (Functions)      | `patient_ops.py`, `multi_domain_functions.py`     |
| Classes, inheritance, `super()`, dunder methods | Lesson 14 (OOP)         | `models.py` — `Patient` → `PaediatricPatient`     |
| `*args`                                       | Lesson 14 (OOP)           | `Patient.add_allergy(*new_allergies)`             |
| `**kwargs`                                    | Lesson 14 (OOP) / 9      | `update_patient_fields(patient_dict, **kwargs)`   |
| `try/except/finally`, custom `raise ValueError` | Lesson 11 (Error Handling) | `patient_ops.py` (age validation, `census_summary`) |
| `while True` input-retry loops                | Lesson 11 (Error Handling) | `safe_int_input()`, age prompt                    |
| JSON file persistence                         | Lesson 12 (File I/O)      | `file_manager.py` (`save_registry`/`load_registry`) |
| Timestamped audit logging                     | Lesson 12 (File I/O)      | `file_manager.log_action()`                       |
| `sorted()` with a `key=` function             | Lesson 9 (Functions)      | `utils.print_patient_table()` — RED sorts first   |
| Sets, dict comprehensions                     | Lesson 9/11               | `census_summary()` occupied wards, `search_patient_by_name()` |

## ⚙️ Menu Options

| # | Action |
|---|--------|
| 1 | View all patients — table sorted RED → YELLOW → GREEN |
| 2 | Register a new patient (auto NHIS ID, validated age & triage) |
| 3 | Add allergies (deduplicated) |
| 4 | Update patient name or triage level |
| 5 | Transfer patient to a new ward |
| 6 | Discharge patient |
| 7 | Ward census + triage risk matrix (with timestamp) |
| 8 | System status (registry size + data file check) |
| 9 | Save and quit |
| 10 ⭐ | Look up one patient's full details |
| 11 ⭐ | Search patients by (partial) name |

## 🖥️ Sample Terminal Session (screenshot)

```
⚠ No saved registry found at .../src/data/registry.json. Starting fresh.
============================================================
🏥 EAZY TECH PATIENT RECORDS SYSTEM - MAIN MENU
============================================================
1. View patients in the system
2. Register a new patient
...
Enter selection (1-11): 2
--- NEW PATIENT INTAKE ---
Enter Patient Full Name: Amina Bello
Enter Patient Age: 34
Assign Initial Triage Colour: red
Assign Initial Ward: Emergency
Enter allergies, comma-separated (blank if none): Penicillin, Latex
✅ Registry saved to .../src/data/registry.json
✅ Registered. Patient AMINA BELLO assigned ID: NHIS-0001

Enter selection (1-11): 1
===================================================================================================
||                             PATIENT REGISTRY (sorted: RED first)                              ||
===================================================================================================
|| NHIS-ID    | PATIENT NAME       | TRIAGE   | STATUS     | WARD         | ALLERGIES            ||
===================================================================================================
|| NHIS-0001  | AMINA BELLO        | RED      | ADMITTED   | EMERGENCY    | Penicillin, Latex    ||
===================================================================================================

Enter selection (1-11): 7
============================================================
                    WARD CENSUS SUMMARY
============================================================
📍 Total Admitted: 1
📍 Per-Ward Breakdown:
  • emergency         : 1 Patient(s)
📍 Occupied Wards (1): ['emergency']
🚨 Triage Risk Matrix:
  🔴 [RED] Critical   : 1
  🟡 [YELLOW] Urgent  : 0
  🟢 [GREEN] Routine  : 0
🕒 Report generated: 2026-07-18 08:13:09
============================================================

Enter selection (1-11): 9
Closing down... saving final state.
✅ Registry saved to .../src/data/registry.json
👋 System offline.
```

## 🎓 What I Learned

1. **Separation of concerns beats one big file.** Splitting the same logic
   across `config` / `models` / `file_manager` / `utils` / `patient_ops` /
   `main` made each file small enough to reason about on its own, and made
   `main.py` genuinely trivial — it's just wiring.
2. **`os.path.dirname(__file__)` beats hard-coded relative paths.** Once
   `config.py` builds its paths from its own location, the app runs the same
   no matter what directory you launch it from — no more `src/data` vs
   `data` guessing games.
3. **A "sensible-looking" default can hide a real bug.** `Patient` was
   storing `triage` as `"RED"` while `config.py`'s lookup tables used
   `"red"` — the mismatch didn't crash anything, it just silently broke
   sorting and the risk-matrix counts (`.get()` quietly fell back to a
   default). It only surfaced by actually running the CLI end-to-end, not
   just eyeballing the code — a good reminder to test integration paths,
   not just individual functions.
4. **`*args` and `**kwargs` earn their keep when reused.** `add_allergy(*args)`
   let `menu_add_allergies()` reuse the same dedup logic instead of
   re-implementing it, and `update_patient_fields(**kwargs)` turned two
   near-duplicate update flows into one generic function with validation.
5. **`try/except/finally` is about guarantees, not just error messages.**
   Putting the timestamp print in `census_summary()`'s `finally` block
   means the report always ends with a timestamp — even if something
   above it went wrong — which is exactly the kind of guarantee an audit
   trail needs.
6. **Backward-compatible storage matters.** Building a real `Patient`
   object during intake but storing `patient.to_dict()` let the app keep
   using simple dicts (and JSON) everywhere else, without a big rewrite of
   the persistence layer.
7. **Package imports vs. script imports are genuinely different things.**
   `src/__init__.py` only needs to exist for `test_models.py`'s
   `from src.models import ...` to work; `main.py` and friends use flat
   `from config import ...` imports because they're run as
   `python src/main.py` (script mode), not imported as a package. Mixing
   the two without understanding why one works and the other doesn't is a
   very easy way to get a confusing `ModuleNotFoundError`.
