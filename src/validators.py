"""
validators.py

A dedicated validation layer for the patient system (Lesson 19A).

WHY THIS FILE EXISTS ON ITS OWN:
Validation logic doesn't belong scattered across patient_ops.py, mixed in
with menu prompts and registry updates. Keeping it here means:
  1. Every place that needs to check an NHIS number, phone, email, or date
     uses the EXACT same rule -- no risk of two functions disagreeing on
     what "valid" means.
  2. We can unit-test this file completely on its own, with no registry,
     no menu, no user input required.
  3. re.compile() patterns are built ONCE at import time (see below),
     not re-built every single time a function is called.

CONCEPT: re.compile() vs calling re.match()/re.search() directly
------------------------------------------------------------------
re.search(pattern, text) secretly compiles `pattern` into a regex object
EVERY time you call it. Python does cache the last few patterns it compiles
internally, but that cache is small and not guaranteed. If you call the
same pattern hundreds of times (e.g. validating every patient on load),
that's wasted work.

re.compile(pattern) builds the regex object ONCE, up front, and hands you
back a reusable object with its own .match()/.search()/.findall() methods.
That's why every pattern below is compiled at module level (outside any
function) -- it happens exactly once, the moment this file is imported.
"""

import re


# ---------------------------------------------------------------------------
# COMPILED PATTERNS
# All defined at module level (not inside a function) so they are compiled
# exactly once, when this module is first imported, and reused forever after.
# ---------------------------------------------------------------------------

# --- NHIS number: literal "NHIS-" followed by EXACTLY 4 digits -----------
# ^        start of string (nothing allowed before "NHIS-")
# NHIS-    the literal text, matched exactly as written
# \d{4}    exactly 4 digit characters (0-9), no more, no fewer
# $        end of string (nothing allowed after the 4th digit)
# Anchoring with ^ and $ matters: without them, "XNHIS-00001Y" would also
# match, because re.match/search only need to find the pattern SOMEWHERE
# inside the text, not describe the WHOLE text.
NHIS_PATTERN = re.compile(r"^NHIS-\d{4}$")

# --- Nigerian mobile phone numbers ----------------------------------------
# We need to accept several real-world shapes:
#   080XXXXXXXX   / 090XXXXXXXX  / 070XXXXXXXX   (11 digits, local format)
#   +2348XXXXXXXXX                               (13 digits after +234)
#   2348XXXXXXXXX                                (13 digits, no +)
#
# ^(?:...)$                 anchor the WHOLE string, non-capturing group
#                            groups our two alternatives together without
#                            creating a numbered capture group we don't need
# 0[789]\d{9}                "0" + one of 7/8/9 + 9 more digits = 11 digits
#                            total, covering 070/080/090 numbers
# \+?234[789]\d{9}            optional "+", then "234", then 7/8/9, then
#                            9 more digits (same 10 significant digits as
#                            the local format, just with 234 swapped in
#                            for the leading 0) = handles both "+2348..."
#                            and "2348..." with ONE pattern (the ? makes
#                            the + optional rather than writing two
#                            separate patterns)
PHONE_PATTERN = re.compile(r"^(?:0[789]\d{9}|\+?234[789]\d{9})$")

# --- Email address: a practical (not RFC-perfect) check -------------------
# There is no single regex that perfectly validates every legal email
# address per the official spec -- the spec is famously enormous. In real
# systems (including this one) you validate a REASONABLE shape here and
# confirm the address really works by sending a verification email. That's
# the industry-standard "practical" approach the task asks for.
#
# ^[A-Za-z0-9._%+-]+   one or more characters allowed in the local part
#                      (before the @): letters, digits, dot, underscore,
#                      percent, plus, hyphen
# @                    the literal @ symbol, exactly once
# [A-Za-z0-9.-]+       the domain name part (e.g. "hospital-systems")
# \.                   a literal dot (escaped! a bare "." in regex means
#                      "any character", so \. means an ACTUAL period)
# [A-Za-z]{2,}$        the extension (.com, .org, .ng...) -- at least 2
#                      letters, anchored to the end of the string
EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")

# --- Date: strict YYYY-MM-DD shape (not calendar-aware) --------------------
# This pattern checks the SHAPE only (4 digits - 2 digits - 2 digits with
# sane digit ranges for month/day). It intentionally does NOT catch things
# like "2026-02-30" (30th of February doesn't exist) -- that's a calendar
# question, not a text-shape question, and belongs to datetime.strptime(),
# not to a regex. Regex answers "does this look like a date?", not "is
# this a real date?". We keep those two concerns separate on purpose.
#
# ^\d{4}-              exactly 4 digits, then a literal hyphen (year)
# (0[1-9]|1[0-2])-     month: 01-09 OR 10-12, then a literal hyphen
# (0[1-9]|[12]\d|3[01])$   day: 01-09, OR 10-29, OR 30-31
DATE_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$")

# --- Finding NHIS codes anywhere inside a larger block of text ------------
# Same shape as NHIS_PATTERN but WITHOUT the ^ and $ anchors, because here
# we WANT to find matches in the middle of a sentence, not demand that the
# entire string be nothing but the code.
NHIS_FINDALL_PATTERN = re.compile(r"NHIS-\d{4}")

# --- Bonus: characters allowed in a sanitised patient name -----------------
# This is a "negated character class": [^...] means "match anything that
# is NOT inside these brackets". So this pattern matches any character
# that is NOT a letter (upper/lower), NOT a space, and NOT a hyphen --
# i.e. exactly the characters we want to strip out (digits, punctuation,
# symbols, etc.).
NAME_STRIP_PATTERN = re.compile(r"[^A-Za-z \-]")


# ---------------------------------------------------------------------------
# VALIDATOR FUNCTIONS
# Each one takes a raw string and returns True/False. They deliberately do
# NOT print anything or raise exceptions -- that keeps them reusable in any
# context (menu prompts, unit tests, batch data-cleaning scripts) without
# forcing a particular UI behaviour on the caller. The CALLER decides what
# to do with a False result.
# ---------------------------------------------------------------------------

def validate_nhis(nhis_str):
    """Return True if nhis_str is exactly 'NHIS-' followed by 4 digits."""
    # bool(match_object_or_None) -> True if a match object was found,
    # False if .match() returned None. re.Match objects are always
    # "truthy" and None is always "falsy", so wrapping in bool() gives us
    # a clean True/False instead of leaking a Match object (or None) out
    # to the caller.
    return bool(NHIS_PATTERN.match(nhis_str))


def validate_phone(phone_str):
    """Return True if phone_str is a recognised Nigerian mobile format."""
    return bool(PHONE_PATTERN.match(phone_str))


def validate_email(email_str):
    """Return True if email_str has a practical, well-formed email shape."""
    return bool(EMAIL_PATTERN.match(email_str))


def validate_date(date_str):
    """Return True if date_str is strictly in YYYY-MM-DD shape."""
    return bool(DATE_PATTERN.match(date_str))


def extract_nhis_codes(text):
    """Return a list of every NHIS-XXXX code found anywhere inside text.

    Uses .findall() instead of .match()/.search() because we don't want
    just the FIRST match (search) or a match anchored at the START
    (match) -- we want ALL occurrences, wherever they appear.
    """
    return NHIS_FINDALL_PATTERN.findall(text)


def sanitise_patient_name(name):
    """BONUS: strip anything that isn't a letter/space/hyphen, then
    Title Case the result.

    re.sub(pattern, replacement, text) scans `text` for every match of
    `pattern` and swaps each one out for `replacement`. Here we replace
    every disallowed character with an empty string "" -- which is just
    a fancy way of deleting it.

    Example: "J0hn_Do3 99!"  ->  strip disallowed chars -> "John Do "
                              ->  .title()                -> "John Do "
    """
    cleaned = NAME_STRIP_PATTERN.sub("", name)
    # .title() capitalises the first letter of every word: "john doe"
    # becomes "John Doe". We do this AFTER stripping, not before, so
    # leftover junk characters can't interfere with word boundaries.
    return cleaned.title()


# ---------------------------------------------------------------------------
# STANDALONE DEMO
# Runs ONLY when this file is executed directly (python validators.py),
# never when it's imported by patient_ops.py or anything else. This is the
# standard Python idiom for "only run this block if I am the main script".
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=== validators.py self-test demo ===\n")

    # Each test prints what we're checking, the input, and the result, so
    # you can visually confirm every validator behaves as expected without
    # needing a separate test framework.

    print("-- validate_nhis --")
    print(f"  'NHIS-0001'  (valid)   -> {validate_nhis('NHIS-0001')}")
    print(f"  'NHIS-12'    (invalid) -> {validate_nhis('NHIS-12')}")

    print("\n-- validate_phone --")
    print(f"  '08031234567' (valid)   -> {validate_phone('08031234567')}")
    print(f"  '+2348031234567' (valid)-> {validate_phone('+2348031234567')}")
    print(f"  '12345'       (invalid) -> {validate_phone('12345')}")

    print("\n-- validate_email --")
    print(f"  'nurse@hospital.ng' (valid)   -> {validate_email('nurse@hospital.ng')}")
    print(f"  'not-an-email'      (invalid) -> {validate_email('not-an-email')}")

    print("\n-- validate_date --")
    print(f"  '2026-08-16' (valid)   -> {validate_date('2026-08-16')}")
    print(f"  '16-08-2026' (invalid) -> {validate_date('16-08-2026')}")

    print("\n-- extract_nhis_codes --")
    sample_text = ("Patients NHIS-0001 and NHIS-0002 were transferred; "
                   "NHIS-0003 was discharged.")
    print(f"  text: {sample_text!r}")
    print(f"  found -> {extract_nhis_codes(sample_text)}")

    print("\n-- sanitise_patient_name (BONUS) --")
    print(f"  'Amaka Eze#2026'   -> {sanitise_patient_name('Amaka Eze#2026')!r}")
    print(f"  'mary-anne'        -> {sanitise_patient_name('mary-anne')!r}")
    # Note: digits/symbols are DELETED wherever they sit, even mid-word --
    # e.g. 'j0hn' becomes 'jhn', not 'john'. Sanitising strips junk
    # characters; it does not try to "guess" the word you meant.
    print(f"  'j0hn_doe99!'      -> {sanitise_patient_name('j0hn_doe99!')!r}  "
          "(digits inside a word are just deleted, not guessed)")
