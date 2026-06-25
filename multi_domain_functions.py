#      AGRITECH
width = 50
print("\n" + '='*width)
def estimate_revenue(yield_kg, price_per_kg, transport_cost=0):
    """Calculating net farm revenue. Transport cost = 0 by default"""
    gross = yield_kg * price_per_kg
    net = gross - transport_cost
    return net
print(f"Maize farm: N{estimate_revenue(500, 1200):,.2f}")
print(f"Tomato farm: N{estimate_revenue(500, 1200, 15000):,.2f}")

#     FINTECH
print("\n" + '='*width)
def loan_eligibility(monthly_income, monthly_expenses):
    """Return (disposable_income, is_eligible). Eligible if disposable >= ₦20,000."""
    disposable = monthly_income - monthly_expenses
    is_eligible = disposable >= 20000
    return disposable, is_eligible
disp, eligible = loan_eligibility(150000, 90000)
print(f"Applicant 1: Disposable ₦{disp:,.2f} | Eligible: {eligible}")
disp, eligible = loan_eligibility(85000, 70000)
print(f"Applicant 2: Disposable ₦{disp:,.2f} | Eligible: {eligible}")

#    EDUCATION 
print("\n" + '='*width)
def class_average(scores_list):
    """Return (average_score, highest_score) from a list of scores."""
    if not scores_list:
        return 0, 0
    average = sum(scores_list) / len(scores_list)
    highest = max(scores_list)
    return average, highest
avg, high = class_average([68, 74, 82, 55, 90])
print(f"JSS3A — Average: {avg:.1f} | Highest: {high}")
avg, high = class_average([45, 52, 61, 58])
print(f"JSS3B — Average: {avg:.1f} | Highest: {high}")

#      LOGISTICS
print("\n" + '='*width)
def delivery_eta(distance_km, speed_kmh=40, traffic_delay_min=0):
    """Estimate delivery time in minutes. Default speed 40km/h (Port Harcourt)."""
    travel_min = (distance_km / speed_kmh) * 60
    total_min = travel_min + traffic_delay_min
    return round(total_min, 1)
print(f"PH → Eleme (22km): {delivery_eta(22)} min")
print(f"PH → Aba (65km, traffic 25min): {delivery_eta(65, traffic_delay_min=25)} min")
print("\n" + '='*width)