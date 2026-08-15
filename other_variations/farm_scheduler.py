# farm_scheduler.py
# Task 18B: Farm Harvest Scheduler
# Demonstrating datetime arithmetic, parsing, and formatting with Nigerian crop data.

from datetime import datetime, date, timedelta


def run_farm_scheduler():
    """Tracks crop growth status, maturity percentage, and harvest schedules."""
    # -------------------------------------------------------------------------
    # STEP 1: Define at least 4 crops with planting dates and maturity periods
    # -------------------------------------------------------------------------
    crops = [
        {"name": "Maize", "planted_date": "2026-05-15", "maturity_days": 90},
        {"name": "Yam", "planted_date": "2026-03-10", "maturity_days": 180},
        {"name": "Cassava", "planted_date": "2025-08-01", "maturity_days": 360},
        {"name": "Tomato", "planted_date": "2026-07-01", "maturity_days": 75},
        {"name": "Plantain", "planted_date": "2026-01-10", "maturity_days": 300},
    ]

    # Capture today's date for current status calculations
    today = date.today()

    print("=================================================================")
    print(
        f"🌾 NIGERIAN FARM HARVEST SCHEDULER — {today.strftime('%A, %d %B %Y')}"
    )
    print("=================================================================\n")

    # Iterate through each crop record
    for crop in crops:
        # -------------------------------------------------------------------------
        # STEP 2: Parse planting date strings into date objects using strptime()
        # -------------------------------------------------------------------------
        # datetime.strptime converts string -> datetime object; .date() extracts date portion
        planting_dt = datetime.strptime(
            crop["planted_date"], "%Y-%m-%d"
        ).date()

        # -------------------------------------------------------------------------
        # STEP 3: Calculate harvest date using timedelta arithmetic
        # -------------------------------------------------------------------------
        # Adding timedelta(days) automatically handles calendar/month boundaries
        harvest_dt = planting_dt + timedelta(days=crop["maturity_days"])

        # -------------------------------------------------------------------------
        # STEP 4: Calculate days grown, days remaining, and percentage maturity
        # -------------------------------------------------------------------------
        days_grown = (today - planting_dt).days
        days_remaining = (harvest_dt - today).days

        # Ensure percentage calculation does not drop below 0% or exceed 100% caps
        raw_percentage = (days_grown / crop["maturity_days"]) * 100
        pct_maturity = max(0.0, min(100.0, raw_percentage))

        # -------------------------------------------------------------------------
        # STEP 5: Format dates into human-readable strings using strftime()
        # -------------------------------------------------------------------------
        formatted_planting = planting_dt.strftime("%d %B %Y")
        formatted_harvest = harvest_dt.strftime("%A, %d %B %Y")

        # Display crop header and basic information
        print(f"🌱 Crop: {crop['name']}")
        print(f"   • Planted On    : {formatted_planting}")
        print(f"   • Expected Date : {formatted_harvest}")
        print(f"   • Growth Period : {crop['maturity_days']} days total")
        print(f"   • Days Grown    : {days_grown} day(s)")
        print(f"   • Maturity      : {pct_maturity:.1f}%")

        # -------------------------------------------------------------------------
        # STEP 6: Handle overdue crops and status warnings
        # -------------------------------------------------------------------------
        if days_remaining < 0:
            overdue_days = abs(days_remaining)
            print(
                f"   • Status        : 🔴 OVERDUE by {overdue_days} day(s)! Harvest immediately to prevent spoilage."
            )
        elif days_remaining == 0:
            print(
                "   • Status        : 🟢 READY FOR HARVEST TODAY! Prepare field hands."
            )
        elif days_remaining <= 14:
            print(
                f"   • Status        : 🟡 HARVEST APPROACHING! Ready in {days_remaining} day(s)."
            )
        else:
            print(
                f"   • Status        : ⏳ GROWING smoothly ({days_remaining} day(s) remaining)."
            )

        print("-" * 65)


# Execute script when run directly
if __name__ == "__main__":
    run_farm_scheduler()