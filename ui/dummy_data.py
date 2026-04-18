"""
Dummy/sample data for all segments — shown ONLY when no real data exists.
Once the user uploads a bank statement, all segments switch to real data automatically.
"""
from datetime import date, datetime, timedelta
import pandas as pd

_TODAY = date(2026, 4, 18)


def _d(offset_days: int) -> date:
    return _TODAY - timedelta(days=offset_days)


def _dt(offset_days: int) -> datetime:
    return datetime.combine(_d(offset_days), datetime.min.time())


# ---------------------------------------------------------------------------
# 1. DASHBOARD
# ---------------------------------------------------------------------------
DUMMY_SUMMARY = {
    "income": 85000.0,
    "expenses": 42350.0,
    "net": 42650.0,
    "categories": {
        "Food & Dining": 8500.0,
        "Transportation": 4200.0,
        "Shopping": 9800.0,
        "Bills & Utilities": 6100.0,
        "Entertainment": 3250.0,
        "Healthcare": 2800.0,
        "Travel": 5200.0,
        "Education": 2500.0,
    },
}
DUMMY_HEALTH_SCORE = 78.0
DUMMY_ANOMALIES = [
    {"amount": 14500.0, "description": "International Wire Transfer"},
    {"amount": 12000.0, "description": "Annual Insurance Premium"},
]

# ---------------------------------------------------------------------------
# 2. EXPENSES — 20 realistic sample transactions
# ---------------------------------------------------------------------------
_raw_txns = [
    (-850.0,  "Swiggy Food Order",           "Food & Dining"),
    (85000.0, "Salary Credit - Employer",    "Other"),
    (-1200.0, "Metro & Auto Fare",           "Transportation"),
    (-3500.0, "Amazon Shopping",             "Shopping"),
    (-2200.0, "Electricity Bill - TNEB",     "Bills & Utilities"),
    (-650.0,  "Movie Tickets - PVR",         "Entertainment"),
    (-900.0,  "Apollo Pharmacy",             "Healthcare"),
    (-5200.0, "Flight Booking - Delhi",      "Travel"),
    (-1100.0, "Zomato Dinner",               "Food & Dining"),
    (-800.0,  "Ola / Uber Rides",            "Transportation"),
    (-4500.0, "Flipkart Order",              "Shopping"),
    (-1800.0, "Internet + OTT Bundle",       "Bills & Utilities"),
    (-1500.0, "Udemy Online Course",         "Education"),
    (-600.0,  "Starbucks Coffee",            "Food & Dining"),
    (-700.0,  "Petrol / Fuel",               "Transportation"),
    (-3200.0, "Myntra Clothing",             "Shopping"),
    (-900.0,  "Water & Gas Bill",            "Bills & Utilities"),
    (-1200.0, "Concert Tickets",             "Entertainment"),
    (-1800.0, "Doctor Consultation",         "Healthcare"),
    (-2500.0, "Weekend Hotel Stay",          "Travel"),
]

DUMMY_TRANSACTIONS = pd.DataFrame([
    {
        "_id": f"dummy_{i}",
        "Date": _d(i * 2),
        "Amount": amt,
        "Description": desc,
        "Category": cat,
        "Notes": "",
    }
    for i, (amt, desc, cat) in enumerate(_raw_txns)
])

# ---------------------------------------------------------------------------
# 3. BUDGET — category budgets with progress
# ---------------------------------------------------------------------------
DUMMY_BUDGET_PROGRESS = {
    "Food & Dining":      {"budgeted": 10000.0, "spent": 8500.0,  "remaining": 1500.0,  "percentage": 85.0},
    "Transportation":     {"budgeted":  5000.0, "spent": 4200.0,  "remaining":  800.0,  "percentage": 84.0},
    "Shopping":           {"budgeted": 12000.0, "spent": 9800.0,  "remaining": 2200.0,  "percentage": 81.6},
    "Bills & Utilities":  {"budgeted":  8000.0, "spent": 6100.0,  "remaining": 1900.0,  "percentage": 76.3},
    "Entertainment":      {"budgeted":  4000.0, "spent": 3250.0,  "remaining":  750.0,  "percentage": 81.3},
    "Healthcare":         {"budgeted":  3000.0, "spent": 2800.0,  "remaining":  200.0,  "percentage": 93.3},
    "Travel":             {"budgeted":  6000.0, "spent": 5200.0,  "remaining":  800.0,  "percentage": 86.7},
    "Education":          {"budgeted":  3000.0, "spent": 2500.0,  "remaining":  500.0,  "percentage": 83.3},
}

# ---------------------------------------------------------------------------
# 4. GOALS — sample savings goals
# ---------------------------------------------------------------------------
DUMMY_GOALS = [
    {
        "_id": "dummy_goal_1",
        "name": "Emergency Fund",
        "target_amount": 300000.0,
        "current_amount": 185000.0,
        "target_date": datetime(2026, 12, 31),
        "created_at": datetime(2026, 1, 1),
    },
    {
        "_id": "dummy_goal_2",
        "name": "Vacation to Europe 🌍",
        "target_amount": 150000.0,
        "current_amount": 65000.0,
        "target_date": datetime(2026, 9, 1),
        "created_at": datetime(2026, 2, 1),
    },
    {
        "_id": "dummy_goal_3",
        "name": "New Laptop 💻",
        "target_amount": 80000.0,
        "current_amount": 72000.0,
        "target_date": datetime(2026, 5, 30),
        "created_at": datetime(2026, 3, 1),
    },
]

# ---------------------------------------------------------------------------
# 5. INVESTMENTS — sample portfolio
# ---------------------------------------------------------------------------
DUMMY_INVESTMENTS = [
    {"_id": "dinv1", "ticker": "RELIANCE.NS",  "quantity": 10.0, "purchase_price": 2850.0, "purchase_date": _dt(120)},
    {"_id": "dinv2", "ticker": "TCS.NS",       "quantity":  5.0, "purchase_price": 3750.0, "purchase_date": _dt(90)},
    {"_id": "dinv3", "ticker": "INFY.NS",      "quantity": 15.0, "purchase_price": 1480.0, "purchase_date": _dt(60)},
    {"_id": "dinv4", "ticker": "HDFCBANK.NS",  "quantity":  8.0, "purchase_price": 1620.0, "purchase_date": _dt(30)},
    {"_id": "dinv5", "ticker": "BAJFINANCE.NS","quantity":  3.0, "purchase_price": 6800.0, "purchase_date": _dt(15)},
]

# ---------------------------------------------------------------------------
# 6. REPORTS — reused from transactions above
# ---------------------------------------------------------------------------
DUMMY_REPORT_DF = DUMMY_TRANSACTIONS.drop(columns=["_id"]).copy()
DUMMY_REPORT_SUMMARY = {
    "income": 85000.0,
    "expenses": 42350.0,
    "net": 42650.0,
}
