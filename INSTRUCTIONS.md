# INSTRUCTIONS.md — Claude Code Workflow

> **How to use this file**: Each phase is a separate Claude Code session. Copy-paste the prompt, let it build, test with the checklist, fix issues, commit, move on.

---

## Your Workflow

```
1. Open a NEW Claude Code session
2. Paste the PROMPT for that phase
3. Let Claude Code work
4. Run the TESTING CHECKLIST yourself
5. If something fails → paste the FIX PROMPT with the error
6. Once all tests pass → commit and start next phase
```

### Fix Prompt Template

```
I'm building Closed Ledger (Phase [N]). Read IMPLEMENTATION.md for full context.

This is failing:
[what's wrong]

Expected:
[what should happen]

Fix this without changing anything unrelated.
```

---

## Phase 1: Foundation

> **Goal**: Project structure, security layer (encryption + passphrase), database with schema and seed data, and a passphrase-gated empty main window.

### PROMPT — Copy this entire block into Claude Code:

```
I'm starting a project called "Closed Ledger" — a native desktop personal finance app
modeled after Quicken Classic. It is built with Python, PySide6, and SQLite. There is NO
web server, no HTTP, no network of any kind.

Read README.md and IMPLEMENTATION.md in this directory. They define the full architecture,
security model, data model, and phased plan. Read them completely before writing any code.

Build Phase 1 — Foundation. Everything below must be implemented:

1. PROJECT STRUCTURE
   Create the full directory tree from README.md "Project Structure".
   Create requirements.txt with exactly: PySide6>=6.6 and cryptography>=42.0
   Create closed_ledger/__main__.py as the entry point (python -m closed_ledger).
   Create a .gitignore that ignores: __pycache__, *.pyc, venv/, .venv/, *.db, *.db.enc,
   salt, key_check (never commit encrypted data or keys to git).

2. SECURITY: ENCRYPTION MODULE (closed_ledger/security/crypto.py)
   Implement these functions:
   - derive_key(passphrase: str, salt: bytes) -> bytes:
     Uses PBKDF2-HMAC-SHA256 with 600,000 iterations. Returns a Fernet-compatible key
     (base64-encoded 32-byte key).
   - generate_salt() -> bytes: returns 32 random bytes via os.urandom.
   - encrypt_file(source_path: str, dest_path: str, key: bytes):
     Reads source file, encrypts with Fernet(key), writes to dest_path.
     Sets dest_path permissions to 0o600.
   - decrypt_file(source_path: str, dest_path: str, key: bytes):
     Reads encrypted file, decrypts with Fernet(key), writes to dest_path.
     Sets dest_path permissions to 0o600.
   - secure_delete(file_path: str):
     Overwrites file content with os.urandom(file_size), then deletes it.
     If file doesn't exist, silently returns.
   - create_key_check(key: bytes, path: str):
     Encrypts a known canary string ("CLOSED_LEDGER_KEY_CHECK") with the key,
     writes to path. Used to verify passphrase on subsequent launches.
   - verify_key_check(key: bytes, path: str) -> bool:
     Decrypts the file at path, returns True if it matches the canary string.
     Returns False on any decryption error (wrong key).

3. SECURITY: PASSPHRASE DIALOG (closed_ledger/security/passphrase.py)
   Two Qt dialogs:
   - FirstRunDialog: shown when no salt/key_check files exist yet.
     Has: passphrase input (QLineEdit, echo mode Password), confirm input,
     minimum 8 characters validation, a warning label: "This passphrase encrypts your
     financial data. If you lose it, your data CANNOT be recovered. There is no reset."
     OK button only enabled when both fields match and >= 8 chars.
   - UnlockDialog: shown on subsequent launches.
     Has: passphrase input (QLineEdit, echo mode Password), OK button.
     If passphrase is wrong (verify_key_check fails), show "Incorrect passphrase" in
     red text. No hints. No "forgot password" link.
   Both dialogs: no close/minimize/maximize buttons. Must enter passphrase or quit.
   Both dialogs: passphrase string is overwritten (set to '') after key derivation.

4. SECURITY: PLATFORM PATHS (closed_ledger/utils/platform.py)
   - get_app_data_dir() -> Path: returns the platform-appropriate directory:
     macOS: ~/Library/Application Support/closed-ledger/
     Linux: ~/.local/share/closed-ledger/
     Windows: %APPDATA%/closed-ledger/
   - ensure_app_data_dir(): creates the directory with 0o700 permissions if it doesn't exist.
   - get_db_encrypted_path() -> Path: app_data / "closed-ledger.db.enc"
   - get_db_temp_path() -> Path: tempfile in system temp dir with random name
   - get_salt_path() -> Path: app_data / "salt"
   - get_key_check_path() -> Path: app_data / "key_check"
   - get_backups_dir() -> Path: app_data / "backups"

5. DATABASE: CONNECTION MANAGER (closed_ledger/db/connection.py)
   Implement a DatabaseManager class that:
   - __init__(self, encryption_key: bytes): stores the key, initializes state
   - open(self): decrypts the .db.enc file to a temp path, opens sqlite3 connection,
     enables WAL mode and foreign_keys. If no .db.enc exists yet, creates a fresh database.
   - close(self): commits any pending transaction, closes sqlite3 connection,
     encrypts the temp db back to .db.enc, then calls secure_delete on the temp file.
   - get_connection(self) -> sqlite3.Connection: returns the active connection.
   - Cleans up stale temp files on open (from previous crashes).
   - Context manager support (__enter__, __exit__).

6. DATABASE: SCHEMA (closed_ledger/db/schema.py)
   - initialize_schema(conn: sqlite3.Connection): executes ALL CREATE TABLE and CREATE INDEX
     statements from IMPLEMENTATION.md exactly as specified. Uses IF NOT EXISTS so it's
     safe to call on every startup. This IS the migration system — additive CREATE IF NOT EXISTS.
   - get_schema_version(conn) and set_schema_version(conn, version): for future migrations
     using PRAGMA user_version.

7. DATABASE: SEED (closed_ledger/db/seed.py)
   - seed_database(conn): populates demo data matching the Quicken screenshots.
     Categories (40+), accounts (13), transactions (250+), bill reminders (6), budgets (7).
     Follow the exact specification in IMPLEMENTATION.md. Uses parameterized queries ONLY.
   - is_seeded(conn) -> bool: checks if data already exists.
   - Seed transactions should span the last 6 months using realistic dates, amounts, and
     the exact payee names from the screenshots.

8. APPLICATION ENTRY POINT (closed_ledger/app.py and __main__.py)
   The startup flow is:
   a) Create QApplication
   b) ensure_app_data_dir()
   c) Check if salt and key_check files exist:
      - If no: show FirstRunDialog → get passphrase → generate salt → derive key →
        create key_check → create fresh database → initialize schema
      - If yes: show UnlockDialog → get passphrase → load salt → derive key →
        verify against key_check → if wrong, show error, retry
   d) Open DatabaseManager with the derived key
   e) If --seed flag passed: run seed_database
   f) Show MainWindow (empty shell for now)
   g) On close: DatabaseManager.close() encrypts and cleans up

   __main__.py: just calls app.main() with sys.argv

9. MAIN WINDOW SHELL (closed_ledger/ui/main_window.py)
   A QMainWindow with:
   - Window title: "Closed Ledger"
   - Left side: placeholder QWidget (240px wide, gray background #F5F5F5) with
     QLabel "ACCOUNTS" — this will become the sidebar in Phase 2
   - Right side: QTabBar across the top (steel blue #4A7AB5 background, white text)
     with tabs: Home, Spending, Bills, Planning, Investing, Property & Debt, Reports
   - Below tab bar: QStackedWidget with placeholder QLabels for each tab
   - QStatusBar at the bottom
   - Window size: 1200x800 default, remembers last position/size in config.json
   - NO NETWORK CALLS ANYWHERE. Verify this.

After building, test that: `python -m closed_ledger` launches, shows passphrase dialog,
creates encrypted database, and shows the main window shell.
If --seed flag: `python -m closed_ledger --seed` populates the database.

CRITICAL SECURITY RULES:
- NEVER use string formatting/interpolation in SQL. ALWAYS use ? placeholders.
- NEVER store the passphrase to disk.
- NEVER leave a plaintext .db file on disk after the app closes.
- NEVER open any network socket or port.
- ALL file creates must set restrictive permissions.
```

### TESTING CHECKLIST

```
□ python -m closed_ledger runs without errors
□ First launch shows FirstRunDialog with passphrase + confirm fields
□ Cannot proceed with passphrase < 8 characters
□ Cannot proceed when passphrase and confirm don't match
□ After setting passphrase, main window appears
□ Files exist in app data dir:
  ls -la ~/.local/share/closed-ledger/  (or equivalent for your OS)
  → closed-ledger.db.enc, salt, key_check
□ File permissions are restrictive:
  stat -c '%a' ~/.local/share/closed-ledger/closed-ledger.db.enc  → 600
  stat -c '%a' ~/.local/share/closed-ledger/  → 700
□ Encrypted DB is NOT readable as SQLite:
  file ~/.local/share/closed-ledger/closed-ledger.db.enc  → should NOT say "SQLite"
  sqlite3 ~/.local/share/closed-ledger/closed-ledger.db.enc ".tables"  → should error
□ Close the app, relaunch → shows UnlockDialog
□ Enter wrong passphrase → shows "Incorrect passphrase" in red, does not unlock
□ Enter correct passphrase → main window appears
□ No temp .db files left after clean close:
  ls /tmp/*closed*  → should find nothing
□ Main window has sidebar placeholder (gray) and tab bar (steel blue)
□ Tabs are visible and clickable (content is placeholder text)
□ python -m closed_ledger --seed populates data:
  After seeding, close app, relaunch, unlock, and the app should start normally
□ SECURITY: No network listeners:
  While app is running: lsof -i -P -n | grep python → NO results (or none from this process)
□ No TypeErrors or import errors in the terminal
```

### COMMIT

```bash
git add -A
git commit -m "Phase 1: Foundation — security layer, encrypted database, passphrase gate, window shell"
```

---

## Phase 2: Account Sidebar

> **Goal**: QTreeView sidebar with real balances from the database, collapsible groups, net worth, add/edit account dialogs.

### PROMPT

```
This is the Closed Ledger project — a native desktop Quicken clone.
Read IMPLEMENTATION.md for the full architecture, data model, and UI specs.

Phase 1 is complete: the app has a security layer (encrypted DB, passphrase gate),
SQLite database with schema and seed data, and a main window shell.

Build Phase 2 — Account Sidebar.

1. ACCOUNT QUERIES (closed_ledger/db/queries/accounts.py)
   All queries use parameterized ? placeholders. No string formatting in SQL.
   - get_accounts_with_balances(conn) -> list[dict]:
     Returns all non-hidden accounts with computed current_balance.
     SQL: SELECT a.*, (a.initial_balance + COALESCE(SUM(t.amount), 0)) AS current_balance
     FROM accounts a LEFT JOIN transactions t ON t.account_id = a.id
     WHERE a.is_hidden = 0 GROUP BY a.id ORDER BY a.account_group, a.sort_order, a.name
   - get_account_groups(conn) -> list[dict]:
     Groups accounts by account_group. Returns list of:
     { group: str, label: str, accounts: list, total: int (cents) }
     Labels: banking→"Banking", investing→"Investing", property_debt→"Property & Debt",
     savings_goals→"Savings Goals"
   - get_net_worth(conn) -> int: sum of all current balances (in cents)
   - get_account_by_id(conn, account_id) -> dict
   - create_account(conn, data: dict) -> int (new id)
   - update_account(conn, account_id, data: dict)
   - delete_account(conn, account_id): only if no transactions reference it

2. SIDEBAR WIDGET (closed_ledger/ui/sidebar.py)
   Replace the placeholder sidebar with a real QWidget containing:
   - Header: QLabel "ACCOUNTS" (bold) with toolbar: refresh button, + button, settings button
   - "All Transactions" clickable item at the top (QLabel styled as link or flat QPushButton)
   - QTreeView with a QStandardItemModel showing account groups and accounts:
     Root items: "Banking ($12,199)", "Investing ($178,094)", etc. (bold, with group total)
     Child items: "  Family Checking  $1,491", "  My Checking  $2,832", etc.
     Each child item stores the account_id in Qt.UserRole for click handling.
   - Clicking a group item expands/collapses its children.
   - Clicking an account item emits a signal with the account_id.
   - Negative balances displayed in red (#CC0000).
   - Active/selected account has highlighted background (#D0E0F0).
   - Below the tree: QLabel "Net Worth" with formatted total, bold.
   - Below net worth: QPushButton "+ Add an Account" (flat, link-styled)

3. CURRENCY UTILITY (closed_ledger/utils/currency.py)
   - cents_to_display(cents: int, show_cents=True) -> str:
     123456 → "$1,234.56" (with show_cents) or "$1,235" (without)
     Negative: -523400 → "-$5,234.00" (red in UI, but this function just formats the string)
   - display_to_cents(text: str) -> int:
     "$1,234.56" or "1234.56" or "1,234.56" → 123456
   - cents_to_table(cents: int) -> str:
     For table cells (no $ sign): 123456 → "1,234.56". Negative: -30000 → "300.00"
     (Note: in the register, Payment column shows positive display of negative amounts)

4. ADD ACCOUNT DIALOG (closed_ledger/ui/dialogs/account_dialog.py)
   QDialog with:
   - Account Name: QLineEdit (required)
   - Account Type: QComboBox with all types from schema
   - Financial Institution: QLineEdit (optional)
   - Opening Balance: QLineEdit with dollar input, converts to cents on save
   - Auto-sets account_group and is_debt based on type selection
     (use mapping from IMPLEMENTATION.md)
   - OK/Cancel buttons. Validates name is not empty.
   - Works in both add and edit mode (pre-fills fields when editing).

5. WIRING
   - MainWindow receives account_selected signal from sidebar → switches to register view
     (placeholder for now, just shows "Selected account: {name}" in the content area)
   - "+ Add an Account" button opens AccountDialog → on accept, inserts via create_account,
     refreshes sidebar
   - Sidebar refreshes on any data change (account add/edit/delete, transaction create/delete)
   - Expose a refresh_sidebar() method on the sidebar that re-queries and rebuilds the tree model

SECURITY REMINDER: All database queries use parameterized ? placeholders.
No string interpolation in SQL. Verify this in every query function.
```

### TESTING CHECKLIST

```
□ Sidebar shows four account groups: Banking, Investing, Property & Debt, Savings Goals
□ Each group is expandable/collapsible by clicking
□ Group totals are correct sums of their child accounts
□ Account balances match expected seed data values (not $0, not unreasonable)
□ Negative balances (credit card, loans, mortgage) display in red
□ Clicking an account highlights it and shows its name in the content area
□ "All Transactions" is clickable at the top
□ Net Worth at bottom = sum of all account balances
□ "+ Add an Account" opens a dialog
□ Creating a test account → appears in correct group, balance shows correctly
□ Editing an account → changes reflected in sidebar
□ Deleting account with no transactions → removed from sidebar
□ Deleting account with transactions → shows error
□ SECURITY: grep -rn "f'" closed_ledger/db/ and grep -rn '\.format' closed_ledger/db/
  → should find NO string interpolation in SQL queries (only in display strings)
```

### COMMIT

```bash
git add -A
git commit -m "Phase 2: Account Sidebar — tree view, live balances, account CRUD"
```

---

## Phase 3: Transaction Register

> **Goal**: QTableView register with full CRUD, inline editing via delegates, filters, running balance, status bar. This is the biggest phase.

### PROMPT

```
This is the Closed Ledger project — a native desktop Quicken clone.
Read IMPLEMENTATION.md for full architecture. Focus on Phase 3 specs and UI Reference.

Phases 1–2 are complete: encrypted DB, passphrase gate, sidebar with live balances.

Build Phase 3 — Transaction Register. This is the core of the application.

1. TRANSACTION QUERIES (closed_ledger/db/queries/transactions.py)
   All queries use parameterized ? placeholders. NEVER use f-strings in SQL.
   - get_transactions_for_account(conn, account_id, filters=None) -> list[dict]:
     Returns transactions with: all transaction fields, category display name
     ("Parent:Child" format via JOIN), running_balance computed in Python after fetch
     (sort by date ASC, id ASC, accumulate from initial_balance).
     filters: optional dict with date_start, date_end, type (payment/deposit/transfer),
     reconciled (bool). For account_id="all": all accounts, no running balance.
   - create_transaction(conn, data: dict) -> int:
     Inserts transaction. If transfer (transfer_account_id set), creates paired transaction.
     Returns new transaction id.
   - update_transaction(conn, txn_id, data: dict):
     Updates transaction. If transfer, updates pair.
   - delete_transaction(conn, txn_id):
     Deletes transaction. If transfer, deletes pair.
   - get_payee_suggestions(conn, prefix: str) -> list[str]:
     SELECT DISTINCT payee WHERE payee LIKE ? (with parameterized LIKE)
   - get_transaction_stats(conn, account_id) -> dict:
     Returns { count, current_balance, ending_balance } for status bar.

2. CATEGORY QUERIES (closed_ledger/db/queries/categories.py)
   - get_all_categories(conn) -> list[dict]:
     Returns all categories with display_name = "Parent:Child" via self-join
   - get_category_tree(conn) -> list[dict]:
     Hierarchical: [{ id, name, type, children: [{id, name, ...}] }]

3. TRANSACTION TABLE MODEL (closed_ledger/ui/models/transaction_model.py)
   Subclass QAbstractTableModel:
   - Columns: Date, Check#, Payee, Memo, Category, Tag, Payment, Deposit, Balance
   - data() returns formatted display values:
     Date: M/D/YYYY format
     Payment: positive display of negative amount, no $ sign (e.g., "300.00")
     Deposit: positive amount, no $ sign
     Balance: running balance, no $ sign
   - setData() handles inline editing: converts user input back to storage format
   - flags(): cells are editable (except Balance), selectable
   - Support for an empty "new transaction" row at the bottom
   - Emits dataChanged when transactions are modified

4. CUSTOM DELEGATES (closed_ledger/ui/delegates/)
   - CurrencyDelegate: for Payment, Deposit, Balance columns. Right-aligns text.
     Creates QLineEdit editor that accepts decimal dollar input.
     Formats display as "1,234.56" (no $ sign, tabular alignment).
     Negative values (Balance column only) shown in red.
   - DateDelegate: for Date column. Creates QDateEdit editor.
     Displays as M/D/YYYY. Default new date: today.
   - CategoryDelegate: for Category column. Creates QComboBox editor
     populated from get_category_tree(). Shows "Parent:Child" display text.
     Searchable/filterable via QCompleter.

5. REGISTER VIEW (closed_ledger/ui/views/register.py)
   A QWidget containing:
   - Header: QLabel with account name in large bold text
   - FilterBar: QHBoxLayout with three QComboBoxes + QPushButton "Reset":
     Date Range: All Dates, This Month, Last Month, This Year, Last Year, Last 12 Months
     Type: Any Type, Payment, Deposit, Transfer
     Status: All Transactions, Unreconciled, Reconciled
   - QTableView connected to TransactionTableModel:
     Set column widths matching IMPLEMENTATION.md spec
     Alternating row colors: white and #F0F5FA
     Row height: ~30px
     Set delegates for Date, Category, Payment, Deposit, Balance columns
     Enable editing on double-click or Enter key
   - New transaction row at bottom (always present, styled differently)
   - Context menu on right-click: Edit, Delete (with confirmation)
   - Keyboard: Enter saves edit, Escape cancels, Tab moves between cells, Delete key with confirmation

6. STATUS BAR (closed_ledger/ui/status_bar.py)
   Update the QStatusBar at bottom of main window when register is active:
   Left: "{N} Transactions"
   Center: "Current Balance: {formatted}"
   Right: "Ending Balance: {formatted}"

7. WIRING
   - Clicking an account in sidebar → switches QStackedWidget to register view,
     loads that account's transactions
   - "All Transactions" → loads all transactions (no running balance column)
   - After any transaction CRUD → refresh sidebar balances AND register data
   - Filter changes → re-query and reload model

SECURITY: Verify NO string interpolation in any SQL query. All use ? placeholders.
The payee suggestions query must use parameterized LIKE: WHERE payee LIKE ? || '%'
OR build the LIKE pattern in Python and pass as parameter: cursor.execute("... LIKE ?", (prefix + "%",))
```

### TESTING CHECKLIST

```
□ Click "Family Checking" in sidebar → register loads with transactions
□ Page header shows "Family Checking"
□ Table columns: Date, Check#, Payee, Memo, Category, Tag, Payment, Deposit, Balance
□ Date format is M/D/YYYY (not ISO, not MM/DD/YYYY)
□ Payment/Deposit show no $ sign, just "300.00" format
□ Alternating row colors visible
□ Running balance: first row = initial balance + first amount
□ Running balance: LAST row matches sidebar balance for that account
□ Status bar shows correct transaction count and balance values
□ FILTER: "This Month" filters to current month only
□ FILTER: "Payment" shows only expense transactions
□ FILTER: Reset restores all transactions
□ EDIT: Double-click a payee → editable, change it, press Enter → saved
□ EDIT: Escape cancels edit
□ NEW: Bottom row accepts new transaction → Enter creates it → sidebar updates
□ DELETE: Right-click → Delete → confirmation → row removed → sidebar updates
□ Category dropdown shows hierarchical "Parent:Child" entries
□ "All Transactions" view shows transactions from all accounts
□ SECURITY: grep -rn "f'" closed_ledger/db/ shows no SQL interpolation
```

### COMMIT

```bash
git add -A
git commit -m "Phase 3: Transaction Register — QTableView, model/view/delegate, CRUD, filters"
```

---

## Phase 4: Home Dashboard

> **Goal**: Dashboard with donut chart, bill reminders, budget summary using QtCharts.

### PROMPT

```
This is the Closed Ledger project. Read IMPLEMENTATION.md for full context.
Focus on Phase 4 specs and the UI Reference screenshots description.

Phases 1–3 complete: encrypted DB, sidebar, full transaction register.

Build Phase 4 — Home Dashboard. This is the view shown when "Home" tab is active.

1. DASHBOARD QUERIES (closed_ledger/db/queries/dashboard.py)
   All queries use ? placeholders. No string interpolation in SQL.
   - get_spending_by_category(conn, date_start, date_end) -> list[dict]:
     Aggregate expense transactions (amount < 0) by TOP-LEVEL category.
     If transaction has child category, group under parent.
     Exclude transfers. Return { category_name, total_cents (positive), color }.
     Map categories to chart colors from IMPLEMENTATION.md.
   - get_upcoming_bills(conn, days_ahead) -> list[dict]:
     Bills where next_due_date <= today + days_ahead.
     Include status: 'overdue' / 'due_soon' / 'upcoming'.
   - get_total_spending(conn, date_start, date_end) -> int (cents, positive)
   - get_whats_left(conn) -> int:
     Sum of budgets for current month minus sum of expenses this month.

2. DONUT CHART WIDGET (closed_ledger/ui/widgets/donut_chart.py)
   Uses PySide6.QtCharts:
   - QPieSeries with setHoleSize(0.55) for donut effect
   - Each slice colored by category color
   - Slice labels show category name on hover
   - Center text overlay (QLabel or custom paint): "TOTAL SPENDING\n$X,XXX"
   - Legend on right side with category + color
   - setAnimationOptions(QChart.AllAnimations)
   - update_data(spending_data: list[dict]) method to refresh

3. HOME VIEW (closed_ledger/ui/views/home.py)
   QWidget with QVBoxLayout containing three card-style sections:

   SECTION A: Spending By Category
   - QGroupBox or framed widget with header "Spending By Category"
   - QComboBox in header: "Last Month", "This Month", "Last 30 Days", "Last 3 Months"
   - DonutChartWidget showing spending data
   - QPushButton "Examine Your Spending" linking to Spending tab

   SECTION B: Bill & Income Reminders
   - Header "Bill & Income Reminders" with QComboBox: "Next 7 Days", "Next 14 Days", "Next 30 Days"
   - "TODAY" label with current date formatted
   - QListWidget or custom widget showing bills:
     Each row: status icon (colored circle), bill name, "Due in X days"/"Overdue", amount in red
   - Amounts: -$150.00 format in red

   SECTION C: Budget Summary
   - Header "Budget"
   - Large QLabel: "$X,XXX left" in green (positive) or red (negative)
   - Subtitle: "in All Categories"
   - If no budgets: "Set up your budget →"

4. WIRING
   - "Home" tab in QTabBar → shows HomeView in QStackedWidget
   - Combo box changes re-query and refresh data
   - This is the default view on app launch

SECURITY: All queries use ? placeholders. No network calls in chart rendering.
```

### TESTING CHECKLIST

```
□ Home tab shows "Overview" or spending chart as default view
□ Donut chart renders with colored segments (not empty, not erroring)
□ Total spending amount shown in center of donut
□ Changing date range combo updates the chart
□ Bill reminders section shows seeded bills with correct amounts
□ Bills show "Due in X days" or "Overdue by X days" correctly
□ Overdue bills have red indicator
□ Budget section shows dollar amount or "Set up your budget"
□ All amounts properly formatted with $ signs and commas
□ Chart colors consistent per category
□ No console errors / no crashes on tab switch
```

### COMMIT

```bash
git add -A
git commit -m "Phase 4: Home Dashboard — donut chart, bill reminders, budget summary"
```

---

## Phase 5: Categories & Budgets

### PROMPT

```
Closed Ledger project. Read IMPLEMENTATION.md. Phases 1–4 complete.

Build Phase 5 — Categories & Budgets.

1. CATEGORY MANAGEMENT
   Add a category management view accessible from a menu or settings:
   - QTreeView showing all categories in hierarchy
   - Each row: category name, type badge (income/expense/transfer), transaction count
   - Add Category: QDialog with name, type QComboBox, optional parent QComboBox
   - Edit/Rename: double-click or context menu
   - Delete: only if no transactions reference it. Show count if in use and block.
   - API: add_category, update_category, delete_category in queries/categories.py
   ALL queries use ? placeholders.

2. BUDGET PAGE (Budgets tab in QStackedWidget)
   - Month navigation: QPushButton ← | QLabel "Month YYYY" | QPushButton →
   - Summary: "Budgeted: $X | Spent: $X | Remaining: $X"
   - QTableView or QTreeWidget with rows per budgeted category:
     Category | Budgeted | Actual Spent | Remaining | Progress Bar
   - Progress bar: QProgressBar styled green ≤75%, yellow 75-100%, red >100%
   - Budgeted column editable (double-click to enter amount)
   - Unbudgeted categories with spending also shown (with $0 budget)
   - Budget CRUD: queries/budgets.py with create/update/delete, all ? parameterized

3. DASHBOARD INTEGRATION
   Update the Budget summary widget on the home dashboard to show real computed data.

SECURITY: All queries use ? placeholders. Verify with grep.
```

### TESTING CHECKLIST

```
□ Category management shows full category tree
□ Can add a new category with parent
□ Can rename a category
□ Delete blocked for categories with transactions
□ Budgets tab shows current month data
□ Budget table: correct category, budgeted, actual, remaining values
□ Progress bars colored correctly (green/yellow/red)
□ Can edit budget amount by double-clicking
□ Month navigation changes displayed data
□ Dashboard budget widget shows real "$ left" amount
□ SECURITY: grep -rn "f'" closed_ledger/db/ → no SQL interpolation
```

### COMMIT

```bash
git add -A
git commit -m "Phase 5: Categories & Budgets — category CRUD, budget tracking, progress bars"
```

---

## Phase 6: Bills & Scheduling

### PROMPT

```
Closed Ledger project. Read IMPLEMENTATION.md. Phases 1–5 complete.

Build Phase 6 — Bills & Scheduling.

1. BILLS VIEW (Bills tab)
   - Three sections: OVERDUE (red), DUE SOON (orange, 7 days), UPCOMING (gray)
   - Each bill: status icon, name, amount, due date, frequency badge, "Auto" badge
   - Action buttons: "Mark as Paid" (green), "Skip" (gray), "Edit" (pencil)

2. MARK AS PAID
   - QDialog with pre-filled: amount, date (today), account, category
   - User can adjust amount/date
   - On confirm: create_transaction on linked account with bill's amount/category/date,
     then advance next_due_date: weekly→+7d, biweekly→+14d, monthly→+1mo,
     quarterly→+3mo, annually→+1yr, once→remove bill
   - Refresh bills list, sidebar balances, dashboard

3. SKIP: advance due date without creating transaction

4. BILL CRUD: QDialog for add/edit with all fields. Delete with confirmation.
   queries/bills.py: all CRUD functions with ? parameterized queries.

SECURITY: All queries use ? placeholders. No string interpolation.
```

### TESTING CHECKLIST

```
□ Bills tab shows all 6 seeded bills in correct sections
□ Mark as Paid → creates transaction visible in register
□ Mark as Paid → due date advances correctly
□ Mark as Paid → sidebar balance updates
□ Skip → due date advances, no transaction created
□ Add/Edit/Delete bill all work
□ Dashboard bill reminders stay in sync
□ SECURITY: All queries parameterized
```

### COMMIT

```bash
git add -A
git commit -m "Phase 6: Bills & Scheduling — bill CRUD, mark as paid, recurring dates"
```

---

## Phase 7: Reports

### PROMPT

```
Closed Ledger project. Read IMPLEMENTATION.md. Phases 1–6 complete.

Build Phase 7 — Reports. Uses PySide6.QtCharts for all charts.

Reports tab with sub-navigation (QComboBox or sub-tabs) for 4 report types:

1. SPENDING OVER TIME: QBarSeries showing monthly expense totals, QValueAxis for $
2. NET WORTH OVER TIME: QLineSeries tracking month-end net worth
3. INCOME VS EXPENSES: grouped QBarSeries (green=income, red=expenses per month)
4. CATEGORY BREAKDOWN: table + reuse donut chart, sorted by amount desc, expandable subcategories

All reports: QComboBox date range (Last 6 Mo, 12 Mo, This Year, Last Year, All Time).
queries/reports.py: all query functions with ? parameterized queries.

Charts: QChartView with QChart, proper axis labels ($ formatting), tooltips, legends.

SECURITY: All queries use ? placeholders. No network calls.
```

### TESTING CHECKLIST

```
□ Reports tab loads with 4 report types selectable
□ Spending over time: bar chart renders with monthly data
□ Net worth: line chart renders, current value matches sidebar
□ Income vs expenses: grouped bars visible
□ Category breakdown: table sorted correctly, donut chart visible
□ Date range changes update all charts
□ Axis labels show proper $ formatting
□ No crashes on empty date ranges
□ SECURITY: All queries parameterized
```

### COMMIT

```bash
git add -A
git commit -m "Phase 7: Reports — spending, net worth, income vs expenses, category breakdown"
```

---

## Phase 8: Polish & Security Hardening

### PROMPT

```
Closed Ledger project. Read IMPLEMENTATION.md. Phases 1–7 complete.

Build Phase 8 — Polish, security hardening, and packaging.

1. CSV EXPORT
   - Menu: File → Export Transactions → QFileDialog save-as .csv
   - WARNING DIALOG before export: "This will create an UNENCRYPTED file containing
     your financial data. The file will not be protected by your passphrase. Continue?"
     Two buttons: "Export Anyway" / "Cancel"
   - Exports visible transactions from current register (respects filters)
   - Columns: Date, Payee, Memo, Category, Tag, Amount (dollars), Check#, Account

2. CSV IMPORT
   - Menu: File → Import Transactions
   - Step 1: QFileDialog to select .csv file
   - Step 2: Preview first 5 rows in a QTableWidget
   - Step 3: Column mapping: QComboBoxes for each CSV column → Date/Payee/Memo/Category/Amount/Skip
   - Step 4: Select target account from QComboBox
   - Step 5: Preview mapped transactions
   - Step 6: Import with progress bar. Show results (N imported, N failed with reasons)

3. GLOBAL SEARCH
   - Ctrl+K or search icon in toolbar → QDialog with QLineEdit
   - Searches: payee, memo, category name across ALL transactions
   - Results in QListWidget grouped by account
   - Click result → navigate to that account's register
   - SECURITY: search query uses parameterized LIKE: cursor.execute("... LIKE ?", ('%' + query + '%',))

4. AUTO-LOCK (closed_ledger/security/session.py)
   - QTimer that resets on any user interaction (install event filter on QApplication)
   - After 15 minutes (configurable) of no interaction:
     a) Encrypt database back to disk
     b) Secure-delete temp plaintext file
     c) Show UnlockDialog
     d) On correct passphrase: decrypt and resume
   - Expose lock timeout in config.json

5. KEYBOARD SHORTCUTS
   - Ctrl+K: search
   - Ctrl+N: new transaction (focus new row in register)
   - Ctrl+S: save current edit
   - Escape: cancel edit / close dialog
   - Ctrl+Shift+B: backup
   - F1 or ?: show shortcuts help dialog (QDialog with QTableWidget listing shortcuts)

6. ENCRYPTED BACKUPS
   - Menu: File → Backup → copies .db.enc to backups/ dir with timestamp
   - Menu: File → Restore → QFileDialog to select .db.enc backup
     WARNING: "This will replace your current data with the backup. Continue?"
   - Both operations work on the encrypted file — no decryption needed.

7. LOADING STATES
   - Show QProgressDialog or QLabel "Loading..." during long queries
   - Startup: show progress while decrypting database

8. ERROR HANDLING
   - All database operations wrapped in try/except
   - User-facing errors shown in QMessageBox
   - Financial data NEVER appears in error messages or logs

9. PACKAGING (optional, instructions only)
   Create a PACKAGING.md with instructions for:
   - PyInstaller: pyinstaller --onefile --windowed closed_ledger/__main__.py
   - Include PySide6 and cryptography in the bundle
   - Set app icon
   - Platform-specific notes (macOS .app, Windows .exe, Linux AppImage)

SECURITY FINAL AUDIT:
- grep -rn 'import requests\|import urllib\|import http.client\|import socket' closed_ledger/
  → should return NOTHING (except possibly in comments)
- grep -rn "f'" closed_ledger/db/ → no SQL interpolation
- grep -rn '\.format' closed_ledger/db/ → no SQL interpolation
- Verify: no temp .db files left after close
- Verify: no listening sockets while running
- Verify: encrypted file on disk is not valid SQLite
```

### TESTING CHECKLIST

```
□ CSV EXPORT: File → Export → warning dialog appears → exports valid CSV
□ CSV EXPORT: Exported file contains correct data, amounts in dollars
□ CSV IMPORT: Can upload CSV, map columns, import to an account
□ CSV IMPORT: Imported transactions appear in register with correct values
□ SEARCH: Ctrl+K opens search, typing finds transactions by payee
□ SEARCH: Clicking result navigates to correct register
□ AUTO-LOCK: Set timeout to 1 minute for testing, wait → app locks
□ AUTO-LOCK: Correct passphrase unlocks, data intact
□ AUTO-LOCK: No temp .db file exists while locked
□ SHORTCUTS: Ctrl+N focuses new transaction row
□ SHORTCUTS: ? shows help dialog
□ BACKUP: File → Backup creates timestamped .db.enc in backups/
□ RESTORE: Selecting backup replaces data (test with caution)
□ ERROR HANDLING: Invalid CSV → helpful error, no crash
□ SECURITY AUDIT:
  □ grep -rn 'import requests' closed_ledger/ → nothing
  □ grep -rn 'import urllib' closed_ledger/ → nothing
  □ grep -rn 'import socket' closed_ledger/ → nothing
  □ grep -rn "f'" closed_ledger/db/ → no SQL string interpolation
  □ lsof -i -P -n | grep python → no network listeners
  □ file ~/.local/share/closed-ledger/closed-ledger.db.enc → not "SQLite"
  □ ls /tmp/*closed* → no temp files after clean close
  □ stat app data dir → 700, stat files → 600
□ App runs cleanly from start to finish with no errors
```

### COMMIT

```bash
git add -A
git commit -m "Phase 8: Polish — CSV, search, auto-lock, backup, security hardening"
```

---

## Post-Completion: Full Verification

```
□ Delete all app data, fresh start → passphrase creation works
□ Seed data → all 13 accounts, 250+ transactions populated
□ Sidebar balances correct, net worth correct
□ Register: running balance last row matches sidebar
□ Create/edit/delete transactions → balances update everywhere
□ Dashboard: donut chart with real data, bills with correct dates
□ Mark bill as paid → transaction created, date advanced
□ Budgets: budget vs actual correct, progress bars work
□ Reports: all 4 report types render with data
□ CSV import → transactions appear correctly
□ CSV export → warning shown, file is valid
□ Auto-lock → encrypts and locks, unlock resumes
□ Backup → creates encrypted copy, restore replaces data
□ SECURITY:
  □ No network sockets open (lsof)
  □ DB file is encrypted on disk (not readable as SQLite)
  □ No temp files after close
  □ Wrong passphrase rejected
  □ No SQL injection vectors (all queries parameterized)
  □ File permissions restrictive (600/700)
  □ No financial data in any log output
```

---

## Troubleshooting

**"No module named 'PySide6'"**
→ Activate your venv: `source venv/bin/activate`, then `pip install PySide6`

**"qt.qpa.plugin: Could not find the Qt platform plugin"**
→ On Linux, install: `sudo apt install libxcb-xinerama0 libxkbcommon-x11-0`

**Passphrase dialog doesn't appear (app crashes silently)**
→ Run from terminal: `python -m closed_ledger` to see Python traceback

**Database appears corrupted after crash**
→ The temp plaintext .db may still exist. Delete it manually, then relaunch (will decrypt from .db.enc)

**"cryptography" install fails**
→ Needs OpenSSL dev headers: `sudo apt install libssl-dev` (Linux) or `brew install openssl` (macOS)

**Charts don't render (blank area)**
→ Ensure PySide6 was installed with QtCharts: `pip install PySide6` should include it.
   Verify: `python -c "from PySide6.QtCharts import QChart; print('OK')"`

**Sidebar shows $0 for all balances**
→ Check that seed ran successfully. Relaunch with `python -m closed_ledger --seed`
→ Check that get_accounts_with_balances uses LEFT JOIN (accounts with 0 transactions should still show)
