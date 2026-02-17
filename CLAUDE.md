# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Closed Ledger is a local-first, single-user personal finance desktop app modeled after Quicken Classic (2013-2017). It is a **native desktop application** — no web server, no HTTP, no localhost, no browser. Python + PySide6 (Qt 6) + SQLite, encrypted at rest. Your financial data never leaves your filesystem.

## Key Reference Files

- **IMPLEMENTATION.md** — Source of truth for schema, security requirements, UI specs, color palette, and phase details. **Read before starting any phase.**
- **INSTRUCTIONS.md** — Phased build workflow with copy-paste prompts and testing checklists
- **README.md** — Project overview, architecture rationale, data model diagram, project structure

## Setup & Run

```bash
git clone https://github.com/dalinkstone/closed-ledger.git
cd closed-ledger
python3 -m venv venv
source venv/bin/activate            # macOS/Linux (venv\Scripts\activate on Windows)
pip install -r requirements.txt
python -m closed_ledger             # First run: prompts to create passphrase
python -m closed_ledger --seed      # Optional: populate demo data
```

All data is stored in the gitignored `data/` directory. Each machine creates its own passphrase and encrypted database on first run — nothing is shared between machines via git.

No test framework is configured. Verify correctness with the testing checklists in INSTRUCTIONS.md.

## Tech Stack

Python 3.11+, PySide6 (Qt 6) for GUI, SQLite via Python's built-in `sqlite3`, `cryptography` (Fernet/AES-256) for database encryption. **Only two external dependencies**: `PySide6>=6.6` and `cryptography>=42.0`.

## Architecture

### Development Phases

The project is built in 8 sequential phases, each designed for a fresh Claude Code session:

1. Foundation (project structure, security/encryption layer, passphrase gate, schema, seed data, main window shell)
2. Account Sidebar (QTreeView, live balances, groups, net worth, account CRUD)
3. Transaction Register (QTableView + model/view/delegate, inline editing, filters, running balance)
4. Home Dashboard (QtCharts donut chart, bill reminders, budget summary)
5. Categories & Budgets (category tree CRUD, budget tracking, progress bars)
6. Bills & Scheduling (bill CRUD, mark-as-paid, recurring date advancement)
7. Reports (spending over time, net worth, income vs expenses, category breakdown — all QtCharts)
8. Polish (CSV import/export, Ctrl+K search, auto-lock, keyboard shortcuts, encrypted backup/restore)

### Project Structure

```
closed_ledger/
├── __main__.py              # Entry point: python -m closed_ledger
├── app.py                   # QApplication setup, passphrase gate, main window launch
├── security/                # Encryption, passphrase dialogs, auto-lock
│   ├── crypto.py            # Fernet encrypt/decrypt, PBKDF2 key derivation, secure delete
│   ├── passphrase.py        # FirstRunDialog, UnlockDialog (Qt dialogs)
│   └── session.py           # Auto-lock timer, session state
├── db/
│   ├── connection.py        # DatabaseManager: decrypt→open→use→close→encrypt cycle
│   ├── schema.py            # CREATE TABLE/INDEX statements (additive, IF NOT EXISTS)
│   ├── seed.py              # Demo data (13 accounts, 250+ transactions, 40+ categories)
│   └── queries/             # All SQL query functions (accounts, transactions, categories, bills, budgets, dashboard, reports)
├── ui/
│   ├── main_window.py       # QMainWindow: sidebar + QTabBar + QStackedWidget
│   ├── sidebar.py           # QTreeView account sidebar
│   ├── views/               # Home, Register, Spending, Bills, Budgets, Reports
│   ├── models/              # QAbstractTableModel subclasses for Qt model/view
│   ├── delegates/           # CurrencyDelegate, DateDelegate, CategoryDelegate for QTableView
│   ├── dialogs/             # Account, bill, import, backup dialogs
│   └── widgets/             # DonutChart, BarChart, LineChart (QtCharts), CurrencyLabel
└── utils/
    ├── currency.py          # cents ↔ display formatting (all money is stored as integer cents)
    ├── dates.py             # Date helpers
    └── platform.py          # Platform-specific app data paths, file permissions
```

### Security Model (Non-Negotiable)

These are hard requirements — every phase must comply:

- **No network access.** No imports of `requests`, `urllib`, `http`, `socket`. No `QNetworkAccessManager`. The app never opens a socket or binds a port.
- **Encrypted at rest.** SQLite database stored as `.db.enc` (Fernet/AES-256). Decrypted to temp file only while running. Temp file is overwritten with `os.urandom` bytes and deleted on close.
- **Passphrase-gated.** PBKDF2-HMAC-SHA256 with 600,000 iterations. Passphrase never stored to disk, overwritten in memory after key derivation.
- **File permissions.** App data directory: `0o700`. All files: `0o600`.
- **Parameterized SQL only.** ALL queries use `?` placeholders. Never use f-strings, `.format()`, or `%` in SQL. Verify with: `grep -rn "f'" closed_ledger/db/` (should find nothing).

### Data Conventions

- **All monetary values stored as integers in cents** (e.g., `$1,234.56` → `123456`). Conversion to dollars only in the UI layer via `cents_to_display()`.
- **Negative amounts** = money leaving account (payments, expenses). **Positive** = money entering (deposits, income).
- **Account balances are never stored** — always computed: `initial_balance + COALESCE(SUM(transactions.amount), 0)`.
- **Transfers** create two linked transactions referencing each other via `transfer_transaction_id`.
- **Running balance** in register: sort by `date ASC, id ASC`, accumulate from `initial_balance`.
- **Dates** stored as TEXT in ISO format. Display format: `M/D/YYYY` (no zero-padding).
- **Currency in register table**: no `$` sign, just `"300.00"` (tabular-nums). In sidebar/dashboard: `$1,234` format with `$` sign.

### Database

All persistent data lives in the gitignored `data/` directory at the project root. Each machine creates its own passphrase, salt, and encrypted database on first run — nothing is shared between machines via git.

```
data/                         ← gitignored, per-machine
├── closed-ledger.db.enc      ← encrypted SQLite database
├── salt                       ← PBKDF2 salt (not secret, but per-machine)
├── key_check                  ← encrypted canary for passphrase verification
├── config.json                ← window geometry, preferences
└── backups/                   ← encrypted backup copies
```

Schema managed via additive `CREATE TABLE IF NOT EXISTS` statements in `schema.py`. Five tables: `accounts`, `transactions`, `categories`, `bill_reminders`, `budgets`.

### Qt Model/View Architecture

The transaction register (the core view) uses Qt's Model/View pattern:
- **TransactionTableModel** (QAbstractTableModel): holds data, implements `data()`, `setData()`, `flags()`
- **QTableView**: displays the model with explicit column widths matching Quicken layout
- **Custom Delegates**: CurrencyDelegate (right-aligned currency), DateDelegate (M/D/YYYY), CategoryDelegate (combobox with QCompleter)

### Color Palette

```
Sidebar bg: #F5F5F5 | Sidebar header/footer: #EBEBEB | Tab bar: #2B579A (navy)
Tab selected: #1E4270 | Tab accent: #5BA3E6 | Link/action: #2B579A
Negative: #CC0000 | Positive: #006600 | Text primary: #333 | Text secondary: #555
Row alt: #F0F5FA | Row hover: #E3EDF7 | Row selected: #D0E0F0 | Borders: #D0D0D0/#E0E0E0
```

### Tab Names

ALL CAPS matching Quicken: HOME, SPENDING, BILLS & INCOME, PLANNING, INVESTING, PROPERTY & DEBT, REPORTS.

### UI Density

Dense layout matching Quicken: 11-13px base font, 30-34px row heights, 240px fixed sidebar. Negative balances in red. Sidebar accounts ~12px, group headers 13px bold.

### Startup Flow

1. `QApplication` created
2. Ensure app data directory exists with `0o700` permissions
3. If first run (no `salt`/`key_check` files): show `FirstRunDialog` → create passphrase → derive key → create encrypted DB
4. If returning: show `UnlockDialog` → verify passphrase against canary → decrypt DB to temp file
5. Open `DatabaseManager` with derived key
6. If `--seed` flag: populate demo data
7. Show `MainWindow`
8. On close: encrypt DB back to disk, secure-delete temp file
