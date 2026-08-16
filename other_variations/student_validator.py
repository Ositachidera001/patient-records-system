"""
student_validator.py

EdTech variation of Lesson 19's regex validator (Task 19B).

This is a STANDALONE script -- it does not import anything from the
patient system (src/). It reuses the same regex CONCEPTS (re.compile,
anchors, character classes, re.sub, re.findall) but applied to a
completely different domain: student records instead of patient records.
That's deliberate -- the point of a "variation exercise" is to prove you
understand the underlying pattern-matching principles, not that you can
copy-paste the healthcare version.
"""

import re


# ---------------------------------------------------------------------------
# COMPILED PATTERNS (built once, at import time -- see validators.py for the
# full explanation of why re.compile() beats calling re.search() directly)
# ---------------------------------------------------------------------------

# --- Student ID: STU- + 4-digit year + - + 4-digit sequence number -------
# ^STU-           literal prefix, anchored to the very start of the string
# \d{4}           exactly 4 digits (the year, e.g. 2026)
# -               a literal hyphen separating year from sequence number
# \d{4}$          exactly 4 digits (the sequence number), anchored to the
#                 very end of the string
# Example match: STU-2026-0001
STUDENT_ID_PATTERN = re.compile(r"^STU-\d{4}-\d{4}$")

# Same shape, WITHOUT anchors, for finding IDs embedded inside prose.
STUDENT_ID_FINDALL_PATTERN = re.compile(r"STU-\d{4}-\d{4}")

# --- Student email: same practical shape as the patient system's email ---
EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")

# --- Pattern used to MASK an email rather than just validate it ----------
# We capture the local part (before @) in a group so we can keep just its
# first character, and capture the domain (after @) in a second group so
# we can keep it fully readable. Everything else in the local part gets
# replaced with asterisks.
#   Group 1: ([A-Za-z0-9._%+-])   -- ONE character: the first char to keep
#   Group 2: [A-Za-z0-9._%+-]*    -- the rest of the local part (not
#                                     captured -- we intentionally throw
#                                     it away and replace it with ***)
#   Group 3: (@[A-Za-z0-9.-]+\.[A-Za-z]{2,})  -- the whole @domain.tld,
#                                                 kept exactly as-is
EMAIL_MASK_PATTERN = re.compile(
    r"^([A-Za-z0-9._%+-])[A-Za-z0-9._%+-]*(@[A-Za-z0-9.-]+\.[A-Za-z]{2,})$"
)


# ---------------------------------------------------------------------------
# VALIDATOR / UTILITY FUNCTIONS
# ---------------------------------------------------------------------------

def validate_student_id(student_id_str):
    """Return True if student_id_str matches STU-YYYY-NNNN exactly."""
    return bool(STUDENT_ID_PATTERN.match(student_id_str))


def validate_student_email(email_str):
    """Return True if email_str has a practical, well-formed email shape."""
    return bool(EMAIL_PATTERN.match(email_str))


def mask_student_email(email_str):
    """Mask an email for safe display/logging, e.g. data-protection rules.

    'jane.doe@school.edu.ng' -> 'j*******@school.edu.ng'

    Uses re.sub() with a REPLACEMENT FUNCTION (not a plain string) via
    a lambda, so we can build the masked text dynamically from what was
    captured, rather than always substituting the exact same fixed text.

    If the email doesn't match our expected shape at all, we return it
    unchanged rather than guessing -- masking something we can't
    confidently parse risks hiding a data-quality problem instead of
    surfacing it.
    """
    match = EMAIL_MASK_PATTERN.match(email_str)
    if not match:
        return email_str  # not a recognisable email shape -- leave as-is

    first_char = match.group(1)   # the single character we keep visible
    domain_part = match.group(2)  # the "@domain.tld" we keep visible

    # We don't know the exact length of the hidden portion from the groups
    # alone (group 2 in the pattern above wasn't captured), so we derive
    # it directly: everything between the kept first character and the
    # kept domain is what we mask, character-for-character.
    local_part = email_str.split("@")[0]
    hidden_length = len(local_part) - 1  # minus the one character we kept
    masked = first_char + ("*" * hidden_length) + domain_part
    return masked


def extract_student_ids(text):
    """Return a list of every STU-YYYY-NNNN code found inside a block of
    text, using re.findall() to collect ALL matches, not just the first.
    """
    return STUDENT_ID_FINDALL_PATTERN.findall(text)


# ---------------------------------------------------------------------------
# STANDALONE DEMO
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=== student_validator.py self-test demo ===\n")

    print("-- validate_student_id --")
    print(f"  'STU-2026-0001' (valid)   -> {validate_student_id('STU-2026-0001')}")
    print(f"  'STU-26-1'      (invalid) -> {validate_student_id('STU-26-1')}")

    print("\n-- validate_student_email --")
    print(f"  'jane.doe@school.edu.ng' (valid)   -> "
          f"{validate_student_email('jane.doe@school.edu.ng')}")
    print(f"  'jane.doe@@school'       (invalid) -> "
          f"{validate_student_email('jane.doe@@school')}")

    print("\n-- mask_student_email (data protection) --")
    print(f"  'jane.doe@school.edu.ng' -> "
          f"{mask_student_email('jane.doe@school.edu.ng')!r}")
    print(f"  'sam@uni.edu'            -> "
          f"{mask_student_email('sam@uni.edu')!r}")

    print("\n-- extract_student_ids (re.findall over prose) --")
    sample_text = (
        "Attendance was recorded for STU-2026-0001 and STU-2026-0002. "
        "STU-2025-0999 was marked as a transfer student."
    )
    print(f"  text: {sample_text!r}")
    print(f"  found -> {extract_student_ids(sample_text)}")
