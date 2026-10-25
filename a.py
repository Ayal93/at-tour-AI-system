import numpy as np                      # arrays and math
import pandas as pd                     # load CSV / Excel data
import matplotlib.pyplot as plt         # plot loss and results





FILE = "car_rental_workbook.xlsx"
INCLUDE_LOANS = True                      # False if owners pay the loans
OTHER_EXPENSES = {"Oct 2026": 15000}      # insurance, wages, rent... (sample)

MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
def month_index(text):                    # "Oct 2026" -> 2026*12 + 10
    return int(text[-4:]) * 12 + MONTHS.index(text[:3]) + 1

def load(sheet, key, prefix):
    """Read a sheet and keep only real data rows (skips TOTAL and note rows)."""
    df = pd.read_excel(FILE, sheet_name=sheet)
    return df[df[key].astype(str).str.startswith(prefix)].copy()

# ---- 1. Load the sheets ----
vehicles    = load("Vehicles", "Vehicle No", "V")
rentals     = load("Rentals", "Rental ID", "RT")
maintenance = load("Maintenance", "Maint ID", "M")
loans       = load("Vehicle Loans", "Loan ID", "L")
owner_pay   = load("Owner Payments", "Rental ID", "RT")
receipts    = load("Renter Receipts", "Rental ID", "RT")

# ---- 2. Loan installment (reducing balance, same as Excel PMT) ----
def installment(amount, annual_rate, months):
    r = annual_rate / 12
    return amount / months if r == 0 else amount * r / (1 - (1 + r) ** -months)

loans["Installment"] = [installment(a, r, n) for a, r, n in
                        zip(loans["Loan Amount"], loans["Annual Interest Rate"], loans["Term (months)"])]
loans["start_idx"] = pd.to_datetime(loans["Start Date"]).apply(lambda d: d.year * 12 + d.month)

# ---- 3. Profit for one month ----
def monthly_profit(month):
    idx = month_index(month)

    # rentals of the month joined with vehicle rates
    rt = rentals[rentals["Month"] == month].merge(vehicles, on="Vehicle No")
    billed     = (rt["Days Rented"] * rt["Rate Charged to Renter (per day)"]).sum()
    owner_gross = (rt["Days Rented"] * rt["Rate Paid to Owner (per day)"]).sum()

    # maintenance: we pay it all, owners repay only where "Owner (deducted)"
    mt = maintenance[maintenance["Month"] == month].merge(
        vehicles[["Vehicle No", "Who Bears Cost"]], on="Vehicle No")
    maint_paid      = mt["Cost (LKR)"].sum()
    maint_recovered = mt.loc[mt["Who Bears Cost"] == "Owner (deducted)", "Cost (LKR)"].sum()

    # loan installments for loans running in that month
    active = loans[(loans["start_idx"] <= idx) & (idx < loans["start_idx"] + loans["Term (months)"])]
    loan_cost = active["Installment"].sum() if INCLUDE_LOANS else 0.0
    other = OTHER_EXPENSES.get(month, 0.0)

    margin = billed - owner_gross
    profit_before_loans = margin - maint_paid + maint_recovered
    net_profit = profit_before_loans - loan_cost - other

    # cash side: amounts actually received / paid (input columns in the workbook)
    received = receipts.loc[receipts["Month"] == month, "Amount Received"].sum()
    paid_out = owner_pay.loc[owner_pay["Month"] == month, "Amount Paid"].sum()
    cash_profit = received - paid_out - maint_paid - loan_cost - other

    return {
        "Month": month,
        "Billed": billed,
        "Owner gross pay": owner_gross,
        "Rental margin": margin,
        "Maintenance paid": maint_paid,
        "Maintenance recovered": maint_recovered,
        "Profit before loans": profit_before_loans,
        "Loan installments": loan_cost,
        "Other expenses": other,
        "NET PROFIT": net_profit,
        "Margin %": net_profit / billed * 100 if billed else 0,
        "Cash received": received,
        "Paid to owners": paid_out,
        "CASH PROFIT": cash_profit,
    }

# ---- 4. Run for every month that has rentals ----
result = pd.DataFrame([monthly_profit(m) for m in rentals["Month"].unique()])
pd.options.display.float_format = "{:,.0f}".format
print(result.T.to_string(header=False))
result.to_excel("monthly_profit_result.xlsx", index=False)