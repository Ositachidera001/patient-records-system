import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
registry_file = os.path.join(BASE_DIR, "data", "registry.json")
audit_log_file = os.path.join(BASE_DIR, "data", "audit_log.txt")

WIDTH = 50

# Triage info
TRIAGE_INFO = {
    "red":    "Immediate - Life threatening",
    "yellow": "Urgent - Within 1 hour",
    "green":  "Routine - Can wait."
}

# Triage rank
rank = {"red": 1, "yellow": 2, "green": 3}
# sorted_patients = sorted(registry.items(),key=lambda x: rank.get(x[1]["triage"], 4)

# valid triage colour
VALID_TRIAGE_COLOURS = ("red", "yellow", "green")
# while True:
#     triage = input("Enter Triage Colour (RED/YELLOW/GREEN): ").strip().lower()
#     if triage in triage_info:
#         break
#     print("❌ Invalid triage. Use RED, YELLOW, or GREEN.")