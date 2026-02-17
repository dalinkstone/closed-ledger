"""Database schema initialization. All CREATE statements use IF NOT EXISTS."""

import sqlite3

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    type TEXT NOT NULL CHECK(type IN (
        'checking','savings','credit_card','cash',
        'brokerage','retirement_401k','ira',
        'property','vehicle','loan','mortgage',
        'other_asset','other_liability'
    )),
    account_group TEXT NOT NULL CHECK(account_group IN (
        'banking','investing','property_debt','savings_goals'
    )),
    institution TEXT DEFAULT '',
    initial_balance INTEGER NOT NULL DEFAULT 0,
    is_debt INTEGER NOT NULL DEFAULT 0,
    is_hidden INTEGER NOT NULL DEFAULT 0,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    parent_id INTEGER REFERENCES categories(id),
    type TEXT NOT NULL DEFAULT 'expense' CHECK(type IN ('income','expense','transfer')),
    is_system INTEGER NOT NULL DEFAULT 0,
    sort_order INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL REFERENCES accounts(id),
    date TEXT NOT NULL,
    payee TEXT NOT NULL DEFAULT '',
    memo TEXT DEFAULT '',
    category_id INTEGER REFERENCES categories(id),
    tag TEXT DEFAULT '',
    amount INTEGER NOT NULL,
    check_number TEXT DEFAULT '',
    is_reconciled INTEGER NOT NULL DEFAULT 0,
    transfer_account_id INTEGER REFERENCES accounts(id),
    transfer_transaction_id INTEGER REFERENCES transactions(id),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS bill_reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    amount INTEGER NOT NULL,
    category_id INTEGER REFERENCES categories(id),
    account_id INTEGER REFERENCES accounts(id),
    frequency TEXT NOT NULL DEFAULT 'monthly' CHECK(frequency IN (
        'weekly','biweekly','monthly','quarterly','annually','once'
    )),
    next_due_date TEXT NOT NULL,
    is_income INTEGER NOT NULL DEFAULT 0,
    is_automatic INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS budgets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL REFERENCES categories(id),
    amount INTEGER NOT NULL,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    UNIQUE(category_id, year, month)
);

CREATE INDEX IF NOT EXISTS idx_transactions_account_date ON transactions(account_id, date);
CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category_id);
CREATE INDEX IF NOT EXISTS idx_transactions_payee ON transactions(payee);
CREATE INDEX IF NOT EXISTS idx_categories_parent ON categories(parent_id);
CREATE INDEX IF NOT EXISTS idx_bill_reminders_due ON bill_reminders(next_due_date);
"""


def initialize_schema(conn: sqlite3.Connection) -> None:
    """Execute all CREATE TABLE and CREATE INDEX statements."""
    conn.executescript(SCHEMA_SQL)
    conn.commit()


def get_schema_version(conn: sqlite3.Connection) -> int:
    """Get the current schema version using PRAGMA user_version."""
    cursor = conn.execute("PRAGMA user_version")
    return cursor.fetchone()[0]


def set_schema_version(conn: sqlite3.Connection, version: int) -> None:
    """Set the schema version. Note: PRAGMA doesn't support parameterized values."""
    # PRAGMA user_version does not support ? placeholders, so we validate the int
    if not isinstance(version, int) or version < 0:
        raise ValueError("Schema version must be a non-negative integer")
    conn.execute(f"PRAGMA user_version = {version}")
    conn.commit()
