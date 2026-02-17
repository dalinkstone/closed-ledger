# IMPLEMENTATION.md — Closed Ledger Architecture & Development Plan

> This is the guiding reference for Claude Code. It defines the security model, data layer, UI architecture, and phased build plan. **Read this entire document before beginning any phase.**

---

## Philosophy & Constraints

### Core Principles

1. **Offline and airgapped by design.** The application never opens a socket, binds a port, or makes a network call. Not even to localhost. If any imported library attempts to phone home, it must be blocked or replaced. This is non-negotiable.

2. **Encrypted at rest.** The SQLite database file on disk is always encrypted. Plaintext database content exists only in memory while the application is running. When the app closes (or locks), the in-memory database is written back encrypted and the temporary plaintext file is securely overwritten with random bytes before deletion.

3. **Data is sacred.** The encrypted database must never be deleted by any script, migration, or build step. Migrations are additive and non-destructive. All write operations use database transactions that rollback on error.

4. **Dense but readable UI.** Quicken's UI is information-dense. Financial software users want to see numbers, not whitespace. Small fonts (13–14px), tight rows (30–34px), minimal padding. But still clean and organized.

5. **Minimal dependencies.** The application depends on exactly two external packages: `PySide6` and `cryptography`. Everything else uses Python's stdlib.

### Security Requirements

These are hard requirements. Claude Code must implement ALL of them.

**S1 — No Network Access**
- The application imports no networking libraries (`requests`, `urllib`, `http`, `socket`) except for what PySide6 internally requires.
- No QNetworkAccessManager instances are created.
- On startup, verify that no listening sockets are opened by the process.
- If the application ever needs to be extended with network features in the future, they must be behind an explicit opt-in flag.

**S2 — Encrypted Database at Rest**
- The database file stored on disk (`closed-ledger.db.enc`) is always Fernet-encrypted.
- The encryption key is derived from the user's master passphrase using PBKDF2-HMAC-SHA256 with a random 32-byte salt and 600,000 iterations.
- The salt is stored in a separate file (`salt`) in the app data directory. The salt is not secret.
- A canary value (`key_check`) is encrypted with the derived key on first setup. On subsequent launches, this canary is decrypted to verify the passphrase is correct before attempting to decrypt the database.

**S3 — Passphrase Handling**
- First launch: user creates a master passphrase (minimum 8 characters, no maximum).
- Subsequent launches: user enters passphrase, which is verified against the canary.
- The passphrase is NEVER stored on disk. It exists only in memory for key derivation.
- After key derivation, the passphrase string is overwritten in memory (set to empty string / zeroed).
- Failed passphrase attempts show a generic "Incorrect passphrase" message with no hints.
- No passphrase recovery mechanism. If the passphrase is lost, data is unrecoverable. The user is warned about this on first setup.

**S4 — File Permissions**
- All files in the app data directory are created with `0o600` (owner read/write only).
- The app data directory itself is created with `0o700` (owner only).
- On Windows, equivalent ACL restrictions are applied using `icacls` or the `win32security` module if available, otherwise a warning is logged.

**S5 — Parameterized Queries**
- ALL SQL queries use parameterized placeholders (`?`). Never use f-strings, `.format()`, or `%` string interpolation to construct SQL. This is enforced by convention and code review.
- Example: `cursor.execute("SELECT * FROM accounts WHERE id = ?", (account_id,))`

**S6 — Secure Temporary Files**
- When the database is decrypted for use, the temporary plaintext `.db` file is created in a temporary directory with `0o600` permissions.
- On application close or lock, the plaintext file is overwritten with random bytes (`os.urandom`) before deletion.
- If the application crashes, the plaintext temp file may persist. On next startup, any stale temp files are detected and securely deleted before proceeding.

**S7 — Auto-Lock**
- After N minutes of no user interaction (keyboard/mouse events in the application window), the app locks.
- Lock means: the in-memory database is encrypted back to disk, the plaintext temp is securely deleted, and a passphrase dialog is shown.
- Default timeout: 15 minutes. Configurable in settings.

**S8 — Encrypted Backups**
- Backups are copies of the encrypted database file. They are already encrypted.
- Backup files are stored in the app data `backups/` directory with timestamps.
- Restore replaces the current encrypted database with a backup. Requires passphrase confirmation.
- Export to plaintext CSV is allowed but triggers a visible warning dialog: "This will create an UNENCRYPTED file containing your financial data."

---

## Data Model

### All Money Values Are Integers in Cents

`$1,234.56` → stored as `123456` (integer). This avoids floating-point rounding errors. Display formatting (`cents_to_display()`) happens only in the UI layer. All arithmetic on amounts uses integers.

### Schema (SQL)

```sql
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

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_transactions_account_date ON transactions(account_id, date);
CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category_id);
CREATE INDEX IF NOT EXISTS idx_transactions_payee ON transactions(payee);
CREATE INDEX IF NOT EXISTS idx_categories_parent ON categories(parent_id);
CREATE INDEX IF NOT EXISTS idx_bill_reminders_due ON bill_reminders(next_due_date);
```

### Amount Convention
- **Negative** = money leaving the account (payment, expense, withdrawal)
- **Positive** = money entering the account (deposit, income, refund)
- Transfers create two linked transactions: negative on source, positive on destination.

### Account Types → Groups

| Type | Group | Is Debt? |
|------|-------|----------|
| checking | banking | No |
| savings | banking | No |
| credit_card | banking | Yes |
| cash | banking | No |
| brokerage | investing | No |
| retirement_401k | investing | No |
| ira | investing | No |
| property | property_debt | No |
| vehicle | property_debt | No |
| loan | property_debt | Yes |
| mortgage | property_debt | Yes |
| other_asset | property_debt | No |
| other_liability | property_debt | Yes |

### Account Balance Computation
```sql
SELECT a.id, a.name, a.type, a.account_group, a.is_debt,
       a.initial_balance + COALESCE(SUM(t.amount), 0) AS current_balance
FROM accounts a
LEFT JOIN transactions t ON t.account_id = a.id
WHERE a.is_hidden = 0
GROUP BY a.id
ORDER BY a.account_group, a.sort_order, a.name;
```

### Running Balance in Register
```
running_balance[0] = account.initial_balance + transaction[0].amount
running_balance[i] = running_balance[i-1] + transaction[i].amount
```
Transactions sorted by `date ASC, id ASC`.

### Default Categories (Seed Data)

**Income:** Salary, Net Salary Spouse, Interest Income, Dividend Income, Bonus

**Expense (Parent → Children):**
- Food & Dining → Restaurants, Groceries, Coffee Shops
- Auto & Transport → Auto Pay, Gas & Fuel, Insurance, Parking, Public Transit
- Home → Mortgage, Rent, Home Services, Lawn & Garden, Home Improvement
- Bills & Utilities → Electric, Gas, Water, Internet, Phone, Cable, Trash
- Entertainment → Movies, Music, Games, Streaming
- Health & Fitness → Gym, Doctor, Pharmacy, Dentist
- Shopping → Clothing, Electronics, General
- Cash & ATM
- Personal Care
- Education
- Gifts & Donations
- Travel
- Taxes → Federal Tax, State Tax, Property Tax

**Transfer:** Transfer, Credit Card Payment

### Seed Accounts (from Screenshots)
- Family Checking ($1,491), My Checking ($2,832), My Savings ($13,200), My Credit Card (-$5,325)
- Brokerage ($95,164), 401(k) ($82,930)
- Car Value ($20,000), House ($800,000), Auto Loan (-$18,288), Home Loan (-$283,043), Loan (-$339,924)
- Dream Home Fund ($4,050), Vacation Fund ($700)

### Seed Transactions (250+, last 6 months)
Payees from screenshots: Car Payment ($300), ATM Withdrawal ($120), Bo-bo- Chili And Ribs ($75), GameStop ($12.50), Trader Joe's ($100), Credit Card Payment ($750), Spouse Paycheck ($2,600), Restaurant ($75), Grocery Store ($100), Gym Membership ($100), Netflix ($12.50), Gas & Electric ($250), Mortgage Payment ($1,400), Water Bill ($10), Yard Work ($25), Garden Bill ($12.50), Paychecks (~$3,500 biweekly)

---

## UI Architecture (Qt)

### Main Window Structure

```
QMainWindow
├── QHBoxLayout (central widget)
│   ├── SidebarWidget (QWidget, fixed 240px, bg #F5F5F5)
│   │   ├── Header bar (bg #EBEBEB): "▾ ACCOUNTS" + [↻] [+] [⚙] toolbar buttons
│   │   ├── QScrollArea
│   │   │   ├── QPushButton "All Transactions" (blue link)
│   │   │   └── Account groups (▾ disclosure + group name + total, indented accounts)
│   │   ├── Net Worth footer (bg #EBEBEB): "Net Worth" + formatted amount
│   │   └── QPushButton "+ Add an Account" (blue link)
│   ├── QFrame (VLine separator, #D0D0D0)
│   └── QWidget (right panel, bg white)
│       ├── QTabBar (bg #2B579A navy, ALL CAPS white text, 36px height)
│       │   Tabs: HOME | SPENDING | BILLS & INCOME | PLANNING | INVESTING | PROPERTY & DEBT | REPORTS
│       └── QStackedWidget (content pages, switched by tab)
│           ├── HomeView (dashboard)
│           ├── RegisterView (transaction table)
│           ├── SpendingView
│           ├── BillsView / BudgetsView
│           └── ReportsView
└── QStatusBar (bg #F0F0F0): "N Transactions" | "Current Balance: X" | "Ending Balance: X"
```

### Transaction Register (QTableView + QAbstractTableModel)

The register is the most important view. It uses Qt's Model/View architecture:

- **TransactionTableModel** (QAbstractTableModel): holds transaction data, implements `data()`, `setData()`, `flags()`, `headerData()`. Returns formatted display values. Handles edit operations.
- **QTableView**: displays the model. Column widths set explicitly to match Quicken layout.
- **Custom Delegates**: CurrencyDelegate for Payment/Deposit/Balance columns (right-aligned, formatted), DateDelegate for the Date column, CategoryDelegate for a combobox dropdown.

Column layout (matching Screenshot 1):
```
| Date (90px) | Check# (60px) | Payee (stretch) | Memo (150px) | Category (200px) | Tag (80px) | Payment (95px) | Deposit (95px) | Balance (100px) |
```

### Color Palette

```python
COLORS = {
    # Sidebar
    'sidebar_bg': '#F5F5F5',
    'sidebar_header_bg': '#EBEBEB',
    # Tab bar (dark navy, matching Quicken reference images)
    'tab_bar_bg': '#2B579A',
    'tab_selected_bg': '#1E4270',
    'tab_accent': '#5BA3E6',
    'tab_hover_bg': '#34629F',
    'tab_text': '#FFFFFF',
    # Content
    'content_bg': '#FFFFFF',
    'text_primary': '#333333',
    'text_secondary': '#555555',
    'text_negative': '#CC0000',
    'text_positive': '#006600',
    'link_color': '#2B579A',
    # Table rows
    'row_alt': '#F0F5FA',
    'row_hover': '#E3EDF7',
    'row_selected': '#D0E0F0',
    'border_light': '#E0E0E0',
    'border_medium': '#D0D0D0',
    # Chart colors (per category)
    'chart_home': '#2E8B57',
    'chart_auto': '#6A5ACD',
    'chart_bills': '#DB7093',
    'chart_food': '#FF8C00',
    'chart_cash': '#4169E1',
    'chart_health': '#CD5C5C',
    'chart_entertainment': '#20B2AA',
    'chart_tax': '#808000',
    'chart_other': '#B0C4DE',
}
```

### UI Reference from Screenshots

**Screenshot 1 — Transaction Register:**
- Dense table, alternating white/#F0F5FA rows
- Date format: M/D/YYYY (8/5/2013)
- Currency in table: no $ sign, just "300.00" and "3,556.31"
- Status bar: "647 Transactions" | "Current Balance: 2,506.31" | "Ending Balance: 543.81"
- Filter bar: date range, type, status dropdowns + Reset button

**Screenshot 2 — Home Dashboard (Mac):**
- Donut chart "Spending By Category" with $4,463.49 total
- Bill reminders: Cable Bill (-$150), Car Insurance (-$150), Cell Phone (-$90), Credit Card Payment (-$750), Internet Service (-$65), Transfer To Savings (-$200)
- Budget: "$2,581 left"

**Screenshot 3 — Home Dashboard (Windows 2017):**
- "TOTAL SPENDING $3,954" in donut center
- Legend: Home, Auto & Transport, Bills & Utilities, Food & Dining, Cash & ATM, Health & Fitness, Entertainment
- "WHAT'S LEFT $823"
- Bill reminders with Overdue (red) and Auto badges

---

## Phase Overview

| Phase | Name | What Gets Built |
|-------|------|-----------------|
| 1 | Foundation | Project structure, security layer, database, schema, seed, passphrase gate, empty main window |
| 2 | Account Sidebar | QTreeView sidebar with live balances, groups, net worth, add/edit account dialogs |
| 3 | Transaction Register | QTableView register, model/view/delegate, inline editing, filters, status bar |
| 4 | Home Dashboard | Donut chart, bill reminders widget, budget summary, all using QtCharts |
| 5 | Categories & Budgets | Category tree management, budget tracking with progress bars |
| 6 | Bills & Scheduling | Bill CRUD, mark-as-paid flow, recurring date advancement |
| 7 | Reports | Spending over time, net worth, income vs expenses, category breakdown charts |
| 8 | Polish | CSV import/export, search, keyboard shortcuts, auto-lock, backup/restore, packaging |

---

## Testing Strategy

After every phase, run these checks:

**Security:**
- `lsof -i -P -n | grep python` shows NO listening sockets
- Database file on disk is not valid SQLite (encrypted): `file data/closed-ledger.db.enc` should not say "SQLite"
- Incorrect passphrase is rejected with generic message
- Data directory permissions are `0o700`, files are `0o600`

**Data Integrity:**
- Sum of transaction amounts + initial balance = sidebar balance for each account
- Net worth = sum of all account balances
- Last running balance in register = account's sidebar balance
- No orphaned transactions referencing deleted accounts
