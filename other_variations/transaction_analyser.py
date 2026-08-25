"""
transaction_analyser.py

Fintech variation of Lesson 22's CSV exercise (Task 22B).

Standalone script -- no imports from src/. Generates a dummy CSV of bank
transactions, reads it back with csv.DictReader, computes summary
statistics, and writes those stats out to a second CSV using
csv.DictWriter. Every currency amount is displayed in the mandatory
"₦{:,.2f}" format (Naira symbol, thousands separator, 2 decimal places).
"""

import csv
from datetime import datetime, timedelta
from pathlib import Path


# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

OUTPUT_DIR = Path(__file__).resolve().parent
TRANSACTIONS_CSV = OUTPUT_DIR / "transactions.csv"
SUMMARY_CSV = OUTPUT_DIR / "transaction_summary.csv"

# The columns every transaction row uses, in this exact order. Defined
# once as a constant so the CSV WRITER and the CSV READER (via
# DictReader, which reads whatever header row is actually in the file)
# both agree on the same field names without us having to retype them.
TRANSACTION_FIELDNAMES = ["date", "description", "amount", "type"]


def generate_dummy_transactions():
    """Build a list of at least 10 realistic dummy bank transactions.

    Returns:
        list[dict]: each shaped as
            {"date": str, "description": str, "amount": str, "type": str}
        `amount` is kept as a STRING here on purpose -- this mirrors what
        a real CSV file actually contains (CSV has no concept of a
        "number" type; every cell is text until something parses it).
        We convert to float only later, when READING the file back in
        analyse_transactions() -- exactly the conversion step a real
        CSV-processing script has to do.
    """
    # A fixed start date keeps every run of this script reproducible --
    # useful for a lesson demo, where you want the same output every time
    # you run it, not a different one depending on today's date.
    start_date = datetime(2026, 8, 1)

    # Each tuple is (days_after_start, description, amount, type).
    # "type" is either "credit" (money coming IN) or "debit" (money going
    # OUT) -- the two categories every bank statement uses.
    raw_transactions = [
        (0, "Salary payment - August", 450000.00, "credit"),
        (1, "Rent payment", 120000.00, "debit"),
        (2, "Grocery shopping - Shoprite", 18500.50, "debit"),
        (3, "Electricity bill (PHCN)", 9200.00, "debit"),
        (4, "Transfer from Chidi", 25000.00, "credit"),
        (5, "Fuel station - NNPC", 15000.00, "debit"),
        (6, "Freelance payment - logo design", 60000.00, "credit"),
        (7, "Internet subscription", 18000.00, "debit"),
        (8, "Restaurant - Yellow Chilli", 12300.75, "debit"),
        (9, "Refund - returned item", 7500.00, "credit"),
        (10, "Data subscription", 3500.00, "debit"),
        (11, "Withdrawal - ATM", 50000.00, "debit"),
    ]

    transactions = []
    for days_offset, description, amount, txn_type in raw_transactions:
        txn_date = start_date + timedelta(days=days_offset)
        transactions.append({
            "date": txn_date.strftime("%Y-%m-%d"),
            "description": description,
            # str(amount) here matches how a real bank export would give
            # you a plain-text number in a CSV cell, e.g. "450000.0".
            "amount": str(amount),
            "type": txn_type,
        })

    return transactions


def write_transactions_csv(transactions, filepath=TRANSACTIONS_CSV):
    """Write the transaction list out to a CSV file using csv.DictWriter.

    Returns:
        Path | None: the path written, or None if writing failed.
    """
    try:
        # newline="" and encoding="utf-8": same reasoning as
        # file_manager.py's CSV functions -- newline="" stops the csv
        # module's own line-ending handling from colliding with Python's
        # text-mode newline translation (which would otherwise double up
        # line endings on Windows), and encoding="utf-8" guarantees the
        # file reads correctly regardless of the OS's default encoding.
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=TRANSACTION_FIELDNAMES)
            writer.writeheader()
            writer.writerows(transactions)
        return filepath
    except OSError as e:
        print(f"⚠ Could not write transactions CSV: {e}")
        return None


def analyse_transactions(filepath=TRANSACTIONS_CSV):
    """Read the transactions CSV with csv.DictReader and compute summary
    statistics.

    Returns:
        dict | None: {
            "total_credits": float,
            "total_debits": float,
            "net_balance": float,
            "largest_debit": dict | None,   # the full transaction row
            "transaction_count": int,
        }
        Returns None (never raises) if the file can't be read.
    """
    total_credits = 0.0
    total_debits = 0.0
    largest_debit = None  # will hold the whole row dict, not just the amount
    transaction_count = 0

    try:
        with open(filepath, "r", newline="", encoding="utf-8") as f:
            # DictReader turns each row into a dict keyed by the header
            # row's column names -- e.g. {"date": "2026-08-01",
            # "description": "Salary payment - August",
            # "amount": "450000.0", "type": "credit"}.
            reader = csv.DictReader(f)

            for row in reader:
                transaction_count += 1

                # Every value read from a CSV file is a STRING, even
                # though "450000.0" LOOKS like a number -- float() is
                # what actually converts it into something we can do
                # arithmetic on.
                amount = float(row["amount"])
                txn_type = row["type"].strip().lower()

                if txn_type == "credit":
                    total_credits += amount
                elif txn_type == "debit":
                    total_debits += amount
                    # Track the single largest debit seen so far. We
                    # compare against the CURRENT largest_debit's amount
                    # each time, updating whenever we find a bigger one.
                    if largest_debit is None or amount > float(largest_debit["amount"]):
                        largest_debit = row

    except FileNotFoundError:
        print(f"⚠ Transactions file not found at {filepath}.")
        return None
    except OSError as e:
        print(f"⚠ Could not read transactions file: {e}")
        return None
    except (KeyError, ValueError) as e:
        # KeyError: a row is missing an expected column (e.g. "amount").
        # ValueError: float() failed because a cell wasn't a valid number.
        # Either way, this means the CSV's DATA is malformed, not that
        # the file itself is unreadable -- worth a distinct message.
        print(f"⚠ Transactions file contains malformed data: {e}")
        return None

    return {
        "total_credits": total_credits,
        "total_debits": total_debits,
        # Net balance: money IN minus money OUT. Positive means the
        # account grew over this period; negative means it shrank.
        "net_balance": total_credits - total_debits,
        "largest_debit": largest_debit,
        "transaction_count": transaction_count,
    }


def naira(amount):
    """Format a number as Nigerian Naira: '₦{:,.2f}'.

    The MANDATORY format from the task spec:
      - ₦        the Naira currency symbol, always first
      - {:,.2f}  comma as the THOUSANDS separator, always exactly
                 2 decimal places

    Example: naira(450000.0) -> '₦450,000.00'
    """
    return f"₦{amount:,.2f}"


def print_summary(stats):
    """Print the required summary: total credits, total debits, net
    balance, and the largest single debit -- all currency values in the
    mandatory ₦{:,.2f} format.
    """
    if stats is None:
        print("No statistics to show (analysis failed — see warning above).")
        return

    print("\n" + "=" * 55)
    print("BANK TRANSACTION SUMMARY")
    print("=" * 55)
    print(f"Transactions analysed : {stats['transaction_count']}")
    print(f"Total credits          : {naira(stats['total_credits'])}")
    print(f"Total debits            : {naira(stats['total_debits'])}")
    print(f"Net balance              : {naira(stats['net_balance'])}")

    if stats["largest_debit"]:
        d = stats["largest_debit"]
        print(f"Largest single debit      : {naira(float(d['amount']))} "
              f"— {d['description']} ({d['date']})")
    else:
        print("Largest single debit      : none recorded")
    print("=" * 55)


def write_summary_csv(stats, filepath=SUMMARY_CSV):
    """Write the summary statistics out to their own CSV file using
    csv.DictWriter -- a second, small CSV alongside the raw transactions
    CSV, suitable for dropping straight into a spreadsheet or a monthly
    report.

    Returns:
        Path | None: the path written, or None if writing failed.
    """
    if stats is None:
        print("⚠ No statistics to save — analysis must succeed first.")
        return None

    summary_fieldnames = [
        "metric", "value_naira",
    ]

    # One row per statistic. Kept as a LIST OF DICTS (rather than one
    # wide row) so the summary CSV opens as a clean, readable two-column
    # table in Excel -- one metric per line -- instead of one very wide
    # row that's awkward to read.
    rows = [
        {"metric": "Total Credits", "value_naira": naira(stats["total_credits"])},
        {"metric": "Total Debits", "value_naira": naira(stats["total_debits"])},
        {"metric": "Net Balance", "value_naira": naira(stats["net_balance"])},
        {
            "metric": "Largest Single Debit",
            "value_naira": (
                naira(float(stats["largest_debit"]["amount"]))
                if stats["largest_debit"] else naira(0.0)
            ),
        },
        {"metric": "Transaction Count", "value_naira": str(stats["transaction_count"])},
    ]

    try:
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=summary_fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        return filepath
    except OSError as e:
        print(f"⚠ Could not write summary CSV: {e}")
        return None


if __name__ == "__main__":
    print("=== Bank Transaction Log Analyser ===\n")

    # Step 1: build and save the dummy transaction data.
    transactions = generate_dummy_transactions()
    txn_path = write_transactions_csv(transactions)
    if txn_path:
        print(f"✅ Wrote {len(transactions)} dummy transaction(s) to {txn_path}")

    # Step 2: read the CSV back with csv.DictReader and compute stats.
    # This is a genuine read-from-disk step, not just reusing the
    # `transactions` list already in memory -- it proves the file we
    # just wrote is actually readable and correctly structured.
    stats = analyse_transactions(txn_path)

    # Step 3: show the results, all currency values in ₦{:,.2f} format.
    print_summary(stats)

    # Step 4: save the stats as their own summary CSV.
    summary_path = write_summary_csv(stats)
    if summary_path:
        print(f"\n✅ Summary CSV saved to {summary_path}")
