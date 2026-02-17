# Closed Ledger — A Quicken-Inspired Personal Finance Manager

> A native desktop personal finance application modeled after Quicken Classic (2013–2017). Fully offline. No servers, no ports, no network. Python + Qt + SQLite.

---

## Overview

Closed Ledger is a faithful recreation of Intuit's Quicken personal finance software — specifically the Quicken Premier 2013–2017 era desktop experience. It provides comprehensive personal finance management including account tracking, transaction registers, budgeting, bill reminders, spending analysis, and net worth calculation.

This is a **true desktop application**. It runs as a native window on your machine. There is no web server, no localhost binding, no HTTP, no browser. Your financial data never leaves your filesystem.

This project exists as a personal tool and learning exercise. It is not affiliated with Quicken Inc. or Intuit.

## Security Model

Closed Ledger treats your financial data as sensitive by default.

- **Zero network exposure.** The application makes no network calls, opens no ports, binds no sockets. There is no server process. Outbound network access is never initiated.
- **Master passphrase.** The application requires a passphrase on first launch. This passphrase is used to derive an encryption key (PBKDF2-HMAC-SHA256, 600,000 iterations) that encrypts your database file at rest using AES-256 via the `cryptography` library's Fernet implementation.
- **Encrypted at rest.** The SQLite database is stored encrypted on disk. It is decrypted into memory only while the application is running. On close, the database is re-encrypted and the plaintext is securely overwritten.
- **Restrictive file permissions.** Database and backup files are created with `0o600` permissions (owner read/write only).
- **Auto-lock.** After a configurable inactivity timeout (default: 15 minutes), the application locks and requires the passphrase to resume.
- **Parameterized queries only.** All SQL operations use parameterized queries. No string interpolation or formatting is ever used in SQL statements.
- **Encrypted backups.** Backup files are encrypted with the same master key. Unencrypted data is never written to disk.
- **No telemetry, no analytics, no logging of financial data.** Application logs (if enabled) never contain account balances, transaction amounts, payee names, or any financial content.

## Architecture

### Tech Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Language** | Python 3.11+ | Batteries-included stdlib, sqlite3 built-in |
| **GUI Framework** | PySide6 (Qt 6) | Native desktop widgets, QTableView for registers, QTreeView for accounts, QtCharts for graphs |
| **Database** | SQLite via Python `sqlite3` | Single-file, zero-config, built into Python — no native compilation needed |
| **Encryption** | `cryptography` (Fernet / AES-256) | Database encryption at rest |
| **Key Derivation** | PBKDF2-HMAC-SHA256 | Passphrase → encryption key |
| **Charts** | PySide6.QtCharts | Native Qt donut, bar, and line charts |
| **Date Handling** | Python `datetime` + `calendar` | No external dependencies needed |
| **Packaging** | PyInstaller | Single-file `.app` / `.exe` distribution |

### Why This Stack?

- **Qt is what Quicken was built on.** Dense table views, collapsible tree sidebars, tabbed navigation — these are native Qt widgets. QTableView maps directly to the transaction register. QTreeView maps to the account sidebar.
- **Zero network surface.** No `npm`, no `node`, no localhost server, no HTTP stack. The application is a single process that opens a window.
- **Python `sqlite3` is built-in.** No native module compilation (`node-gyp`, `better-sqlite3`). No package manager surprises. It just works.
- **Minimal dependency chain.** The entire application depends on: `PySide6`, `cryptography`. That's it. Both are well-maintained, audited libraries.

### Data Persistence Strategy

```
<project-root>/data/                ← gitignored, per-machine data directory
├── closed-ledger.db.enc            ← Encrypted SQLite database
├── salt                            ← PBKDF2 salt (32 bytes, not secret)
├── key_check                       ← Encrypted canary value for passphrase verification
├── config.json                     ← Non-sensitive preferences (window size, theme, timeout)
└── backups/
    └── closed-ledger-2026-02-16-143022.db.enc  ← Encrypted backups
```

All data stays within the repository's `data/` directory (gitignored). Each machine that clones the repo creates its own passphrase and encrypted database on first run. Nothing is written outside the project root.

### Data Model (Core Entities)

```
┌─────────────┐     ┌──────────────────┐     ┌──────────────┐
│   Account    │────<│   Transaction    │>────│   Category   │
│              │     │                  │     │              │
│ id           │     │ id               │     │ id           │
│ name         │     │ date             │     │ name         │
│ type         │     │ payee            │     │ parent_id    │
│ group        │     │ memo             │     │ type         │
│ initial_bal  │     │ category_id      │     └──────────────┘
│ is_debt      │     │ amount           │
│ institution  │     │ check_number     │     ┌──────────────┐
│ sort_order   │     │ tag              │     │   Budget     │
└─────────────┘     │ is_reconciled    │     │              │
                     │ account_id       │     │ category_id  │
                     │ transfer_acct_id │     │ amount       │
                     └──────────────────┘     │ month / year │
                                               └──────────────┘
┌─────────────────┐
│  BillReminder   │
│ id              │
│ name / amount   │
│ category_id     │
│ account_id      │
│ frequency       │
│ next_due_date   │
│ is_auto         │
│ is_income       │
└─────────────────┘
```

## Feature Map

### Core Features (Phase 1–4)
- Master passphrase with encrypted database at rest
- Account sidebar with grouped accounts (Banking, Investing, Property & Debt, Savings Goals)
- Running account balances and Net Worth calculation
- Full transaction register with inline editing (QTableView)
- Transaction filtering (date range, type, category, payee search)
- Hierarchical categories (e.g., "Food & Dining:Restaurants")
- Home dashboard with spending donut chart (QtCharts)
- Bill & Income reminders with due date tracking

### Extended Features (Phase 5–7)
- Budget creation and tracking with monthly comparisons
- Spending tab with detailed category breakdowns
- Recurring/scheduled transactions
- Reports: Spending Over Time, Net Worth Over Time, Category Comparison
- Data import (CSV) and export (encrypted or plaintext with warning)
- Transaction search across all accounts

### Polish (Phase 8)
- Keyboard shortcuts
- Auto-lock on inactivity
- Encrypted backups with restore
- PyInstaller packaging

## Getting Started

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Run the application
python -m closed_ledger

# (Optional) Seed with demo data — will prompt for passphrase first
python -m closed_ledger --seed
```

### requirements.txt
```
PySide6>=6.6
cryptography>=42.0
```

That's the entire dependency list.

## Project Structure

```
closed_ledger/
├── __main__.py                     # Entry point: python -m closed_ledger
├── app.py                          # QApplication setup, passphrase gate, main window launch
├── security/
│   ├── __init__.py
│   ├── crypto.py                   # Fernet encryption/decryption, key derivation, file I/O
│   ├── passphrase.py               # Passphrase dialog, validation, first-run setup
│   └── session.py                  # Auto-lock timer, session state management
├── db/
│   ├── __init__.py
│   ├── connection.py               # SQLite connection manager (decrypt → open → use → close → encrypt)
│   ├── schema.py                   # CREATE TABLE statements and migrations
│   ├── seed.py                     # Demo data matching Quicken screenshots
│   └── queries/
│       ├── __init__.py
│       ├── accounts.py             # Account balance queries
│       ├── transactions.py         # Transaction CRUD, running balance
│       ├── categories.py           # Category tree queries
│       ├── bills.py                # Bill reminder queries
│       ├── budgets.py              # Budget queries
│       ├── dashboard.py            # Spending aggregation, upcoming bills
│       └── reports.py              # Report data queries
├── ui/
│   ├── __init__.py
│   ├── main_window.py              # QMainWindow: sidebar + tabs + content
│   ├── sidebar.py                  # QTreeView account sidebar
│   ├── top_nav.py                  # QTabBar navigation
│   ├── status_bar.py               # Bottom status bar
│   ├── views/
│   │   ├── __init__.py
│   │   ├── home.py                 # Dashboard: donut chart, bill reminders, budget summary
│   │   ├── register.py             # Transaction register (QTableView)
│   │   ├── spending.py             # Spending analysis view
│   │   ├── bills.py                # Bill management view
│   │   ├── budgets.py              # Budget tracking view
│   │   └── reports.py              # Reports with charts
│   ├── models/
│   │   ├── __init__.py
│   │   ├── transaction_model.py    # QAbstractTableModel for transactions
│   │   ├── account_model.py        # QStandardItemModel for account tree
│   │   └── category_model.py       # QStandardItemModel for category picker
│   ├── delegates/
│   │   ├── __init__.py
│   │   ├── currency_delegate.py    # Custom delegate for currency cells
│   │   ├── date_delegate.py        # Custom delegate for date cells
│   │   └── category_delegate.py    # Custom delegate for category dropdown
│   ├── dialogs/
│   │   ├── __init__.py
│   │   ├── account_dialog.py       # Add/edit account
│   │   ├── bill_dialog.py          # Add/edit bill reminder
│   │   ├── import_dialog.py        # CSV import wizard
│   │   └── backup_dialog.py        # Backup/restore
│   └── widgets/
│       ├── __init__.py
│       ├── donut_chart.py          # Spending donut chart (QtCharts)
│       ├── bar_chart.py            # Bar chart for reports
│       ├── line_chart.py           # Line chart for net worth
│       └── currency_label.py       # Formatted currency display widget
└── utils/
    ├── __init__.py
    ├── currency.py                 # cents ↔ display formatting
    ├── dates.py                    # Date helpers
    └── platform.py                 # Platform-specific paths, file permissions
```

## Design Language

The UI closely follows Quicken's visual conventions:

- **Color Palette**: Dark navy tab bar (`#2B579A`), white content area, light gray sidebar (`#F5F5F5`) with `#EBEBEB` header/footer bands, red for debts/negative values (`#CC0000`)
- **Typography**: System font, 11–13px base for dense data display, ALL CAPS tab labels
- **Layout**: Fixed left sidebar (240px) with vertical separator, dark navy tab bar across top of content, scrollable content area
- **Sidebar Structure**: `ACCOUNTS` header with toolbar icons (refresh/add/settings), "All Transactions" link, collapsible account groups with disclosure triangles (▾), Net Worth footer, "+ Add an Account" link
- **Tab Navigation**: HOME, SPENDING, BILLS & INCOME, PLANNING, INVESTING, PROPERTY & DEBT, REPORTS
- **Tables**: Dense row height (~30px), alternating row colors, right-aligned numbers
- **Negative values**: Displayed in red (e.g., `-$283,043`), positive in black
- **Account Groups**: Collapsible nodes with bold group headers, right-aligned totals, indented accounts with hover highlight

## License

MIT — This is an educational project. Not affiliated with Quicken Inc.
