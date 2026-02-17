# INSTRUCTIONS.md — Claude Code Workflow

> **How to use this file**: Each phase below is designed to be run in its own Claude Code session. For each phase, you will copy-paste one or two prompts into Claude Code, let it work, then manually test the results using the provided checklist before moving to the next phase.

---

## How This Works

### Your Workflow for Each Phase

```
1. Open a NEW Claude Code session (fresh context)
2. Paste the CONTEXT PROMPT for that phase (it tells Claude Code what the project is and what's already done)
3. Paste the BUILD PROMPT for that phase (the actual work instructions)
4. Let Claude Code work. Answer any questions it asks.
5. When it's done, run the TESTING CHECKLIST yourself.
6. If something fails, paste the FIX PROMPT template with what's wrong.
7. Once all tests pass, commit your code and move to the next phase.
```

### Why New Sessions?

Claude Code has a context window limit. A fresh session for each phase means Claude Code starts clean, reads the project files on disk, and doesn't get confused by stale context from previous work. The CONTEXT PROMPT at the start of each phase catches it up instantly.

### Fix Prompt Template

Whenever something doesn't work after a phase, use this template:

```
I just completed Phase [N] of the Closed Ledger project. Read IMPLEMENTATION.md for full context.

The following test is failing:
[describe what's wrong — e.g., "The sidebar shows $0 for all account balances" or "npm run dev crashes with error: Cannot find module 'better-sqlite3'"]

The expected behavior is:
[describe what should happen]

Please investigate and fix this issue. Do not change anything unrelated to this fix.
```

### Important Files Claude Code Should Always Read

At the start of each session, Claude Code should be aware of these files in the project root:
- `README.md` — Project overview and structure
- `IMPLEMENTATION.md` — Full architecture spec, data model, UI specs, color palette

You don't need to tell Claude Code to read them explicitly — the context prompts below reference them. But if Claude Code seems confused, tell it: `Read IMPLEMENTATION.md before proceeding.`

---

## Phase 1: Foundation

> **Goal**: A running Next.js app with SQLite database, complete schema, seed data, and the basic three-panel layout shell.

### Step 1: Paste this CONTEXT + BUILD prompt into a new Claude Code session

```
I'm starting a new project called "Closed Ledger" — a personal finance manager inspired by
Quicken Classic (2013–2017 era). The project has planning docs already written.

Read README.md and IMPLEMENTATION.md in this directory. These define the full architecture,
data model, UI specs, and phased build plan. Familiarize yourself with them before writing
any code.

Then execute Phase 1 — Foundation. Here's everything you need to build:

1. PROJECT SETUP
   - Initialize a Next.js 14 project with App Router, TypeScript (strict), Tailwind CSS 3
   - The project name is "closed-ledger"
   - Install dependencies: better-sqlite3, @types/better-sqlite3, drizzle-orm, drizzle-kit,
     recharts, date-fns, lucide-react
   - Install tsx as a dev dependency (for running seed/migrate scripts)
   - Configure drizzle.config.ts for SQLite, pointing to src/lib/db/schema.ts, output to ./drizzle/migrations
   - Add npm scripts:
     "db:generate": "drizzle-kit generate"
     "db:migrate": "tsx src/lib/db/migrate.ts"
     "db:seed": "tsx src/lib/db/seed.ts"
   - .gitignore must include data/ but NOT drizzle/

2. DATABASE SCHEMA
   Create src/lib/db/schema.ts with ALL five tables defined in IMPLEMENTATION.md:
   accounts, transactions, categories, bill_reminders, budgets.
   Follow the exact column definitions, types, and constraints from the doc.
   All money values are INTEGER in cents. Dates are TEXT in ISO format.
   Export table definitions AND inferred TypeScript types.

3. DATABASE CONNECTION
   Create src/lib/db/index.ts — a singleton that:
   - Creates data/ directory if missing
   - Opens data/closed-ledger.db with better-sqlite3
   - Sets WAL journal mode and foreign_keys = ON
   - Wraps with Drizzle ORM
   - Exports the db instance

4. MIGRATION RUNNER
   Create src/lib/db/migrate.ts that runs pending Drizzle migrations.
   Generate the initial migration with drizzle-kit generate.
   Verify the migration runs without errors.

5. SEED SCRIPT
   Create src/lib/db/seed.ts matching the seed data spec in IMPLEMENTATION.md.
   It must:
   - Check if data exists already (skip if seeded, or clear and reseed)
   - Insert categories first (full hierarchy from the doc)
   - Insert accounts (all 13 accounts from the doc with correct initial balances)
   - Insert 250+ transactions spanning the last 6 months using the exact payees
     from the screenshots (Car Payment, ATM Withdrawal, Bo-bo- Chili And Ribs,
     GameStop, Trader Joe's, etc.)
   - Insert 6 bill reminders (Cable Bill, Car Insurance, Cell Phone, Credit Card Payment,
     Internet Service, Transfer To Savings)
   - Insert budgets for the current month
   Run the seed script and verify data was inserted.

6. LAYOUT SHELL
   Build the three-panel layout visible in all Quicken screenshots:
   - Root layout (src/app/layout.tsx): flex row, sidebar left + main right
   - Sidebar (src/components/layout/Sidebar.tsx): 240px fixed width, light gray bg (#F5F5F5),
     header with "ACCOUNTS" label, "All Transactions" link, placeholder account list,
     "Net Worth" at bottom, "+ Add an Account" at very bottom. THIS IS JUST A SHELL —
     Phase 2 will make it functional.
   - Top nav (src/components/layout/TopNav.tsx): steel blue bar (#4A7AB5), white text,
     tab items: HOME, SPENDING, BILLS, PLANNING, INVESTING, PROPERTY & DEBT, REPORTS.
     Use Next.js Link. Active tab detection via usePathname.
   - Global styles (src/styles/globals.css): Tailwind directives + CSS variables from
     the color palette in IMPLEMENTATION.md

7. ROUTE STUBS
   Create placeholder pages that just show a centered message:
   - src/app/page.tsx → "Dashboard coming in Phase 4"
   - src/app/accounts/[id]/page.tsx → "Transaction Register coming in Phase 3"
   - src/app/spending/page.tsx → "Spending analysis coming in Phase 5"
   - src/app/bills/page.tsx → "Bills management coming in Phase 6"
   - src/app/budgets/page.tsx → "Budget tracking coming in Phase 5"
   - src/app/reports/page.tsx → "Reports coming in Phase 7"

After building everything, run `npm run dev` and verify the app starts on localhost:3000.
```

### Step 2: Testing Checklist

After Claude Code finishes, verify each of these yourself:

```
□ npm run dev starts without errors
□ http://localhost:3000 loads and shows the three-panel layout
□ Sidebar is visible on the left (gray background, "ACCOUNTS" header)
□ Top nav bar is visible (steel blue, tab items are clickable)
□ Clicking tab items navigates to the correct routes with placeholder messages
□ data/closed-ledger.db file exists after first run
□ npm run db:seed runs without errors
□ Database has data — run this in terminal:
  sqlite3 data/closed-ledger.db "SELECT COUNT(*) FROM accounts;"      → should return 13
  sqlite3 data/closed-ledger.db "SELECT COUNT(*) FROM categories;"    → should return 40+
  sqlite3 data/closed-ledger.db "SELECT COUNT(*) FROM transactions;"  → should return 200+
  sqlite3 data/closed-ledger.db "SELECT COUNT(*) FROM bill_reminders;" → should return 6
□ Restarting npm run dev does NOT lose database data
□ No TypeScript errors (run: npx tsc --noEmit)
```

**If something fails**, use the Fix Prompt Template above. Common Phase 1 issues:
- `better-sqlite3` may need `node-gyp` / build tools — Claude Code should handle this
- Drizzle config may need adjustment for the migration output path
- Seed script may fail on foreign key ordering — categories must be inserted before transactions

### Step 3: Commit

```bash
git add -A
git commit -m "Phase 1: Foundation — project setup, schema, seed data, layout shell"
```

---

## Phase 2: Account Sidebar

> **Goal**: The sidebar becomes fully functional with real account balances, collapsible groups, net worth, and account CRUD.

### Step 1: Paste this CONTEXT + BUILD prompt

```
This is the Closed Ledger project — a Quicken-inspired personal finance app.
Read IMPLEMENTATION.md for the full architecture and data model.

Phase 1 is complete: the project has a running Next.js app, SQLite database with Drizzle ORM,
seeded data (13 accounts, 250+ transactions, categories, bill reminders), and a layout shell
with a placeholder sidebar and top navigation.

Now execute Phase 2 — Account Sidebar. Here's everything to build:

1. ACCOUNT QUERY FUNCTIONS (src/lib/db/queries/accounts.ts)
   Create reusable server-side query functions:
   - getAccountsWithBalances(): returns all non-hidden accounts with computed current balance.
     Balance = initial_balance + SUM(transactions.amount). Use LEFT JOIN so accounts with
     zero transactions still show. Order by group, sort_order, name.
   - getAccountGroups(): calls getAccountsWithBalances(), groups them by `group` field,
     returns array of { group, label, accounts, total }. Group labels:
     banking→"Banking", investing→"Investing", property_debt→"Property & Debt",
     savings_goals→"Savings Goals"
   - getNetWorth(): sum of all account current balances
   - getAccountById(id): single account with current balance

2. SIDEBAR COMPONENT (src/components/layout/Sidebar.tsx)
   Replace the placeholder sidebar with a fully functional server component:
   - Header: "ACCOUNTS" bold text with RefreshCw, Plus, Settings icons (from lucide-react)
   - "All Transactions" link (routes to /accounts/all)
   - For each account group: an AccountGroup client component
   - Net Worth at the bottom: "Net Worth" label with formatted total right-aligned
   - "+ Add an Account" link at the very bottom

3. ACCOUNT GROUP COMPONENT (src/components/accounts/AccountGroup.tsx)
   Client component ("use client") for expand/collapse:
   - Group header row: ▼/▶ disclosure triangle, group label (bold), total balance (right-aligned)
   - Clicking header toggles the children list
   - Each child: account name (indented, regular weight) linked to /accounts/[id], balance right-aligned
   - Negative balances in red text (credit cards, loans, mortgages)
   - Active account highlighted with light blue background (detect via usePathname)
   - Default state: expanded

4. CURRENCY COMPONENT (src/components/shared/Currency.tsx)
   - Takes amount in cents, formats for display
   - Negative: red text, "-$5,325" format
   - Positive: default color, "$13,200" format
   - Use Intl.NumberFormat for comma separators
   - Optional prop to show/hide cents (sidebar balances typically show whole dollars,
     transaction register shows cents)

5. ADD ACCOUNT MODAL
   - Reusable Modal component (src/components/shared/Modal.tsx): backdrop overlay, centered card,
     close on X/Escape/backdrop click, client component with portal
   - AccountForm component (src/components/accounts/AccountForm.tsx): client component with fields:
     Account Name (required), Account Type (dropdown with all types), Institution (optional),
     Opening Balance (currency input in dollars, converts to cents). Auto-sets group and isDebt
     from the type using the mapping in IMPLEMENTATION.md.
   - API route POST /api/accounts: creates account, returns it
   - API route GET /api/accounts: returns all accounts with balances
   - Wire "+ Add an Account" to open the modal
   - After creation, use router.refresh() to update the sidebar

6. EDIT & DELETE
   - Small pencil icon appears on hover next to account names in sidebar
   - Clicking opens the AccountForm in edit mode (pre-filled)
   - API route PUT /api/accounts/[id]: updates account
   - API route DELETE /api/accounts/[id]: deletes only if no transactions exist, else return error
   - After edit/delete, refresh sidebar

Verify that all account balances in the sidebar are correct by cross-referencing with the
seed data. The net worth should match the sum of all account balances.
```

### Step 2: Testing Checklist

```
□ Sidebar shows four account groups: Banking, Investing, Property & Debt, Savings Goals
□ Each group has a total balance that matches the sum of its accounts
□ Account balances match expected values from seed data:
  Family Checking: ~$1,491  |  My Checking: ~$2,832  |  My Savings: $13,200
  My Credit Card: ~-$5,325  |  Brokerage: $95,164  |  401(k): $82,930
  (Exact values depend on seed transactions — just verify they're reasonable, not $0)
□ Negative balances (credit card, loans, mortgage) display in red
□ Clicking a group header collapses/expands the account list
□ Clicking an account name navigates to /accounts/[id]
□ The active account is highlighted in the sidebar
□ "All Transactions" link navigates to /accounts/all
□ Net Worth at bottom = sum of all account balances
□ "+ Add an Account" opens a modal
□ Creating a new account (e.g., "Test Savings", type: savings, balance: $1000):
  - Modal closes after submit
  - New account appears in sidebar under Banking
  - Balance shows $1,000
□ Edit icon appears on hover, opens pre-filled form
□ Delete works for accounts with no transactions, shows error for accounts with transactions
□ No console errors
```

### Step 3: Commit

```bash
git add -A
git commit -m "Phase 2: Account Sidebar — live balances, groups, CRUD, net worth"
```

---

## Phase 3: Transaction Register

> **Goal**: The core data entry interface — a spreadsheet-like transaction table with CRUD, inline editing, filtering, and running balance. This is the biggest phase.

### Step 1: Paste this CONTEXT + BUILD prompt

```
This is the Closed Ledger project — a Quicken-inspired personal finance app.
Read IMPLEMENTATION.md for the full architecture, data model, and UI specs.

Phase 1–2 are complete: the app has a running database, seeded data, and a fully functional
sidebar with real account balances, collapsible groups, and account CRUD.

Now execute Phase 3 — Transaction Register. This is the most important page in the app.
It must closely match the transaction register from the Quicken screenshots described in
IMPLEMENTATION.md under "Phase 3: Transaction Register" and "UI Reference Notes."

Build ALL of the following:

1. TRANSACTION QUERIES (src/lib/db/queries/transactions.ts)
   - getTransactionsForAccount(accountId, filters?): returns transactions with category name
     (joined as "Parent:Child" format) and running balance. Sorted by date ASC, id ASC.
     Running balance = account.initialBalance + cumulative sum of amounts.
     Filters: dateRange {start, end}, type (payment/deposit/transfer), reconciled (boolean).
     For accountId="all": return all transactions across all accounts (no running balance).
   - getTransactionById(id): single transaction with category info
   - getPayeeSuggestions(query): distinct payee names matching prefix, for autocomplete
   - getTransactionStats(accountId): { count, currentBalance, endingBalance } for the status bar

2. CATEGORY QUERIES (src/lib/db/queries/categories.ts)
   - getAllCategories(): all categories with parent name, formatted as "Parent:Child" display string
   - getCategoryTree(): hierarchical tree for dropdown (groups children under parents)

3. API ROUTES
   - GET /api/transactions?accountId=X&dateStart=Y&dateEnd=Z&type=T
   - POST /api/transactions: create transaction. Validate accountId, date, amount required.
     If transferAccountId is provided, create paired transaction on other account.
   - PUT /api/transactions/[id]: update transaction. If transfer, update paired transaction too.
   - DELETE /api/transactions/[id]: delete transaction. If transfer, delete pair.
   - GET /api/categories: all categories in tree structure

4. TRANSACTION REGISTER PAGE (src/app/accounts/[id]/page.tsx)
   Server component that:
   - Fetches account info (name for header) and transactions with running balances
   - Renders: account name as page header (e.g., "Family Checking"), FilterBar, TransactionTable, StatusBar
   - Handles id="all" as a special case showing all transactions

5. FILTER BAR (src/components/transactions/FilterBar.tsx)
   Client component. Three select dropdowns + Reset button in a horizontal row:
   - Date Range: All Dates, This Month, Last Month, This Year, Last Year, Last 12 Months
   - Type: Any Type, Payment, Deposit, Transfer
   - Status: All Transactions, Unreconciled, Reconciled
   - Reset button clears all to defaults
   - Filters update URL search params (so they survive refresh)
   - Styled compactly matching the screenshots

6. TRANSACTION TABLE (src/components/transactions/TransactionTable.tsx)
   Client component. Columns matching IMPLEMENTATION.md Phase 3 exactly:
   Status icon (30px) | Flag (24px) | Date (95px) | Check # (65px) | Payee (flex) |
   Memo (150px) | Category (200px) | Tag (80px) | Payment (95px, right) | Deposit (95px, right) |
   Balance (105px, right)
   - Alternating row colors: white and #F0F5FA
   - Header row: light gray background, bold text
   - Currency in table: NO $ sign, just "300.00" and "3,556.31" (monospace/tabular-nums)
   - Date format: M/D/YYYY

7. INLINE EDITING (src/components/transactions/TransactionRow.tsx)
   - Click a row → entire row becomes editable (all fields become inputs)
   - Date: date input. Payee: text input with autocomplete from existing payees.
     Category: searchable dropdown showing "Parent:Child" hierarchy.
     Payment/Deposit: number input (dollars, converts to cents on save).
   - Enter or click-away saves via PUT /api/transactions/[id]
   - Escape cancels
   - Tab moves between fields within the row
   - Only ONE of Payment or Deposit should have a value (entering one clears the other)
   - Delete icon (trash) appears on row hover, with confirmation popover

8. NEW TRANSACTION ROW
   Always visible as the last row, slightly different styling (e.g., light yellow bg or dashed border).
   Fields are always in input mode. Date defaults to today.
   Enter/Tab on last field creates transaction via POST and clears the row for the next entry.

9. STATUS BAR (src/components/layout/StatusBar.tsx)
   Fixed at bottom of content area. Three sections:
   Left: "{N} Transactions" | Center: "Current Balance: X,XXX.XX" | Right: "Ending Balance: X,XXX.XX"
   Subtle top border, 12px font.

10. CATEGORY PICKER (src/components/shared/CategoryPicker.tsx)
    Searchable dropdown for selecting categories:
    - Typing filters the list
    - Parent categories shown as group headers (bold, not selectable)
    - Child categories shown indented below parents (selectable)
    - Selected value displays as "Parent:Child" text

After building, verify with seed data that the Family Checking register shows all its transactions
with correct running balances and that the status bar numbers are accurate.
```

### Step 2: Testing Checklist

```
□ Navigating to /accounts/[family-checking-id] shows the register
□ Page header shows "Family Checking"
□ Table displays all transactions for that account
□ Columns are correct: Date, Check#, Payee, Memo, Category, Tag, Payment, Deposit, Balance
□ Date format is M/D/YYYY (not MM/DD/YYYY or ISO)
□ Currency in table has no $ sign, just "300.00" format
□ Alternating row colors (white and light blue)
□ Running balance is correct:
  - First transaction balance = initial balance + first transaction amount
  - Each subsequent balance = previous balance + current amount
  - LAST row balance matches the account balance shown in the sidebar
□ Status bar shows correct transaction count and balance values
□ FILTER: Selecting "This Month" filters to current month's transactions only
□ FILTER: Selecting "Payment" shows only expense transactions
□ FILTER: Reset button restores defaults
□ INLINE EDIT: Clicking a row makes it editable
□ INLINE EDIT: Changing the payee and pressing Enter saves the change
□ INLINE EDIT: Escape cancels without saving
□ NEW TRANSACTION: Typing in the bottom row and pressing Enter creates a new transaction
□ NEW TRANSACTION: After creation, the new row appears in the table and sidebar balance updates
□ DELETE: Trash icon appears on hover, clicking shows confirmation, confirming deletes the row
□ Category picker shows hierarchical categories and is searchable
□ "All Transactions" (/accounts/all) shows transactions from all accounts
□ No console errors
```

### Step 3: Commit

```bash
git add -A
git commit -m "Phase 3: Transaction Register — table, CRUD, filters, running balance"
```

---

## Phase 4: Home Dashboard

> **Goal**: The landing page with spending chart, bill reminders, and budget summary.

### Step 1: Paste this CONTEXT + BUILD prompt

```
This is the Closed Ledger project — a Quicken-inspired personal finance app.
Read IMPLEMENTATION.md for full context, particularly the Phase 4 and UI Reference sections.

Phases 1–3 are complete: the app has a database with seeded data, a functional sidebar with
real balances, and a full transaction register with inline editing, filtering, and running balances.

Now execute Phase 4 — Home Dashboard. This replaces the placeholder at src/app/page.tsx.

Build ALL of the following:

1. DASHBOARD QUERIES (src/lib/db/queries/dashboard.ts)
   - getSpendingByCategory(dateStart, dateEnd): aggregate expense transactions (amount < 0)
     by TOP-LEVEL category (if a transaction has a child category like "Food & Dining:Restaurants",
     group it under the parent "Food & Dining"). Exclude transfers. Return array of
     { category, total (in cents, as positive number), color }. Map categories to the color
     palette defined in IMPLEMENTATION.md under "Category Color Mapping."
   - getUpcomingBills(daysAhead): bill reminders where next_due_date is within the next N days.
     Include computed status: 'overdue' if past due, 'due_soon' if within 7 days, 'upcoming' otherwise.
   - getTotalSpending(dateStart, dateEnd): sum of all expense transactions in the range
   - getWhatsLeft(): total budgeted for current month minus total expenses this month

2. DASHBOARD PAGE (src/app/page.tsx)
   Server component. Page title: "Overview". Three card sections stacked vertically:

   SECTION A — SPENDING BY CATEGORY
   - Card header: "Spending By Category" left-aligned, total dollar amount right-aligned
   - Date range dropdown in header: "Last Month (MMM)", "This Month", "Last 30 Days",
     "Last 3 Months", "This Year" — defaults to "Last Month"
   - Donut chart (Recharts PieChart with innerRadius for the hole)
   - Center of donut: "TOTAL SPENDING" label + dollar amount (e.g., "$3,954")
   - Right side: legend with category name + color swatch for each segment
   - If no expense data in range, show "No spending data for this period"

3. SPENDING CHART COMPONENT (src/components/dashboard/SpendingChart.tsx)
   Client component ("use client") — Recharts requires it.
   - PieChart with Pie component, innerRadius ~60% of outerRadius
   - Each Cell colored by the category's assigned color
   - Tooltip on hover showing category name and dollar amount
   - Custom center label (absolutely positioned text over the chart center)
   - ResponsiveContainer wrapper for responsive sizing
   - Date range selector triggers re-fetch of data

4. BILL REMINDERS WIDGET (src/components/dashboard/BillReminders.tsx)
   - Card header: "Bill & Income Reminders" with dropdown: "Next 7 Days", "Next 14 Days", "Next 30 Days"
   - "TODAY" badge with current date (e.g., "TODAY Feb 16")
   - List of bills: status icon, bill name, "Due in X days" or "Overdue by X days", amount in red
   - Status icon: red alert circle for overdue, orange clock for due soon, gray clock for upcoming
   - Amounts formatted as -$XXX.XX in red
   - If no bills in range: "No upcoming bills"

5. BUDGET SUMMARY WIDGET (src/components/dashboard/BudgetSummary.tsx)
   - Card header: "Budget"
   - Large number: "$X,XXX left" in green if positive, red if negative
   - Subtitle: "in All Categories"
   - If no budgets exist: "Set up your budget →" link to /budgets

Make sure the dashboard loads with real data from the seed. The spending chart should show
actual spending from the seeded transactions. The bill reminders should show the 6 seeded bills.
```

### Step 2: Testing Checklist

```
□ Home page (/) shows "Overview" title with three card sections
□ Spending donut chart renders with colored segments
□ Total spending amount appears in the center of the donut
□ Legend on the right shows category names with color swatches
□ Changing the date range dropdown updates the chart data
□ Bill reminders section shows the 6 seeded bills with correct amounts
□ Bill due dates are reasonable ("Due in X days" or "Overdue by X days")
□ Overdue bills show red indicator, due-soon bills show orange
□ Budget summary shows a dollar amount or "Set up your budget" link
□ Date range dropdown for bills (Next 7/14/30 days) changes the visible bills
□ All dollar amounts are properly formatted with commas and $ signs
□ Chart colors are consistent (Home=green, Food=orange, etc.)
□ No console errors
□ Dashboard loads fast (under 2 seconds)
```

### Step 3: Commit

```bash
git add -A
git commit -m "Phase 4: Home Dashboard — spending chart, bill reminders, budget summary"
```

---

## Phase 5: Categories & Budgets

> **Goal**: Category management and monthly budget tracking with budget vs. actual views.

### Step 1: Paste this CONTEXT + BUILD prompt

```
This is the Closed Ledger project — a Quicken-inspired personal finance app.
Read IMPLEMENTATION.md for full context.

Phases 1–4 are complete: running app with database, sidebar, full transaction register,
and home dashboard with spending chart and bill reminders.

Now execute Phase 5 — Categories & Budgets.

1. CATEGORY MANAGEMENT (route: /categories or accessible via a modal/settings)
   - Tree view showing all categories in hierarchy (parents with children indented)
   - Each row: category name, type badge (income/expense/transfer), transaction count using it
   - Expand/collapse parent categories
   - Add Category: name, type dropdown, optional parent category dropdown
   - Edit Category: rename, change parent, change type
   - Delete Category: only if no transactions reference it. If in use, show count and block deletion.
   - API routes: GET/POST /api/categories, PUT/DELETE /api/categories/[id]

2. BUDGET TRACKING PAGE (route: /budgets)
   - Month navigation at top: ← arrow | "Month YYYY" | → arrow
   - Summary bar: "Total Budgeted: $X,XXX | Total Spent: $X,XXX | Remaining: $X,XXX"
   - Table with one row per budgeted expense category:
     Category | Budgeted | Actual Spent | Remaining | Progress Bar
   - Progress bar: green fill ≤75%, yellow 75-100%, red >100% of budget
   - Budgeted column is editable — clicking shows an input to change the amount
   - Actual Spent is computed from transactions in that category for the selected month
   - Categories without a budget set can still show spending (with $0 budget)
   - "Add Budget" row at bottom for categories not yet budgeted

3. BUDGET API
   - GET /api/budgets?year=YYYY&month=MM: returns budgets with actual spending per category
   - POST /api/budgets: upsert — create or update budget for category+year+month
   - DELETE /api/budgets/[id]: remove a budget line

4. DASHBOARD INTEGRATION
   Update the Budget summary widget on the home dashboard (from Phase 4) to show real data:
   - Compute: sum of all budget amounts for current month - sum of actual spending this month
   - Display as "$X,XXX left" in green, or "-$XXX over budget" in red
   - Link to /budgets for details

Make sure all budget calculations use the same amount-in-cents convention as the rest of the app.
The budget page should show meaningful data with the seeded budgets and transactions.
```

### Step 2: Testing Checklist

```
□ /categories (or category management UI) shows all categories in a tree
□ Can add a new category (e.g., "Subscriptions" under "Bills & Utilities")
□ Can rename an existing category
□ Deleting a category with transactions shows an error/warning
□ Deleting an unused category works
□ /budgets page shows the current month with seeded budget data
□ Budget table shows category, budgeted amount, actual spending, remaining
□ Progress bars show correct fill level and color (green/yellow/red)
□ Can change a budget amount by clicking the Budgeted column
□ Month navigation (← →) changes the displayed month
□ Navigating to a month with no budgets shows empty state or $0 values
□ Dashboard budget widget now shows real "$ left" data
□ Budget remaining matches: sum(budgets) - sum(expenses for the month)
□ No console errors
```

### Step 3: Commit

```bash
git add -A
git commit -m "Phase 5: Categories & Budgets — category CRUD, budget tracking, progress bars"
```

---

## Phase 6: Bills & Scheduling

> **Goal**: Full bill reminder management, "Mark as Paid" flow, and recurring date advancement.

### Step 1: Paste this CONTEXT + BUILD prompt

```
This is the Closed Ledger project — a Quicken-inspired personal finance app.
Read IMPLEMENTATION.md for full context.

Phases 1–5 are complete: running app with database, sidebar, transaction register,
home dashboard, category management, and budget tracking.

Now execute Phase 6 — Bills & Scheduling.

1. BILLS PAGE (route: /bills)
   - Page title: "Bills & Income"
   - Three sections: OVERDUE (red header), DUE SOON (orange, next 7 days), UPCOMING (gray)
   - Each bill row shows:
     Status indicator (red/orange/gray circle), bill name, amount (-$XXX in red, or +$XXX
     in green for income), due date ("Due Feb 21" or "Overdue by 3 days"),
     frequency badge ("Monthly"), "Auto" badge if is_automatic
   - Action buttons per bill: "Mark as Paid" (green), "Skip" (gray), "Edit" (pencil icon)

2. MARK AS PAID
   When clicking "Mark as Paid":
   - Show confirmation dialog pre-filled with: amount, date (today), account, category
   - User can adjust the amount or date before confirming
   - On confirm:
     a) Create a transaction on the bill's linked account with bill's amount (as negative
        cents for expense, positive for income), bill's category, and the selected date
     b) Advance next_due_date based on frequency:
        weekly→+7d, biweekly→+14d, monthly→+1mo (date-fns addMonths),
        quarterly→+3mo, annually→+1yr, once→mark as completed
     c) Refresh the bills list, sidebar balances, and dashboard
   - API: POST /api/bills/[id]/pay { amount?, date? }

3. SKIP
   - Advance next_due_date without creating a transaction
   - API: POST /api/bills/[id]/skip

4. BILL CRUD
   - "Add Bill" button opens a modal with fields: name, amount (dollar input),
     category (dropdown), account (dropdown), frequency (dropdown), next due date (date picker),
     is income (checkbox), is automatic (checkbox)
   - Edit opens same modal pre-filled
   - Delete with confirmation
   - API: POST/PUT/DELETE /api/bills, /api/bills/[id]

5. DASHBOARD INTEGRATION
   Make sure the Bill Reminders widget on the home dashboard (Phase 4) uses the same query
   as this page. Clicking a bill on the dashboard could navigate to /bills.

Test with the 6 seeded bill reminders. Mark one as paid and verify a transaction was created
and the due date advanced.
```

### Step 2: Testing Checklist

```
□ /bills page shows all 6 seeded bill reminders
□ Bills are sorted into correct sections (overdue/due soon/upcoming)
□ Each bill shows name, amount, due date, frequency badge
□ "Mark as Paid" opens a confirmation dialog with pre-filled details
□ Confirming "Mark as Paid":
  - Creates a new transaction (visible in the account's register)
  - Advances the bill's next_due_date by one frequency period
  - Updates the sidebar balance for the affected account
  - The bill moves to its new due date section
□ "Skip" advances the due date without creating a transaction
□ "Add Bill" opens modal, creating a new bill works
□ "Edit" opens pre-filled modal, saving changes works
□ Delete removes the bill with confirmation
□ Dashboard bill reminders widget still works correctly
□ No console errors
```

### Step 3: Commit

```bash
git add -A
git commit -m "Phase 6: Bills & Scheduling — bill CRUD, mark as paid, recurring dates"
```

---

## Phase 7: Reports & Analytics

> **Goal**: Data visualization and financial analysis reports.

### Step 1: Paste this CONTEXT + BUILD prompt

```
This is the Closed Ledger project — a Quicken-inspired personal finance app.
Read IMPLEMENTATION.md for full context.

Phases 1–6 are complete. The app has all core features: accounts, transactions, dashboard,
categories, budgets, and bills.

Now execute Phase 7 — Reports & Analytics.

Build a reports hub at /reports with four report types, selectable via tabs or cards at the top:

1. SPENDING OVER TIME
   - Recharts BarChart showing monthly total spending (sum of expense transactions) for each month
   - X-axis: month labels (Jan, Feb, Mar...), Y-axis: dollar amounts
   - Tooltip on bar hover showing exact amount
   - Date range selector: Last 6 Months, Last 12 Months, This Year, Last Year, All Time

2. NET WORTH OVER TIME
   - Recharts LineChart tracking net worth at the end of each month
   - For each month-end, compute: sum of all account initial balances + sum of all transactions
     through that month-end date
   - Show current net worth prominently above the chart
   - Date range: Last 12 Months, Last 2 Years, All Time

3. INCOME VS EXPENSES
   - Recharts grouped BarChart: two bars per month (green=income, red=expenses)
   - Below each pair: surplus/deficit label
   - Date range selector
   - Summary: total income, total expenses, net surplus/deficit for the period

4. CATEGORY BREAKDOWN
   - Detailed table: Category | Amount | % of Total | Avg per Month
   - Sorted by amount descending
   - Expandable rows to show subcategories
   - Small horizontal bar next to each row showing relative size vs largest category
   - Reuse the donut chart from the dashboard above the table
   - Date range selector

REPORT QUERIES (src/lib/db/queries/reports.ts):
- getMonthlySpending(start, end): monthly expense totals as array of {month, year, total}
- getNetWorthOverTime(start, end): net worth at each month-end
- getMonthlyIncomeVsExpenses(start, end): monthly income and expense totals
- getCategoryBreakdown(start, end): per-category spending with hierarchy

ALL reports should have:
- Date range controls (dropdown with presets)
- Recharts with ResponsiveContainer, proper axis formatting (dollar amounts with $),
  tooltips, and legends
- Clean layout with the chart above and any summary stats below

Use the seeded data to verify charts render with meaningful data.
```

### Step 2: Testing Checklist

```
□ /reports page loads with report type tabs/cards
□ SPENDING OVER TIME: bar chart renders with monthly bars
□ SPENDING OVER TIME: hovering a bar shows the dollar amount
□ SPENDING OVER TIME: changing date range updates the chart
□ NET WORTH: line chart renders with monthly data points
□ NET WORTH: current net worth displayed above chart matches sidebar
□ INCOME VS EXPENSES: grouped bars show income (green) and expenses (red)
□ INCOME VS EXPENSES: surplus/deficit summary is accurate
□ CATEGORY BREAKDOWN: table shows categories sorted by spending
□ CATEGORY BREAKDOWN: percentages add up to ~100%
□ CATEGORY BREAKDOWN: expandable rows show subcategories
□ All charts use proper dollar formatting on axes ($1,000, $2,000, etc.)
□ Date range selectors work across all report types
□ Charts are responsive (resize with browser window)
□ No console errors
```

### Step 3: Commit

```bash
git add -A
git commit -m "Phase 7: Reports — spending, net worth, income vs expenses, category breakdown"
```

---

## Phase 8: Polish & Power Features

> **Goal**: CSV import/export, search, keyboard shortcuts, and final quality pass.

### Step 1: Paste this CONTEXT + BUILD prompt

```
This is the Closed Ledger project — a Quicken-inspired personal finance app.
Read IMPLEMENTATION.md for full context.

Phases 1–7 are complete. All core features are built. Now execute Phase 8 — Polish.

1. CSV EXPORT
   - "Export" button on the transaction register page
   - Exports visible transactions (respecting filters) as CSV download
   - Columns: Date, Payee, Memo, Category, Tag, Amount (dollars, negative for payments), Check #, Account
   - Also add export capability to reports pages
   - API: GET /api/transactions/export?accountId=X&dateStart=Y&dateEnd=Z → returns CSV

2. CSV IMPORT
   - "Import" button on the register or a /import route
   - Upload: drag-and-drop zone + file picker for .csv files
   - Step 1: Parse CSV, show preview of first 5 rows
   - Step 2: Column mapping — dropdowns for each CSV column to map to: Date, Payee, Memo,
     Category, Amount, Check Number, (Skip). Auto-detect common names.
   - Step 3: Preview how transactions will look
   - Step 4: Execute import on selected account
   - Handle both single-amount and separate debit/credit column formats
   - Error handling: show which rows failed and why
   - API: POST /api/transactions/import

3. GLOBAL SEARCH
   - Search icon in the top nav bar
   - Opens a Cmd+K style search overlay/modal
   - Search across all transactions: payee, memo, amount, category name
   - Results grouped by account
   - Clicking a result navigates to that transaction in its register
   - Debounced 300ms search as user types
   - API: GET /api/search?q=query&limit=20

4. KEYBOARD SHORTCUTS
   - Ctrl/Cmd+K: open search
   - Ctrl/Cmd+N: focus new transaction row
   - Escape: cancel edit / close modal
   - Enter: save current edit
   - "?" key: show shortcuts help modal

5. LOADING & EMPTY STATES
   - Add loading.tsx skeleton/shimmer states for each route
   - Empty state messages for: no transactions, no bills, no budgets, no report data

6. ERROR HANDLING
   - API routes return proper error JSON with messages
   - Forms show inline validation errors (required fields, invalid amounts)
   - Toast/notification component for success messages ("Transaction created", "Bill paid")

7. DATA BACKUP
   - "Backup" button in sidebar settings area
   - Copies closed-ledger.db to data/backups/closed-ledger-YYYY-MM-DD-HHMMSS.db
   - "Restore" lists available backups and can replace the current database
   - Confirmation dialog before restore (destructive action)

8. PERFORMANCE
   - Add database indexes: transactions(account_id, date), transactions(category_id),
     transactions(payee), categories(parent_id)
   - Verify sidebar and register load fast with 500+ transactions

9. PRINT STYLES
   - @media print rules that hide sidebar and nav
   - Reports are print-friendly
```

### Step 2: Testing Checklist

```
□ CSV EXPORT: "Export" button on register downloads a valid CSV file
□ CSV EXPORT: Opening the CSV in a spreadsheet shows correct data
□ CSV IMPORT: Can upload a CSV file and see a preview
□ CSV IMPORT: Column mapping dropdowns work
□ CSV IMPORT: Importing creates real transactions visible in the register
□ SEARCH: Ctrl/Cmd+K opens search overlay
□ SEARCH: Typing a payee name shows matching transactions
□ SEARCH: Clicking a result navigates to the correct register
□ SHORTCUTS: "?" shows keyboard shortcuts help
□ LOADING: Pages show skeleton/shimmer while loading
□ EMPTY STATES: New account shows "No transactions yet" message
□ ERRORS: Submitting a transaction with no amount shows validation error
□ TOAST: Creating a transaction shows a success notification
□ BACKUP: Clicking backup creates a file in data/backups/
□ BACKUP: Restore replaces the database (test with caution)
□ PERFORMANCE: Register loads in under 1 second with all seed data
□ PRINT: Ctrl+P on a report page shows a clean printable view
□ No console errors across the entire application
```

### Step 3: Final Commit

```bash
git add -A
git commit -m "Phase 8: Polish — CSV import/export, search, shortcuts, backup, loading states"
```

---

## Post-Completion: Full App Verification

After all 8 phases, run through this end-to-end test:

```
□ Fresh start: delete data/closed-ledger.db, run npm run dev — app creates DB automatically
□ Run npm run db:seed — all seed data populates
□ Sidebar shows 13 accounts with correct balances across 4 groups
□ Net Worth is calculated correctly
□ Click Family Checking → register shows 100+ transactions with correct running balance
□ Create a new transaction → sidebar balance updates, register shows new row
□ Delete a transaction → balance updates correctly
□ Home dashboard shows spending chart with real data
□ Bill reminders show upcoming bills with correct dates
□ Mark a bill as paid → transaction created, due date advances, balances update
□ Budget page shows budget vs actual for current month
□ Reports page generates all 4 report types with real data
□ Import a CSV from a bank → transactions appear in register
□ Export transactions → valid CSV downloads
□ Search finds transactions by payee name
□ Backup creates a copy of the database file
□ App handles 500+ transactions without performance issues
```

---

## Troubleshooting Common Issues

**"Cannot find module 'better-sqlite3'"**
→ Run `npm install` again. May need build tools: `apt-get install build-essential python3`

**"SQLITE_CONSTRAINT: FOREIGN KEY constraint failed"**
→ Seed script is inserting in wrong order. Categories must come before transactions.

**"Hydration mismatch" errors**
→ A server component is using browser-only APIs. Make sure client components have "use client" directive.

**Sidebar shows $0 for all balances**
→ The balance query likely has a JOIN issue. Check that getAccountsWithBalances uses LEFT JOIN.

**Running balance is wrong in the register**
→ Check sort order: must be date ASC, id ASC. Check that initial balance is included as the starting point.

**Charts don't render**
→ Recharts requires "use client". Make sure chart components are client components.

**Database resets on restart**
→ Check that data/ is NOT in any clean/build script. The database file must persist.
