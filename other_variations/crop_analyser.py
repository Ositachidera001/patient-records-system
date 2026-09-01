# lesson 23
# Developer: Nwonye Ezekiel
# Date: 1st September, 2026. 
"""
crop_analyser.py

AgriTech variation of Lesson 23's Pandas exercise (Task 23B).

Standalone script -- no imports from src/. Builds a small Pandas
DataFrame FROM SCRATCH (no CSV involved this time -- the data is
defined directly in Python) representing Nigerian crop yields across
different states and growing seasons, then runs the same kind of
"derive a column, count distributions, filter, and group-summarise"
workflow as registry_analysis.py, applied to a completely different
domain.
"""

import pandas as pd


def build_crop_dataframe():
    """Build a DataFrame of Nigerian crop yield records from scratch.

    Returns:
        pd.DataFrame: with columns crop, state, yield_kg, area_ha,
        season -- at least 8 rows as required by the task.
    """
    # A DataFrame can be built directly from a dict of equal-length
    # lists: each KEY becomes a column name, each LIST becomes that
    # column's values, matched up by position (index 0 across every
    # list becomes row 0, and so on). This is the most direct way to
    # hand-write a small DataFrame without going through a CSV file or
    # a list of row-dicts first.
    data = {
        "crop": [
            "Maize", "Maize", "Rice", "Rice", "Cassava",
            "Cassava", "Sorghum", "Yam", "Yam", "Millet",
        ],
        "state": [
            "Kaduna", "Benue", "Kano", "Ebonyi", "Oyo",
            "Enugu", "Kano", "Benue", "Delta", "Sokoto",
        ],
        # Total harvest weight in kilograms for that specific plot.
        "yield_kg": [
            8200, 9100, 12500, 11800, 15600,
            14200, 6700, 9800, 8900, 5400,
        ],
        # Land area farmed, in hectares.
        "area_ha": [
            2.0, 2.5, 3.0, 2.8, 1.8,
            1.6, 2.2, 2.1, 1.9, 1.7,
        ],
        "season": [
            "wet", "wet", "wet", "dry", "wet",
            "dry", "dry", "wet", "wet", "dry",
        ],
    }

    df = pd.DataFrame(data)
    return df


def add_yield_per_ha_column(df):
    """Add a `yield_per_ha` column, computed as yield_kg / area_ha.

    Dividing one whole COLUMN by another whole column is a single
    vectorised operation in pandas -- df["yield_kg"] / df["area_ha"]
    divides row 0 by row 0, row 1 by row 1, and so on, all at once,
    without writing a loop or a zip() over the two columns manually.
    """
    df["yield_per_ha"] = (df["yield_kg"] / df["area_ha"]).round(2)
    return df


def print_value_counts(df):
    """Print value_counts() on the crop and season columns, as required."""
    print("\n--- Crop value counts ---")
    print(df["crop"].value_counts())

    print("\n--- Season value counts ---")
    print(df["season"].value_counts())


def print_wet_season_high_yield(df):
    """Filter to wet-season crops with yield_kg > 5000, shown via .loc[].

    .loc[] is pandas' LABEL-based selector: you give it a row condition
    (and optionally a column list) and it returns exactly those rows
    (and columns). Here we pass a BOOLEAN CONDITION built from two
    combined checks:
      (df["season"] == "wet") & (df["yield_kg"] > 5000)
    The `&` is the element-wise AND for two boolean Series (Python's
    plain `and` keyword does NOT work here -- it only works on single
    True/False values, not on a whole column of them at once, which is
    why pandas requires `&` for this and `|` for OR).
    """
    print("\n--- Wet season crops with yield_kg > 5,000 ---")
    condition = (df["season"] == "wet") & (df["yield_kg"] > 5000)
    wet_high_yield = df.loc[condition]
    print(wet_high_yield)


def print_average_yield_per_crop(df):
    """Print average yield_per_ha per crop using .groupby()."""
    print("\n--- Average yield_per_ha by crop ---")
    # .groupby("crop") splits the DataFrame into one mini-table per
    # unique crop name (Maize's rows together, Rice's rows together,
    # etc.). ["yield_per_ha"].mean() then averages just that one column
    # WITHIN each group, and pandas stitches the results back into one
    # Series indexed by crop name.
    avg_by_crop = df.groupby("crop")["yield_per_ha"].mean().sort_values(ascending=False)
    print(avg_by_crop.map("{:.2f}".format))


if __name__ == "__main__":
    print("=== Nigerian Crop Yield Analyser ===")

    df = build_crop_dataframe()
    print(f"\nBuilt DataFrame with {df.shape[0]} rows and {df.shape[1]} columns.")
    print(df)

    df = add_yield_per_ha_column(df)
    print("\n--- With yield_per_ha added ---")
    print(df)

    print_value_counts(df)
    print_wet_season_high_yield(df)
    print_average_yield_per_crop(df)
