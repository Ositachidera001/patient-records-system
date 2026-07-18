"""
config.py

centralised configuration for the patient Records system.
Every other module reads its file paths and reference data from here,
so there is exactly one place to change if a path or constant needs to move 
no more guessing whether "data/" means "src/data" or project-root/data
"""
import os

# os.path.dirname(__file__) gives the folder THIS file lives in (src/),
# no matter what directory the user launched python from.
# os.path.abspath()makes it a full, unambiguous path.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_DIR = os.path.join(BASE_DIR, "data")

registry_file = os.path.join(DATA_DIR, "registry.json")
audit_log_file = os.path.join(DATA_DIR, "audit_log.txt")

# console table width, used by patient_ops.py and utils.py
WIDTH = 60

# Triage colour -> human-readable meaning, shown to the user at intake
# and whenever triage is re-assessed.
TRIAGE_INFO = {
    "red":    "Immediate - Life threatening",
    "yellow": "Urgent - Within 1 hour",
    "green":  "Routine - Can wait."
}

# Triage colour rank -> sort priority.
# used by utils.patient_table() to sort RED patients to the top.
TRIAGE_RANK = {"red": 1, "yellow": 2, "green": 3}


# The only triage values the system will accept.
VALID_TRIAGE_COLOURS = ("red", "yellow", "green")
