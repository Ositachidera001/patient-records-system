"""
registry_analysis.py

Pandas-based analysis module for the patient system (Lesson 23A).

WHAT THIS FILE DOES
----------------------
Loads the CSV that Lesson 22's export_registry_to_csv() produces (see
file_manager.py) into a Pandas DataFrame, and runs the kind of daily
report a real hospital data department would want: shape/structure
checks, distribution counts, derived columns (triage severity score,
age group), filtered views, and summary statistics -- then saves the
enriched result back out to a new CSV.

WHY PANDAS INSTEAD OF PLAIN PYTHON LOOPS
--------------------------------------------
Everything in this file COULD be written with plain `for` loops over a
list of dicts (that's literally what the rest of this patient system
does). Pandas exists because, once you're doing REPEATED whole-column
operations -- "compute this for every row", "count how many rows have
each value", "group rows by ward and average something" -- a DataFrame
lets you express that in one line, and Pandas runs it as fast, compiled,
vectorised code under the hood instead of a slow Python-level loop.
That's the whole trade a data department is making: give up some of the
row-by-row control a raw loop gives you, in exchange for speed and much
shorter code for exactly this kind of "slice and summarise a table"
work.

HOW TO RUN THIS FILE
------------------------
python registry_analysis.py <path_to_csv>

If no path is given, it defaults to the most recently exported CSV in
data/exports/ (the same folder Lesson 22's menu_export_csv() writes to).
"""

import sys
from pathlib import Path

import pandas as pd


# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

DATA_DIR = Path(__file__).resolve().parent / "data"
EXPORTS_DIR = DATA_DIR / "exports"

# Maps each triage colour to a numeric severity score. Defined once as a
# constant (a plain dict) so it can be reused by .map() below without
# retyping the mapping, and so there's exactly ONE place to update if the
# hospital ever changes how severity is scored.
TRIAGE_SCORE_MAP = {"red": 3, "yellow": 2, "green": 1}


def find_latest_export(exports_dir=EXPORTS_DIR):
    """Find the most recently created CSV inside data/exports/, so this
    script can be run with no arguments and still find real data.

    Returns:
        Path | None: the newest CSV file's path, or None if the exports
        folder doesn't exist or contains no CSV files yet.
    """
    if not exports_dir.exists():
        return None

    csv_files = list(exports_dir.glob("*.csv"))
    if not csv_files:
        return None

    # max(..., key=...) with a file's modification time (st_mtime) picks
    # whichever file was written most recently -- exactly what "latest
    # export" means here.
    return max(csv_files, key=lambda p: p.stat().st_mtime)


def load_registry_csv(filepath):
    """Load a patient export CSV into a DataFrame using pd.read_csv().

    Args:
        filepath (str | Path): path to the CSV file to load.

    Returns:
        pd.DataFrame | None: the loaded table, or None if the file
        couldn't be read (missing file, empty file, malformed CSV).
        Returning None (rather than letting pandas' exception propagate)
        keeps this module consistent with the rest of the codebase's
        "fail safely, let the caller decide what to do" style.
    """
    try:
        # pd.read_csv() does what csv.DictReader does, but for an ENTIRE
        # table at once: it reads every row, infers a sensible data type
        # per COLUMN (not per cell) -- e.g. the whole "age" column
        # becomes integers, the whole "admission_status" column becomes
        # booleans -- and hands the result back as one DataFrame object
        # you can slice, filter, and summarise as a whole.
        df = pd.read_csv(filepath)
        return df
    except FileNotFoundError:
        print(f"⚠ Could not find CSV at {filepath}.")
        return None
    except pd.errors.EmptyDataError:
        print(f"⚠ CSV at {filepath} is empty — nothing to analyse.")
        return None
    except pd.errors.ParserError as e:
        print(f"⚠ CSV at {filepath} is malformed and couldn't be parsed: {e}")
        return None


def print_structure_report(df):
    """Print the required structural overview: shape, info(), describe(),
    and isnull().sum().
    """
    print("\n" + "=" * 60)
    print("STRUCTURE REPORT")
    print("=" * 60)

    # .shape is a TUPLE of (row_count, column_count) -- not a function
    # call, just an attribute, because it's cheap to know (Pandas
    # already tracks it) rather than something that needs computing.
    print(f"\nShape (rows, columns): {df.shape}")

    # .info() prints, for EVERY column: its name, how many non-null
    # values it has, and its inferred dtype (int64, object/string,
    # bool, etc). This is usually the FIRST thing you run on any new
    # DataFrame -- it tells you immediately whether a column pandas
    # thinks is "numbers" is actually numbers, or secretly text with
    # some numbers mixed in.
    print("\n--- df.info() ---")
    df.info()

    # .describe() computes summary statistics (count, mean, std, min,
    # 25/50/75th percentiles, max) for every NUMERIC column only, by
    # default. Non-numeric columns (name, ward, triage as plain text)
    # are silently skipped here -- that's expected, not a bug: you
    # can't compute a "mean" of the word "cardiology".
    print("\n--- df.describe() ---")
    print(df.describe())

    # .isnull() returns a same-shaped DataFrame of True/False (True =
    # that cell is missing). .sum() on a DataFrame of True/False adds
    # them up PER COLUMN (True counts as 1, False as 0), giving a quick
    # "how many missing values does each column have?" report -- useful
    # for spotting incomplete patient records at a glance.
    print("\n--- df.isnull().sum() ---")
    print(df.isnull().sum())


def print_distribution_reports(df):
    """Print the required triage and ward distribution counts."""
    print("\n" + "=" * 60)
    print("DISTRIBUTION REPORTS")
    print("=" * 60)

    # .value_counts() counts how many times each UNIQUE value appears in
    # a column, sorted from most to least common by default. This is the
    # fastest way to answer "how many of each triage colour do we have?"
    # without writing a manual counting loop.
    print("\n--- Triage distribution ---")
    print(df["triage"].value_counts())

    print("\n--- Ward distribution ---")
    print(df["ward"].value_counts())


def add_triage_score_column(df):
    """Add a `triage_score` column (red=3, yellow=2, green=1) using
    .map().

    .map() looks up EVERY value in a column against a dict (or a
    function) and returns a new column of the results, one output per
    input row -- it's the DataFrame equivalent of writing
    `[TRIAGE_SCORE_MAP[value] for value in df["triage"]]`, just built
    into pandas and run as fast, vectorised code.

    Any triage value NOT found in TRIAGE_SCORE_MAP (e.g. a typo, or a
    genuinely new/unexpected triage colour) becomes NaN (pandas' "missing
    value" marker) rather than crashing the whole column — which is
    exactly the isnull().sum() check above would catch if it ever
    happened.
    """
    df["triage_score"] = df["triage"].map(TRIAGE_SCORE_MAP)
    return df


def _classify_age_group(age):
    """Classify a single age into 'Paediatric' (<18), 'Adult' (18-59),
    or 'Elderly' (60+).

    This is a plain Python function that operates on ONE value at a
    time -- it has no idea it's being used on a DataFrame column at
    all. That's deliberate: .apply() (see add_age_group_column below)
    is the pandas tool that takes a plain function like this and runs
    it once per row, which is exactly the situation where a simple
    if/elif chain (rather than a vectorised dict lookup like .map())
    is the clearer, more natural way to express the logic.
    """
    if age < 18:
        return "Paediatric"
    elif age < 60:
        return "Adult"
    else:
        return "Elderly"


def add_age_group_column(df):
    """Add an `age_group` column (Paediatric <18, Adult 18-59, Elderly
    60+) using .apply().

    .apply() runs a function ONCE FOR EACH VALUE in df["age"] and
    collects the results into a new column. It's more flexible than
    .map() (it can express any logic a plain function can, not just a
    fixed lookup table) but generally slower on large DataFrames, since
    it's closer to a regular Python loop under the hood rather than a
    fully vectorised pandas operation. For age-bracket logic like this
    -- a small if/elif chain, not a fixed dict -- .apply() is the right
    tool; .map() only accepts a dict or a 1-argument lookup, not
    multi-branch logic like "less than 18 vs less than 60".
    """
    df["age_group"] = df["age"].apply(_classify_age_group)
    return df


def print_filtered_views(df):
    """Print the three required filtered views: RED triage only,
    ADMITTED only, and patients over 40.

    Each filter uses BOOLEAN INDEXING: `df["column"] == value` produces
    a column of True/False (one per row), and `df[that_boolean_column]`
    keeps only the rows where it's True. This is the single most common
    pattern in pandas for "give me a subset of rows matching a
    condition" -- no manual for-loop with an if-check needed.
    """
    print("\n" + "=" * 60)
    print("FILTERED VIEWS")
    print("=" * 60)

    print("\n--- RED triage patients ---")
    red_patients = df[df["triage"] == "red"]
    print(red_patients)

    print("\n--- Admitted patients ---")
    # admission_status was read from the CSV as the literal text "True"/
    # "False" -- pandas' CSV reader is usually smart enough to infer this
    # column as a real boolean dtype automatically, but we compare
    # against the Python boolean True either way, which works correctly
    # once the column IS boolean (confirmed by the df.info() dtype check
    # above -- if it ever shows up as "object" instead of "bool", that's
    # a sign the source CSV had inconsistent True/False spelling).
    admitted_patients = df[df["admission_status"] == True]  # noqa: E712
    print(admitted_patients)

    print("\n--- Patients over 40 ---")
    over_40 = df[df["age"] > 40]
    print(over_40)


def print_summary_statistics(df):
    """Print the required summary statistics: average age, max age, min
    age, and total admitted count.
    """
    print("\n" + "=" * 60)
    print("SUMMARY STATISTICS")
    print("=" * 60)

    # .mean(), .max(), .min() on a single column (a "Series" in pandas
    # terminology) compute that statistic across every value in the
    # column in one call.
    print(f"Average age      : {df['age'].mean():.1f}")
    print(f"Max age            : {df['age'].max()}")
    print(f"Min age            : {df['age'].min()}")

    # .sum() on a boolean Series adds up how many True values there are
    # (True counts as 1, False as 0) -- so this counts admitted patients
    # without needing a separate .value_counts() call.
    print(f"Total admitted count : {(df['admission_status'] == True).sum()}")  # noqa: E712


def add_ward_severity_report(df):
    """BONUS: use df.groupby("ward")["triage_score"].mean() to find
    which ward has the highest average triage severity.

    .groupby("ward") splits the DataFrame into one mini-table PER unique
    ward value. ["triage_score"].mean() then computes the average
    triage_score WITHIN each of those mini-tables, and pandas
    automatically stitches the per-group results back into one tidy
    Series, indexed by ward name. This is the pandas equivalent of
    "for each ward, look at only that ward's rows, and average their
    triage_score" -- but expressed in one line instead of a manual loop
    with a running total per ward.
    """
    print("\n" + "=" * 60)
    print("BONUS: WARD SEVERITY REPORT")
    print("=" * 60)

    ward_severity = df.groupby("ward")["triage_score"].mean().sort_values(ascending=False)
    print("\nAverage triage severity by ward (highest first):")
    print(ward_severity)

    highest_severity_ward = ward_severity.index[0]
    print(f"\n🚨 Highest average triage severity: '{highest_severity_ward}' "
          f"ward (avg score {ward_severity.iloc[0]:.2f})")


def add_data_quality_column(df):
    """BONUS: flag any row where age < 0 or age > 130 as "Invalid" in a
    new `data_quality` column (and "Valid" otherwise).

    np.where-style logic without numpy: we build the boolean condition
    first (is_invalid_age), then use pandas' own .where() ... actually,
    the simplest, most readable way to express a two-outcome column like
    this is a direct conditional assignment via .apply() on a boolean
    mask -- shown below using a compact helper so the intent ("Invalid"
    vs "Valid") reads clearly at the call site.
    """
    def _classify_quality(age):
        if age < 0 or age > 130:
            return "Invalid"
        return "Valid"

    df["data_quality"] = df["age"].apply(_classify_quality)

    invalid_count = (df["data_quality"] == "Invalid").sum()
    if invalid_count:
        print(f"\n⚠ Data quality check: {invalid_count} row(s) flagged "
              f"as Invalid (age < 0 or age > 130):")
        print(df[df["data_quality"] == "Invalid"][["nhis_number", "name", "age"]])
    else:
        print("\n✅ Data quality check: no invalid ages found.")

    return df


def save_enriched_csv(df, source_filepath):
    """Save the enriched DataFrame (with triage_score, age_group, and
    data_quality columns added) to a new CSV file, alongside the
    original export.

    Returns:
        Path | None: the path written, or None if saving failed.
    """
    source_filepath = Path(source_filepath)
    output_path = source_filepath.parent / f"{source_filepath.stem}_enriched.csv"

    try:
        # index=False: by default, df.to_csv() writes pandas' own
        # internal row-number index as an extra unlabeled first column
        # (0, 1, 2, ...). We don't want that in the saved file -- it's
        # not real patient data, just pandas' internal bookkeeping --
        # so index=False tells it to write ONLY the real columns.
        df.to_csv(output_path, index=False)
        return output_path
    except OSError as e:
        print(f"⚠ Could not save enriched CSV: {e}")
        return None


# ---------------------------------------------------------------------------
# STANDALONE ENTRY POINT
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Accept an optional CSV path as a command-line argument; otherwise
    # fall back to the newest file in data/exports/.
    if len(sys.argv) > 1:
        csv_path = Path(sys.argv[1])
    else:
        csv_path = find_latest_export()
        if csv_path is None:
            print("⚠ No CSV path given and no exports found in "
                  f"{EXPORTS_DIR}. Run the patient system's CSV export "
                  "(menu option 15) first, or pass a path directly:\n"
                  "    python registry_analysis.py path/to/file.csv")
            sys.exit(1)

    print(f"Loading {csv_path} ...")
    df = load_registry_csv(csv_path)

    if df is None:
        sys.exit(1)

    print_structure_report(df)
    print_distribution_reports(df)

    df = add_triage_score_column(df)
    df = add_age_group_column(df)

    print_filtered_views(df)
    print_summary_statistics(df)

    add_ward_severity_report(df)
    df = add_data_quality_column(df)

    saved_path = save_enriched_csv(df, csv_path)
    if saved_path:
        print(f"\n✅ Enriched DataFrame saved to {saved_path}")
