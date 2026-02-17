"""Seed database with demo data matching Quicken screenshots."""

import random
import sqlite3
from datetime import date, timedelta


def is_seeded(conn: sqlite3.Connection) -> bool:
    """Check if demo data already exists."""
    cursor = conn.execute("SELECT COUNT(*) FROM accounts")
    return cursor.fetchone()[0] > 0


def seed_database(conn: sqlite3.Connection) -> None:
    """Populate demo data: categories, accounts, transactions, bills, budgets."""
    if is_seeded(conn):
        return

    _seed_categories(conn)
    _seed_accounts(conn)
    cat_map = _get_category_map(conn)
    acct_map = _get_account_map(conn)
    _seed_transactions(conn, cat_map, acct_map)
    _seed_bill_reminders(conn, cat_map, acct_map)
    _seed_budgets(conn, cat_map)
    conn.commit()


def _get_category_map(conn: sqlite3.Connection) -> dict:
    """Return {name: id} for all categories."""
    cursor = conn.execute("SELECT id, name FROM categories")
    return {row[1]: row[0] for row in cursor.fetchall()}


def _get_account_map(conn: sqlite3.Connection) -> dict:
    """Return {name: id} for all accounts."""
    cursor = conn.execute("SELECT id, name FROM accounts")
    return {row[1]: row[0] for row in cursor.fetchall()}


def _seed_categories(conn: sqlite3.Connection) -> None:
    """Insert 40+ categories matching IMPLEMENTATION.md spec."""
    # Income categories (no parent)
    income_cats = [
        ("Salary", "income", 1),
        ("Net Salary Spouse", "income", 2),
        ("Interest Income", "income", 3),
        ("Dividend Income", "income", 4),
        ("Bonus", "income", 5),
    ]
    for name, cat_type, sort in income_cats:
        conn.execute(
            "INSERT INTO categories (name, parent_id, type, is_system, sort_order) VALUES (?, NULL, ?, 0, ?)",
            (name, cat_type, sort),
        )

    # Expense parent categories with children
    expense_groups = [
        ("Food & Dining", ["Restaurants", "Groceries", "Coffee Shops"]),
        ("Auto & Transport", ["Auto Pay", "Gas & Fuel", "Insurance", "Parking", "Public Transit"]),
        ("Home", ["Mortgage", "Rent", "Home Services", "Lawn & Garden", "Home Improvement"]),
        ("Bills & Utilities", ["Electric", "Gas", "Water", "Internet", "Phone", "Cable", "Trash"]),
        ("Entertainment", ["Movies", "Music", "Games", "Streaming"]),
        ("Health & Fitness", ["Gym", "Doctor", "Pharmacy", "Dentist"]),
        ("Shopping", ["Clothing", "Electronics", "General"]),
        ("Taxes", ["Federal Tax", "State Tax", "Property Tax"]),
    ]

    sort_order = 10
    for parent_name, children in expense_groups:
        conn.execute(
            "INSERT INTO categories (name, parent_id, type, is_system, sort_order) VALUES (?, NULL, 'expense', 0, ?)",
            (parent_name, sort_order),
        )
        parent_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        sort_order += 1
        for child_name in children:
            conn.execute(
                "INSERT INTO categories (name, parent_id, type, is_system, sort_order) VALUES (?, ?, 'expense', 0, ?)",
                (child_name, parent_id, sort_order),
            )
            sort_order += 1

    # Expense categories without children
    standalone_expense = [
        "Cash & ATM",
        "Personal Care",
        "Education",
        "Gifts & Donations",
        "Travel",
    ]
    for name in standalone_expense:
        conn.execute(
            "INSERT INTO categories (name, parent_id, type, is_system, sort_order) VALUES (?, NULL, 'expense', 0, ?)",
            (name, sort_order),
        )
        sort_order += 1

    # Transfer categories
    transfer_cats = ["Transfer", "Credit Card Payment"]
    for name in transfer_cats:
        conn.execute(
            "INSERT INTO categories (name, parent_id, type, is_system, sort_order) VALUES (?, NULL, 'transfer', 1, ?)",
            (name, sort_order),
        )
        sort_order += 1


def _seed_accounts(conn: sqlite3.Connection) -> None:
    """Insert 13 accounts from IMPLEMENTATION.md seed spec."""
    accounts = [
        # (name, type, group, institution, initial_balance_cents, is_debt, sort_order)
        ("Family Checking", "checking", "banking", "Chase", 149100, 0, 1),
        ("My Checking", "checking", "banking", "Wells Fargo", 283200, 0, 2),
        ("My Savings", "savings", "banking", "Wells Fargo", 1320000, 0, 3),
        ("My Credit Card", "credit_card", "banking", "Visa", -532500, 1, 4),
        ("Brokerage", "brokerage", "investing", "Fidelity", 9516400, 0, 1),
        ("401(k)", "retirement_401k", "investing", "Vanguard", 8293000, 0, 2),
        ("Car Value", "vehicle", "property_debt", "", 2000000, 0, 1),
        ("House", "property", "property_debt", "", 80000000, 0, 2),
        ("Auto Loan", "loan", "property_debt", "Chase", -1828800, 1, 3),
        ("Home Loan", "mortgage", "property_debt", "Wells Fargo", -28304300, 1, 4),
        ("Loan", "loan", "property_debt", "Bank of America", -33992400, 1, 5),
        ("Dream Home Fund", "savings", "savings_goals", "", 405000, 0, 1),
        ("Vacation Fund", "savings", "savings_goals", "", 70000, 0, 2),
    ]
    for name, acct_type, group, institution, balance, is_debt, sort in accounts:
        conn.execute(
            "INSERT INTO accounts (name, type, account_group, institution, initial_balance, is_debt, sort_order) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (name, acct_type, group, institution, balance, is_debt, sort),
        )


def _seed_transactions(
    conn: sqlite3.Connection, cat_map: dict, acct_map: dict
) -> None:
    """Insert 250+ transactions spanning the last 6 months."""
    today = date.today()
    six_months_ago = today - timedelta(days=180)
    random.seed(42)  # Reproducible seed data

    # Helper to get a random date in the range
    def rand_date(start=six_months_ago, end=today):
        delta = (end - start).days
        return (start + timedelta(days=random.randint(0, delta))).isoformat()

    # Helper category lookup — returns id or None
    def cat(name):
        return cat_map.get(name)

    fam_chk = acct_map["Family Checking"]
    my_chk = acct_map["My Checking"]
    my_sav = acct_map["My Savings"]
    my_cc = acct_map["My Credit Card"]
    brokerage = acct_map["Brokerage"]
    auto_loan = acct_map["Auto Loan"]
    home_loan = acct_map["Home Loan"]
    dream_fund = acct_map["Dream Home Fund"]
    vacation_fund = acct_map["Vacation Fund"]

    transactions = []

    # --- Recurring paychecks (biweekly, ~$3,500) for My Checking ---
    paycheck_date = six_months_ago
    while paycheck_date <= today:
        transactions.append(
            (my_chk, paycheck_date.isoformat(), "Paycheck - Direct Deposit", "Biweekly pay",
             cat("Salary"), "", 350000, "", 0)
        )
        paycheck_date += timedelta(days=14)

    # --- Spouse paycheck (biweekly, $2,600) for Family Checking ---
    spouse_date = six_months_ago + timedelta(days=7)
    while spouse_date <= today:
        transactions.append(
            (fam_chk, spouse_date.isoformat(), "Spouse Paycheck", "Biweekly pay",
             cat("Net Salary Spouse"), "", 260000, "", 0)
        )
        spouse_date += timedelta(days=14)

    # --- Monthly mortgage ($1,400) from My Checking ---
    for m in range(6):
        d = (six_months_ago.replace(day=1) + timedelta(days=32 * m)).replace(day=1)
        if d <= today:
            transactions.append(
                (my_chk, d.isoformat(), "Mortgage Payment", "Monthly mortgage",
                 cat("Mortgage"), "", -140000, "", 0)
            )

    # --- Monthly car payment ($300) from Family Checking ---
    for m in range(6):
        d = (six_months_ago.replace(day=1) + timedelta(days=32 * m)).replace(day=15)
        if d <= today:
            transactions.append(
                (fam_chk, d.isoformat(), "Car Payment", "Monthly auto loan",
                 cat("Auto Pay"), "", -30000, "", 0)
            )

    # --- Credit card payment ($750) from My Checking to CC ---
    for m in range(6):
        d = (six_months_ago.replace(day=1) + timedelta(days=32 * m)).replace(day=20)
        if d <= today:
            transactions.append(
                (my_chk, d.isoformat(), "Credit Card Payment", "Monthly CC payment",
                 cat("Credit Card Payment"), "", -75000, "", 0)
            )
            transactions.append(
                (my_cc, d.isoformat(), "Credit Card Payment", "Monthly CC payment",
                 cat("Credit Card Payment"), "", 75000, "", 0)
            )

    # --- Utility bills (from My Checking, monthly) ---
    utilities = [
        ("Gas & Electric", "Electric", -25000),
        ("Water Bill", "Water", -1000),
        ("Internet Service", "Internet", -6500),
        ("Cell Phone Bill", "Phone", -9000),
        ("Cable Bill", "Cable", -15000),
    ]
    for payee, cat_name, amount in utilities:
        for m in range(6):
            d = (six_months_ago.replace(day=1) + timedelta(days=32 * m)).replace(day=5)
            if d <= today:
                transactions.append(
                    (my_chk, d.isoformat(), payee, "",
                     cat(cat_name), "", amount, "", 0)
                )

    # --- Grocery shopping (weekly, varying amounts) ---
    grocery_date = six_months_ago
    while grocery_date <= today:
        amount = -random.randint(6000, 15000)
        transactions.append(
            (fam_chk, grocery_date.isoformat(), "Trader Joe's", "Weekly groceries",
             cat("Groceries"), "", amount, "", 0)
        )
        grocery_date += timedelta(days=7)

    # --- Restaurants / dining out ---
    restaurant_payees = [
        "Bo-bo- Chili And Ribs", "Olive Garden", "Chipotle",
        "Panda Express", "Subway", "Thai Kitchen",
    ]
    for _ in range(30):
        amount = -random.randint(1500, 8500)
        payee = random.choice(restaurant_payees)
        transactions.append(
            (random.choice([fam_chk, my_cc]), rand_date(), payee, "Dining out",
             cat("Restaurants"), "", amount, "", 0)
        )

    # --- Coffee shops ---
    for _ in range(20):
        amount = -random.randint(350, 750)
        transactions.append(
            (my_cc, rand_date(), "Starbucks", "",
             cat("Coffee Shops"), "", amount, "", 0)
        )

    # --- Gas & Fuel ---
    for _ in range(15):
        amount = -random.randint(3000, 6500)
        transactions.append(
            (fam_chk, rand_date(), "Shell Gas Station", "Fuel",
             cat("Gas & Fuel"), "", amount, "", 0)
        )

    # --- Entertainment / streaming ---
    streaming = [
        ("Netflix", -1250), ("Spotify", -1099), ("Disney+", -1099),
    ]
    for payee, amount in streaming:
        for m in range(6):
            d = (six_months_ago.replace(day=1) + timedelta(days=32 * m)).replace(day=10)
            if d <= today:
                transactions.append(
                    (my_cc, d.isoformat(), payee, "Monthly subscription",
                     cat("Streaming"), "", amount, "", 0)
                )

    # --- GameStop ---
    for _ in range(4):
        amount = -random.randint(1000, 5000)
        transactions.append(
            (my_cc, rand_date(), "GameStop", "",
             cat("Games"), "", amount, "", 0)
        )

    # --- Shopping ---
    shopping_payees = [
        ("Amazon", "General"), ("Target", "General"),
        ("Nordstrom", "Clothing"), ("Best Buy", "Electronics"),
    ]
    for _ in range(20):
        payee, sub_cat = random.choice(shopping_payees)
        amount = -random.randint(1500, 12000)
        transactions.append(
            (my_cc, rand_date(), payee, "",
             cat(sub_cat), "", amount, "", 0)
        )

    # --- ATM withdrawals ---
    for _ in range(8):
        amount = -random.choice([-6000, -10000, -12000, -20000])
        transactions.append(
            (my_chk, rand_date(), "ATM Withdrawal", "",
             cat("Cash & ATM"), "", amount, "", 0)
        )

    # --- Gym membership ($100/mo) ---
    for m in range(6):
        d = (six_months_ago.replace(day=1) + timedelta(days=32 * m)).replace(day=1)
        if d <= today:
            transactions.append(
                (my_chk, d.isoformat(), "Gym Membership", "",
                 cat("Gym"), "", -10000, "", 0)
            )

    # --- Health ---
    health_txns = [
        ("Dr. Smith", "Doctor", -15000),
        ("CVS Pharmacy", "Pharmacy", -4500),
        ("Dr. Johnson DDS", "Dentist", -20000),
    ]
    for payee, sub_cat, amount in health_txns:
        for _ in range(2):
            transactions.append(
                (my_chk, rand_date(), payee, "",
                 cat(sub_cat), "", amount, "", 0)
            )

    # --- Home services ---
    transactions.append(
        (my_chk, rand_date(), "Yard Work", "Lawn service",
         cat("Lawn & Garden"), "", -2500, "", 0)
    )
    transactions.append(
        (my_chk, rand_date(), "Garden Bill", "",
         cat("Lawn & Garden"), "", -1250, "", 0)
    )

    # --- Savings transfers ---
    for m in range(6):
        d = (six_months_ago.replace(day=1) + timedelta(days=32 * m)).replace(day=25)
        if d <= today:
            transactions.append(
                (my_chk, d.isoformat(), "Transfer To Savings", "",
                 cat("Transfer"), "", -20000, "", 0)
            )
            transactions.append(
                (my_sav, d.isoformat(), "Transfer From Checking", "",
                 cat("Transfer"), "", 20000, "", 0)
            )

    # --- Dream Home Fund contributions ---
    for m in range(6):
        d = (six_months_ago.replace(day=1) + timedelta(days=32 * m)).replace(day=28)
        if d <= today:
            transactions.append(
                (my_chk, d.isoformat(), "Transfer to Dream Home Fund", "",
                 cat("Transfer"), "", -15000, "", 0)
            )
            transactions.append(
                (dream_fund, d.isoformat(), "Transfer From Checking", "",
                 cat("Transfer"), "", 15000, "", 0)
            )

    # --- Vacation Fund ---
    for m in range(0, 6, 2):
        d = (six_months_ago.replace(day=1) + timedelta(days=32 * m)).replace(day=28)
        if d <= today:
            transactions.append(
                (fam_chk, d.isoformat(), "Transfer to Vacation Fund", "",
                 cat("Transfer"), "", -10000, "", 0)
            )
            transactions.append(
                (vacation_fund, d.isoformat(), "Transfer From Checking", "",
                 cat("Transfer"), "", 10000, "", 0)
            )

    # --- Interest income ---
    for m in range(6):
        d = (six_months_ago.replace(day=1) + timedelta(days=32 * m)).replace(day=28)
        if d <= today:
            transactions.append(
                (my_sav, d.isoformat(), "Interest Payment", "",
                 cat("Interest Income"), "", random.randint(500, 1500), "", 0)
            )

    # --- Dividend income (quarterly) ---
    for m in range(0, 6, 3):
        d = (six_months_ago.replace(day=1) + timedelta(days=32 * m)).replace(day=15)
        if d <= today:
            transactions.append(
                (brokerage, d.isoformat(), "Dividend Payment", "Quarterly dividend",
                 cat("Dividend Income"), "", random.randint(50000, 120000), "", 0)
            )

    # --- Insurance (quarterly from Family Checking) ---
    for m in range(0, 6, 3):
        d = (six_months_ago.replace(day=1) + timedelta(days=32 * m)).replace(day=12)
        if d <= today:
            transactions.append(
                (fam_chk, d.isoformat(), "Car Insurance", "",
                 cat("Insurance"), "", -15000, "", 0)
            )

    # --- Personal care, education, gifts ---
    misc = [
        ("Hair Salon", "Personal Care", -4500),
        ("Udemy Course", "Education", -1299),
        ("Birthday Gift", "Gifts & Donations", -5000),
        ("Charity Donation", "Gifts & Donations", -10000),
        ("Hotel Stay", "Travel", -25000),
        ("Flight Tickets", "Travel", -45000),
    ]
    for payee, sub_cat, amount in misc:
        transactions.append(
            (random.choice([my_chk, my_cc]), rand_date(), payee, "",
             cat(sub_cat), "", amount, "", 0)
        )

    # --- Taxes (quarterly) ---
    for m in range(0, 6, 3):
        d = (six_months_ago.replace(day=1) + timedelta(days=32 * m)).replace(day=15)
        if d <= today:
            transactions.append(
                (my_chk, d.isoformat(), "IRS - Estimated Tax", "",
                 cat("Federal Tax"), "", -180000, "", 0)
            )
            transactions.append(
                (my_chk, d.isoformat(), "State Tax Payment", "",
                 cat("State Tax"), "", -45000, "", 0)
            )

    # --- Home loan payments ---
    for m in range(6):
        d = (six_months_ago.replace(day=1) + timedelta(days=32 * m)).replace(day=1)
        if d <= today:
            transactions.append(
                (home_loan, d.isoformat(), "Home Loan Payment", "",
                 cat("Mortgage"), "", 140000, "", 0)
            )

    # --- Auto loan payments ---
    for m in range(6):
        d = (six_months_ago.replace(day=1) + timedelta(days=32 * m)).replace(day=15)
        if d <= today:
            transactions.append(
                (auto_loan, d.isoformat(), "Auto Loan Payment", "",
                 cat("Auto Pay"), "", 30000, "", 0)
            )

    # Insert all transactions
    for txn in transactions:
        conn.execute(
            "INSERT INTO transactions (account_id, date, payee, memo, category_id, tag, amount, check_number, is_reconciled) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            txn,
        )


def _seed_bill_reminders(
    conn: sqlite3.Connection, cat_map: dict, acct_map: dict
) -> None:
    """Insert 6 bill reminders matching Quicken screenshots."""
    today = date.today()
    my_chk = acct_map["My Checking"]
    fam_chk = acct_map["Family Checking"]

    bills = [
        # (name, amount_cents, category, account, frequency, next_due, is_income, is_auto)
        ("Cable Bill", -15000, "Cable", my_chk, "monthly",
         _next_month_day(today, 5), 0, 0),
        ("Car Insurance", -15000, "Insurance", fam_chk, "quarterly",
         _next_month_day(today, 12), 0, 0),
        ("Cell Phone", -9000, "Phone", my_chk, "monthly",
         _next_month_day(today, 8), 0, 0),
        ("Credit Card Payment", -75000, "Credit Card Payment", my_chk, "monthly",
         _next_month_day(today, 20), 0, 1),
        ("Internet Service", -6500, "Internet", my_chk, "monthly",
         _next_month_day(today, 5), 0, 1),
        ("Transfer To Savings", -20000, "Transfer", my_chk, "monthly",
         _next_month_day(today, 25), 0, 1),
    ]

    for name, amount, cat_name, acct_id, freq, due, is_income, is_auto in bills:
        conn.execute(
            "INSERT INTO bill_reminders (name, amount, category_id, account_id, frequency, next_due_date, is_income, is_automatic) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (name, amount, cat_map.get(cat_name), acct_id, freq, due, is_income, is_auto),
        )


def _seed_budgets(conn: sqlite3.Connection, cat_map: dict) -> None:
    """Insert 7 monthly budgets for the current month."""
    today = date.today()
    year = today.year
    month = today.month

    budgets = [
        ("Food & Dining", 60000),
        ("Auto & Transport", 50000),
        ("Bills & Utilities", 55000),
        ("Entertainment", 15000),
        ("Shopping", 20000),
        ("Health & Fitness", 15000),
        ("Home", 160000),
    ]

    for cat_name, amount in budgets:
        cat_id = cat_map.get(cat_name)
        if cat_id:
            conn.execute(
                "INSERT INTO budgets (category_id, amount, year, month) VALUES (?, ?, ?, ?)",
                (cat_id, amount, year, month),
            )


def _next_month_day(ref: date, day: int) -> str:
    """Return the next occurrence of a given day-of-month as ISO string."""
    # If the day this month hasn't passed yet, use it; otherwise next month
    try:
        candidate = ref.replace(day=day)
    except ValueError:
        # Day exceeds month length, use last day
        candidate = ref.replace(day=28)
    if candidate <= ref:
        # Move to next month
        if ref.month == 12:
            candidate = ref.replace(year=ref.year + 1, month=1, day=day)
        else:
            try:
                candidate = ref.replace(month=ref.month + 1, day=day)
            except ValueError:
                candidate = ref.replace(month=ref.month + 1, day=28)
    return candidate.isoformat()
