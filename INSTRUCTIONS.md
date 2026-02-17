# INSTRUCTIONS.md — Claude Code Prompts by Phase

> This file contains the exact prompts to feed to Claude Code for each development phase. Run them in order. Each prompt assumes the previous phase is complete and working. Before starting, ensure Claude Code has access to README.md and IMPLEMENTATION.md in the project root.

---

## Pre-Flight

Before beginning Phase 1, give Claude Code this context-setting prompt:

### Prompt 0: Project Context

```
Read the README.md and IMPLEMENTATION.md files in this project root. These are the guiding
documents for the entire project. Familiarize yourself with the tech stack, data model,
design specifications, and phased development plan before proceeding.

This project is called OpenLedger — a Quicken-inspired personal finance manager. It is a
local-first, single-user Next.js application backed by SQLite. All monetary values are
stored as integers in cents. The UI is modeled after Quicken Classic 2013–2017.

Acknowledge that you've read both documents and summarize the key architectural decisions.
```

---

## Phase 1: Foundation

### Prompt 1.1: Project Scaffolding

```
Initialize the OpenLedger project. Follow the architecture defined in IMPLEMENTATION.md.

1. Create a Next.js 14 project with App Router, TypeScript (strict mode), and Tailwind CSS.
2. Install these exact dependencies:
   - better-sqlite3 and @types/better-sqlite3 (SQLite driver)
   - drizzle-orm and drizzle-kit (ORM and migration tooling)
   - recharts (charting)
   - date-fns (date utilities)
   - lucide-react (icons)
3. Configure drizzle.config.ts pointing to src/lib/db/schema.ts and ./drizzle/migrations output.
4. Add these npm scripts to package.json:
   - "db:generate": "drizzle-kit generate"
   - "db:migrate": "tsx src/lib/db/migrate.ts"
   - "db:seed": "tsx src/lib/db/seed.ts"
5. Create a .gitignore that includes data/ (the SQLite database directory) but NOT the drizzle migrations folder.
6. Create the directory structure outlined in README.md under "Project Structure".

Do not create any components or pages yet — just the project scaffold, configuration, and empty directories.
```

### Prompt 1.2: Database Schema

```
Create the complete database schema in src/lib/db/schema.ts using Drizzle ORM for SQLite.

Follow the exact schema defined in IMPLEMENTATION.md under "Data Model Deep Dive". Create all five tables:
1. accounts — with type enum, group enum, initial_balance in cents, is_debt, is_hidden, sort_order
2. transactions — with amount in cents (negative=payment, positive=deposit), category reference, transfer support
3. categories — with parent_id for hierarchy, type enum (income/expense/transfer), is_system flag
4. bill_reminders — with frequency enum, next_due_date, is_income, is_automatic
5. budgets — with category reference, amount in cents, year, month

Key requirements:
- All monetary amounts are INTEGER type stored in cents
- Dates are TEXT type in ISO format ('YYYY-MM-DD')
- Use proper foreign key references between tables
- Include created_at timestamps with default of current datetime
- Export all table definitions and their inferred types (InferSelectModel, InferInsertModel)

Then create the database connection singleton in src/lib/db/index.ts that:
- Creates data/ directory if missing
- Opens data/openledger.db
- Sets WAL journal mode and foreign_keys = ON
- Exports the drizzle db instance

Then create src/lib/db/migrate.ts that runs Drizzle migrations.

Finally, run drizzle-kit generate to create the initial migration, then verify the migration runs cleanly.
```

### Prompt 1.3: Seed Data

```
Create the seed script at src/lib/db/seed.ts that populates the database with realistic demo data
matching the Quicken screenshots described in IMPLEMENTATION.md.

The seed script should:
1. Check if data already exists (don't double-seed)
2. Clear all tables if re-seeding (in proper order to respect foreign keys)
3. Insert in this order: categories, accounts, transactions, bill_reminders, budgets

CATEGORIES — Create these hierarchical categories:

Income categories:
- Salary (income)
- Net Salary Spouse (income)  
- Interest Income (income)
- Dividend Income (income)
- Bonus (income)

Expense categories (parent → children):
- Food & Dining → Restaurants, Groceries, Coffee Shops
- Auto & Transport → Auto Pay, Gas & Fuel, Insurance, Parking, Public Transit
- Home → Mortgage, Rent, Home Services, Lawn & Garden, Home Improvement
- Bills & Utilities → Electric, Gas, Water, Internet, Phone, Cable, Trash
- Entertainment → Movies, Music, Games, Streaming
- Health & Fitness → Gym, Doctor, Pharmacy, Dentist
- Shopping → Clothing, Electronics, General
- Cash & ATM (no children)
- Personal Care (no children)
- Education (no children)
- Gifts & Donations (no children)
- Travel (no children)
- Taxes → Federal Tax, State Tax, Property Tax

Transfer categories:
- Transfer
- Credit Card Payment

ACCOUNTS — Create these accounts matching the screenshots:
- Family Checking (checking, banking) - initial balance that results in ~$1,491 after transactions
- My Checking (checking, banking) - ~$2,832
- My Savings (savings, banking) - $13,200
- My Credit Card (credit_card, banking, is_debt=true) - results in ~-$5,325
- Brokerage (brokerage, investing) - $95,164
- 401(k) (retirement_401k, investing) - $82,930
- Car Value (vehicle, property_debt) - $20,000
- House (property, property_debt) - $800,000
- Auto Loan (loan, property_debt, is_debt=true) - -$18,288
- Home Loan (mortgage, property_debt, is_debt=true) - -$283,043
- Loan (loan, property_debt, is_debt=true) - -$339,924
- Dream Home Fund (savings, savings_goals) - $4,050
- Vacation Fund (savings, savings_goals) - $700

TRANSACTIONS — Generate 250+ transactions on the Family Checking and My Checking accounts
spanning the last 6 months. Use these exact payees from the screenshots:
- Car Payment ($300, Auto & Transport:Auto Pay, monthly)
- ATM Withdrawal ($120, Cash & ATM, ~biweekly)
- Bo-bo- Chili And Ribs ($75, Food & Dining:Restaurants, ~biweekly)
- GameStop ($12.50, Entertainment, ~monthly)
- Trader Joe's ($100, Food & Dining:Groceries, ~weekly)
- Credit Card Payment ($750, Credit Card Payment, monthly, transfer to My Credit Card)
- Spouse Paycheck ($2,600, Net Salary Spouse, ~bimonthly, deposit)
- Restaurant ($75, Food & Dining:Restaurants, ~biweekly)
- Grocery Store ($100, Food & Dining:Groceries, ~weekly)
- Gym Membership ($100, Health & Fitness:Gym, monthly)
- Netflix ($12.50, Entertainment:Streaming, monthly)
- Gas & Electric ($250, Bills & Utilities:Electric, monthly)
- Mortgage Payment ($1,400, Home:Mortgage, monthly)
- Water Bill ($10, Bills & Utilities:Water, monthly)
- Yard Work ($25, Home:Lawn & Garden, monthly)
- Garden Bill ($12.50, Home:Home Services, monthly)
- Paycheck deposits (~$3,500, Salary, biweekly, deposit on My Checking)

Also generate some transactions on the credit card (Trader Joe's, restaurants, gas, etc.)

BILL REMINDERS — Create these monthly bills:
- Cable Bill ($150, Bills & Utilities:Cable, monthly, due 21st)
- Car Insurance ($150, Auto & Transport:Insurance, monthly, due 21st)
- Cell Phone ($90, Bills & Utilities:Phone, monthly, due 21st)
- Credit Card Payment ($750, Credit Card Payment, monthly, due 21st)
- Internet Service ($65, Bills & Utilities:Internet, monthly, due 21st)
- Transfer To Savings ($200, Transfer, monthly, due 21st)

BUDGETS — Create monthly budgets for the current month:
- Food & Dining: $600
- Auto & Transport: $500
- Bills & Utilities: $600
- Entertainment: $150
- Health & Fitness: $150
- Shopping: $200
- Home: $1,600

Run the seed script and verify data was inserted correctly.
```

### Prompt 1.4: Layout Shell

```
Create the root application layout and basic navigation structure.

ROOT LAYOUT (src/app/layout.tsx):
- HTML with system font stack, 14px base font size
- Body has flex row layout: sidebar on left, main content on right
- Sidebar is a fixed-width 240px panel on the left, full viewport height
- Main content area fills remaining width, flex column with top nav + scrollable content
- Import global styles from styles/globals.css

GLOBAL STYLES (src/styles/globals.css):
- Tailwind directives (@tailwind base, components, utilities)
- Custom CSS variables for the Quicken color palette defined in IMPLEMENTATION.md
- Base styles: box-sizing border-box, smooth scrolling
- Scrollbar styling for the sidebar (thin, subtle)

SIDEBAR PLACEHOLDER (src/components/layout/Sidebar.tsx):
- Light gray background (#F5F5F5)
- Header area: "ACCOUNTS" label with sync, add (+), and settings (⚙) icon buttons
- "All Transactions" link
- Placeholder text: "Accounts will appear here"
- Bottom: "Net Worth" label with placeholder value
- Bottom: "+ Add an Account" link
- This will be fully built in Phase 2 — just create the shell now

TOP NAVIGATION (src/components/layout/TopNav.tsx):
- Steel blue background (#4A7AB5)
- Tab items as links: HOME, SPENDING, BILLS, PLANNING, INVESTING, PROPERTY & DEBT, REPORTS
- Active tab has white bottom border or slightly lighter background
- Use Next.js Link component with usePathname for active detection
- HOME links to /, SPENDING to /spending, BILLS to /bills, REPORTS to /reports, etc.

ROUTE STUBS — Create placeholder pages for each route:
- src/app/page.tsx (Home) — "Dashboard coming in Phase 4"
- src/app/accounts/[id]/page.tsx — "Transaction Register coming in Phase 3"
- src/app/spending/page.tsx — "Spending coming in Phase 5"
- src/app/bills/page.tsx — "Bills coming in Phase 6"
- src/app/budgets/page.tsx — "Budgets coming in Phase 5"
- src/app/reports/page.tsx — "Reports coming in Phase 7"

Each placeholder should render a centered message in the content area. The sidebar and top nav
should be visible on all pages.

Verify the app runs with `npm run dev` and all routes work.
```

---

## Phase 2: Account Sidebar

### Prompt 2.1: Account Queries & Sidebar Data

```
Build the server-side data layer for the account sidebar, then implement the full Sidebar component.

QUERY FUNCTIONS (src/lib/db/queries/accounts.ts):
Create these reusable query functions:

1. getAccountsWithBalances() — Returns all non-hidden accounts with computed current balance:
   SELECT a.*, (a.initial_balance + COALESCE(SUM(t.amount), 0)) as current_balance
   FROM accounts a LEFT JOIN transactions t ON t.account_id = a.id
   WHERE a.is_hidden = 0 GROUP BY a.id ORDER BY a.group, a.sort_order, a.name

2. getAccountGroups() — Calls getAccountsWithBalances() and groups accounts by their `group` field.
   Returns an array of { group: string, label: string, accounts: Account[], total: number }
   Group labels: banking → "Banking", investing → "Investing", property_debt → "Property & Debt", savings_goals → "Savings Goals"

3. getNetWorth() — Sum of all account balances (current_balance from getAccountsWithBalances)

4. getAccountById(id) — Single account with current balance

SIDEBAR COMPONENT (src/components/layout/Sidebar.tsx):
Replace the placeholder with the full sidebar implementation. This is a SERVER COMPONENT.

Structure:
- Header: "ACCOUNTS" in bold, with Lucide icons for RefreshCw (sync), Plus (add account), Settings
- "All Transactions" link (navigates to /accounts/all)
- For each account group from getAccountGroups():
  - AccountGroup component (client component for collapse/expand state)
  - Group header: disclosure triangle (▼/▶), group label in bold, group total right-aligned
  - Account list: indented account names with balance right-aligned
  - Each account is a link to /accounts/[id]
- Net Worth at bottom: "Net Worth" label + formatted total
- "+ Add an Account" link at very bottom

ACCOUNT GROUP COMPONENT (src/components/accounts/AccountGroup.tsx):
- Client component ("use client") for collapse/expand state
- Default to expanded
- Click group header to toggle
- Smooth collapse animation (optional, simple height transition is fine)

CURRENCY DISPLAY COMPONENT (src/components/shared/Currency.tsx):
- Takes amount in cents and formats to display currency
- Negative values: red text, with negative sign before dollar sign (e.g., -$5,325)
- Positive values: default text color
- Format: $X,XXX or $X,XXX.XX (always show cents for transaction amounts, optionally hide for sidebar balances)
- Use Intl.NumberFormat for locale-aware formatting

Highlight the active account in the sidebar using the current URL pathname.
Verify all balances match the expected values from the seed data.
```

### Prompt 2.2: Add Account Modal

```
Create the "Add an Account" modal that opens when clicking "+ Add an Account" in the sidebar.

MODAL COMPONENT (src/components/shared/Modal.tsx):
- Reusable modal with backdrop overlay (semi-transparent black)
- Centered content card with rounded corners, shadow
- Close button (X) in top right
- Click backdrop to close
- Escape key to close
- Client component with portal to document.body

ACCOUNT FORM (src/components/accounts/AccountForm.tsx):
- Client component for form state management
- Fields:
  1. Account Name (text input, required)
  2. Account Type (select dropdown with all types from the schema)
  3. Financial Institution (text input, optional, e.g., "Chase", "Fidelity")
  4. Opening Balance (currency input, required, default $0.00)
     - Input should accept decimal dollar amounts and convert to cents for storage
- Auto-set the `group` and `is_debt` fields based on the selected account type
  (use the mapping table from IMPLEMENTATION.md)
- Submit button: "Add Account"
- Cancel button: closes modal

API ROUTE (src/app/api/accounts/route.ts):
- POST: Create a new account. Accept JSON body with name, type, institution, initialBalance.
  Auto-compute group and isDebt from type. Insert into accounts table. Return the new account.
- GET: Return all accounts with balances (for client-side refresh if needed).

Wire the "+ Add an Account" link in the sidebar to open this modal.
After successful creation, refresh the sidebar (use router.refresh() or revalidatePath).

Also create an edit mode for the form that pre-fills fields when editing an existing account.
Add a small edit (pencil) icon next to account names in the sidebar that opens the edit modal.

API ROUTE for single account:
- src/app/api/accounts/[id]/route.ts
- PUT: Update account fields
- DELETE: Delete account (only if it has no transactions, otherwise return error)
```

---

## Phase 3: Transaction Register

### Prompt 3.1: Transaction Data Layer

```
Build the server-side queries and API routes for transactions.

QUERY FUNCTIONS (src/lib/db/queries/transactions.ts):

1. getTransactionsForAccount(accountId, filters?) — Returns all transactions for an account with:
   - Category name (joined, formatted as "Parent:Child")
   - Running balance (computed via window function or application-level accumulation)
   - Sorted by date ASC, then id ASC
   - Optional filters: dateRange (start/end), type (payment/deposit/transfer/check), reconciled status
   - For "all" accounts view: return transactions across all accounts

2. getTransactionById(id) — Single transaction with category info

3. getPayeeSuggestions(query) — Return distinct payee names matching a prefix for autocomplete

4. getTransactionStats(accountId) — Returns { count, currentBalance, endingBalance } for the status bar

Computing running balance server-side:
```sql
WITH ordered AS (
  SELECT t.*, ROW_NUMBER() OVER (ORDER BY t.date, t.id) as rn
  FROM transactions t WHERE t.account_id = ?
)
SELECT *, 
  (SELECT a.initial_balance FROM accounts a WHERE a.id = ?) + 
  SUM(amount) OVER (ORDER BY date, id ROWS UNBOUNDED PRECEDING) as running_balance
FROM ordered
```
If this SQL window function approach doesn't work well with better-sqlite3/Drizzle, 
compute running balances in the application layer after fetching sorted transactions.

API ROUTES (src/app/api/transactions/route.ts):
- GET: List transactions with query params (accountId, dateStart, dateEnd, type, search)
- POST: Create transaction. Validate required fields (accountId, date, amount).
  If it's a transfer (transferAccountId provided), create the paired transaction on the other account.

API ROUTES (src/app/api/transactions/[id]/route.ts):
- GET: Single transaction
- PUT: Update transaction. If it's a transfer, also update the paired transaction.
- DELETE: Delete transaction. If it's a transfer, also delete the paired transaction.

CATEGORY QUERIES (src/lib/db/queries/categories.ts):
1. getAllCategories() — All categories with parent info, formatted as "Parent:Child" display names
2. getCategoryTree() — Hierarchical tree structure for the category picker dropdown
```

### Prompt 3.2: Transaction Register Page

```
Build the transaction register page at src/app/accounts/[id]/page.tsx.

This is the most important and most complex page in the application. It must match the layout
from Screenshot 1 (described in IMPLEMENTATION.md under "UI Reference Notes").

PAGE COMPONENT (src/app/accounts/[id]/page.tsx):
- Server component that fetches account info and transactions
- Page header: Account name in large text (e.g., "Family Checking")
- Below header: FilterBar component
- Below filter bar: TransactionTable component
- Below table: StatusBar component
- Handle the special case where id = "all" to show all transactions across accounts

FILTER BAR (src/components/transactions/FilterBar.tsx):
- Client component ("use client")
- Three select dropdowns in a horizontal row + Reset button:
  1. Date Range: All Dates, This Month, Last Month, This Year, Last Year, Last 12 Months, Custom Range
  2. Type: Any Type, Payment, Deposit, Transfer, Check
  3. Status: All Transactions, Unreconciled, Reconciled
- Reset button clears all filters to defaults
- Filters should update URL search params so they survive page refresh
- Style: compact, matches the screenshot with bordered dropdowns

TRANSACTION TABLE (src/components/transactions/TransactionTable.tsx):
- Client component for interactivity
- Table with these columns (matching Screenshot 1 exactly):
  | Column | Width | Align | Notes |
  |--------|-------|-------|-------|
  | Status icon | 30px | center | Reconciled checkmark or scheduled clock |
  | Flag | 24px | center | Red flag toggle |
  | Date | 95px | left | M/D/YYYY format |
  | Check # | 65px | left | Usually empty |
  | Payee | flex | left | Primary field, takes remaining space |
  | Memo | 150px | left | Secondary description |
  | Category | 200px | left | "Parent:Child" format |
  | Tag | 80px | left | Optional tag |
  | Payment | 95px | right | Amount if expense (no $ sign, just "300.00") |
  | Deposit | 95px | right | Amount if income |
  | Balance | 105px | right | Running balance |

- Alternating row colors: white and light blue (#F0F5FA)
- Table header row: light gray background, bold text, bottom border
- Numbers in Payment/Deposit/Balance columns: monospace or tabular-nums font feature
- Balance column shows running balance
- Click on the Date column header to toggle sort direction (default: ascending with ▲ indicator)

TRANSACTION ROW (src/components/transactions/TransactionRow.tsx):
- Default: display mode — shows formatted data in each cell
- Click on a row to enter edit mode:
  - Date becomes a date input
  - Payee becomes a text input with autocomplete
  - Memo becomes a text input
  - Category becomes a searchable select/dropdown
  - Payment/Deposit becomes a number input
  - Check # becomes a text input
  - Tag becomes a text input
- Enter or clicking outside saves changes via PUT /api/transactions/[id]
- Escape cancels edit mode
- Delete button appears on hover (trash icon at far right)

NEW TRANSACTION ROW:
- Always visible as the last row of the table
- Styled slightly differently (maybe a light yellow background or dashed top border)
- Fields are always in input mode
- Date defaults to today
- Submitting (Enter or Tab past last field) creates the transaction via POST and clears the row

STATUS BAR (src/components/layout/StatusBar.tsx):
- Fixed at the bottom of the content area
- Three sections: left, center, right
- Left: "{N} Transactions"
- Center: "Current Balance: {balance}" (the computed balance)
- Right: "Ending Balance: {balance}" (balance of the last transaction in the register)
- Subtle top border, small font size (12px)

CATEGORY PICKER:
- Dropdown/combobox for selecting categories
- Searchable: typing filters the list
- Shows hierarchy: parent categories as group headers, child categories indented below
- Creating a transaction with a category like "Food & Dining:Restaurants" should link to the child category

This is a large prompt. Focus on getting the table rendering correctly with real data first,
then add inline editing, then the new transaction row. Iterate.
```

### Prompt 3.3: Transaction Register Polish

```
Polish the transaction register from the previous step. Focus on these specific items:

1. PAYEE AUTOCOMPLETE:
   - When typing in the Payee field (edit mode or new transaction row), show a dropdown
     with matching payee names from previous transactions
   - Fetch suggestions from GET /api/transactions/suggestions?q=<prefix>
   - Arrow keys to navigate, Enter to select, Escape to dismiss

2. CURRENCY INPUT HANDLING:
   - The Payment and Deposit fields should accept decimal dollar amounts (e.g., "75.00" or "75")
   - On save, convert to cents for storage
   - On display, convert from cents to formatted string (no $ sign in the table, just "1,400.00")
   - Only one of Payment/Deposit should have a value. If user types in Payment, clear Deposit and vice versa.
   - Tabbing from Payment to Deposit should move focus, not duplicate the value

3. TRANSFER HANDLING:
   - If category is "Transfer" or "Credit Card Payment", show an additional dropdown to select
     the destination/source account
   - Creating a transfer should create paired transactions on both accounts
   - Display transfer transactions with the other account name in brackets, e.g., "[My Credit Card]"
     in the Category column

4. DELETE CONFIRMATION:
   - Clicking the delete (trash) icon shows a small confirmation popover: "Delete this transaction? [Yes] [No]"
   - Deleting a transfer deletes both paired transactions

5. DATE INPUT:
   - Date field should use a native date input or a lightweight date picker
   - Should display as M/D/YYYY in view mode but use a proper date picker in edit mode

6. KEYBOARD NAVIGATION:
   - Tab through fields in a row: Date → Check # → Payee → Memo → Category → Tag → Payment → Deposit
   - Enter on the last field saves and moves to a new blank row
   - Up/Down arrows move between rows (if not in edit mode)

Verify the register works correctly with the seed data. Check that running balances are accurate.
```

---

## Phase 4: Home Dashboard

### Prompt 4.1: Dashboard Data Layer

```
Build the server-side queries for the home dashboard.

QUERY FUNCTIONS (src/lib/db/queries/dashboard.ts):

1. getSpendingByCategory(dateStart, dateEnd) — Returns spending grouped by top-level category:
   SELECT c_parent.name as category, c_parent.id as category_id,
          ABS(SUM(t.amount)) as total
   FROM transactions t
   JOIN categories c ON t.category_id = c.id
   LEFT JOIN categories c_parent ON c.parent_id = c_parent.id
   WHERE t.amount < 0 
     AND t.date BETWEEN ? AND ?
     AND c.type = 'expense'
   GROUP BY COALESCE(c_parent.id, c.id)
   ORDER BY total DESC
   
   Return objects with: { category: string, total: number (in cents), color: string }
   Map category names to colors from the palette in IMPLEMENTATION.md.

2. getUpcomingBills(daysAhead) — Returns bill reminders due within the next N days:
   SELECT * FROM bill_reminders 
   WHERE next_due_date <= date('now', '+' || ? || ' days')
   ORDER BY next_due_date ASC
   Include status: 'overdue' if next_due_date < today, 'due_soon' if within 7 days, 'upcoming' otherwise.

3. getTotalSpending(dateStart, dateEnd) — Sum of all expense transactions in range

4. getWhatsLeft() — Budget remaining for the current month:
   Total budgeted income - total expenses this month so far
   Or: sum of all checking/savings account balances if no budgets set

5. getMonthlySpendingTotal(dateStart, dateEnd) — Simple sum of negative transactions (expenses)
```

### Prompt 4.2: Dashboard Page

```
Build the home dashboard page at src/app/page.tsx matching Screenshots 2 and 3.

PAGE LAYOUT:
- Page title: "Overview" (large heading)
- Sections stacked vertically with spacing between them

SECTION 1: SPENDING BY CATEGORY
- Card/panel with header "Spending By Category"
- Top right of header: total dollar amount (e.g., "$4,463.49") and date range dropdown
- Date range dropdown: "Last Month (MMM)", "This Month", "Last 30 Days", "Last 3 Months", "This Year"
- Donut chart (Recharts PieChart with inner radius):
  - Hole in the center showing "TOTAL SPENDING" label and dollar amount
  - Each segment colored by category using the consistent color palette
  - Legend on the right side showing category names with color swatches
- "Examine Your Spending" button below chart that links to /spending

DONUT CHART COMPONENT (src/components/dashboard/SpendingChart.tsx):
- Client component (Recharts requires "use client")
- Use Recharts: <PieChart>, <Pie>, <Cell>, <Tooltip>, <Legend>
- Inner radius = 60% of outer radius (to create the donut hole)
- Custom center label using Recharts' built-in customization or positioned absolutely
- Responsive: chart should resize with its container
- Tooltip shows category name and dollar amount on hover
- If no data, show an empty state message

SECTION 2: BILL & INCOME REMINDERS
- Card/panel with header "Bill & Income Reminders"
- Top right: date range dropdown ("Next 7 Days", "Next 14 Days", "Next 30 Days")
- "TODAY" marker with current date formatted as "MMM DD"
- List of bills:
  - Each row: status icon (clock for upcoming, red alert for overdue, "Auto" badge for automatic), 
    bill name, "Due in X days" or "Overdue by X days", amount in red
  - Amounts formatted as -$XXX.XX in red
  - If no bills in range, show "No upcoming bills" message

BILL REMINDERS COMPONENT (src/components/dashboard/BillReminders.tsx):
- Client component for the date range selector
- Fetch bill data server-side and pass as props, or use a client-side fetch
- Color coding: overdue = red text/icon, due within 3 days = orange, otherwise gray
- Show the bill name, due date description, and amount

SECTION 3: BUDGET SUMMARY (WHAT'S LEFT)
- Card/panel with header "Budget"
- Large display: "$X,XXX left" in green (or red if overspent)
- Subtitle: "in All Categories / All accounts"
- Computed from: total budget for the month minus total expenses this month
- If no budgets are set, show "Set up your budget" with a link to /budgets

The dashboard should use server components where possible, with client components only for
the chart and interactive dropdowns. Use async server components to fetch data.

Make sure the layout is clean and matches the Quicken aesthetic: cards with subtle borders,
proper spacing, consistent typography.
```

---

## Phase 5: Categories & Budgets

### Prompt 5.1: Category Management

```
Build the category management interface.

This can be accessed from a /categories route or as a modal/panel.

CATEGORY LIST VIEW:
- Tree view showing all categories in their hierarchy
- Each category shows: name, type (income/expense/transfer), number of transactions using it
- Indent child categories under parents
- Expand/collapse parent categories

CATEGORY CRUD:
- Add Category: name, type, optional parent category (select from existing parents)
- Edit Category: rename, change parent, change type
- Delete Category: only if no transactions reference it. Show warning with count if in use.
  Offer to reassign transactions to another category before deletion.

API ROUTES:
- GET /api/categories — All categories in tree structure
- POST /api/categories — Create new category
- PUT /api/categories/[id] — Update category
- DELETE /api/categories/[id] — Delete category (fail if in use, unless reassignment target provided)

This doesn't need to be elaborate — a simple, functional management page is fine.
```

### Prompt 5.2: Budget Tracking

```
Build the budget creation and tracking interface at /budgets.

BUDGET SETUP VIEW:
- Table with one row per expense category
- Columns: Category | Monthly Budget | Actual (this month) | Remaining
- Monthly budget column is editable — click to type a dollar amount
- Saving updates or creates the budget record for the current month/year
- Auto-populate the Actual column by summing transactions in that category for the current month

BUDGET OVERVIEW:
- Month selector at top: ← Previous Month | "January 2026" | Next Month →
- Summary row at top: "Total Budgeted: $X,XXX | Total Spent: $X,XXX | Remaining: $X,XXX"
- For each budgeted category:
  - Category name
  - Progress bar: green fill up to 75% of budget, yellow 75-100%, red over 100%
  - "Budgeted: $XXX | Spent: $XXX | Left: $XXX" text

API ROUTES:
- GET /api/budgets?year=YYYY&month=MM — Get budgets for a month with actual spending
- POST /api/budgets — Create/update budget (upsert by category+year+month)

DASHBOARD INTEGRATION:
Update the "Budget" section on the home dashboard to show real budget data:
- "$X,XXX left" using actual budget vs. spending calculation
- Link to /budgets page for details
```

---

## Phase 6: Bills & Scheduling

### Prompt 6.1: Bills Management Page

```
Build the bills management page at /bills.

BILLS LIST VIEW:
- Page title: "Bills & Income"
- Three sections: Overdue, Due Soon (next 7 days), Upcoming
- Each bill shows:
  - Status indicator (red circle for overdue, orange for due soon, gray for upcoming)
  - Bill name
  - Amount (in red for bills, in green for income)
  - Due date ("Due Feb 21" or "Overdue by 3 days")
  - Frequency badge ("Monthly", "Quarterly", etc.)
  - "Auto" badge if is_automatic
  - Action buttons: "Mark as Paid", "Skip", "Edit"

MARK AS PAID FLOW:
When user clicks "Mark as Paid" on a bill:
1. Show a confirmation dialog with pre-filled details (amount, date=today, account, category)
2. Allow the user to adjust the amount or date
3. On confirm:
   - Create a transaction on the bill's linked account with the bill amount, category, and date
   - Advance the bill's next_due_date based on frequency:
     - weekly: +7 days
     - biweekly: +14 days
     - monthly: +1 month (using date-fns addMonths)
     - quarterly: +3 months
     - annually: +1 year
     - once: mark bill as completed (hide or delete)
4. Refresh the bills list and sidebar

SKIP FLOW:
- Advance the next_due_date without creating a transaction

ADD/EDIT BILL MODAL:
- Fields: name, amount, category (dropdown), account (dropdown), frequency (dropdown), 
  next due date (date picker), is income (checkbox), is automatic (checkbox)
- For new bills, default frequency to "monthly" and next due date to the 1st of next month

API ROUTES:
- GET /api/bills — All bill reminders with computed status
- POST /api/bills — Create new bill reminder
- PUT /api/bills/[id] — Update bill reminder
- DELETE /api/bills/[id] — Delete bill reminder
- POST /api/bills/[id]/pay — Mark as paid (creates transaction, advances date)
- POST /api/bills/[id]/skip — Skip (advances date without transaction)
```

---

## Phase 7: Reports & Analytics

### Prompt 7.1: Reports Page

```
Build the reports page at /reports with multiple report types.

REPORTS HUB:
- Page title: "Reports"
- Report type selector (tabs or cards): 
  Spending Over Time | Net Worth | Income vs Expenses | Category Breakdown

REPORT 1: SPENDING OVER TIME
- Bar chart showing monthly total spending for the last 12 months
- X-axis: months (Jan, Feb, Mar...)
- Y-axis: dollar amounts
- Hovering a bar shows the exact amount
- Date range selector: Last 6 Months, Last 12 Months, This Year, Last Year, All Time
- Account filter: All Accounts or specific account group

REPORT 2: NET WORTH OVER TIME
- Line chart tracking net worth at end of each month
- Computed by: for each month-end date, calculate the sum of all account balances
  (initial_balance + sum of transactions through that date)
- X-axis: months
- Y-axis: dollar amounts
- Show the current net worth prominently
- Date range: Last 12 Months, Last 2 Years, All Time

REPORT 3: INCOME VS EXPENSES
- Grouped bar chart: two bars per month (income in green, expenses in red)
- Shows the surplus/deficit below each month
- Date range selector

REPORT 4: CATEGORY BREAKDOWN
- Detailed table showing spending per category for a selected period
- Columns: Category | Amount | % of Total | Avg per Month
- Sorted by amount descending
- Expandable rows to see subcategories
- Bar visualization next to each row showing relative size

All charts use Recharts components:
- BarChart + Bar for bar charts
- LineChart + Line for line charts
- PieChart + Pie for category breakdown (reuse from dashboard)
- ResponsiveContainer wrapper for all charts

Use Recharts tooltips, legends, and axis formatting for professional presentation.
Format all dollar amounts with commas and $ sign in chart labels.

QUERY FUNCTIONS (src/lib/db/queries/reports.ts):
1. getMonthlySpending(startDate, endDate) — Monthly totals of expense transactions
2. getNetWorthOverTime(startDate, endDate) — Net worth snapshot at each month end
3. getMonthlyIncomeVsExpenses(startDate, endDate) — Monthly income and expense totals
4. getCategoryBreakdown(startDate, endDate) — Per-category spending with hierarchy
```

---

## Phase 8: Polish & Power Features

### Prompt 8.1: CSV Import/Export

```
Add CSV import and export capabilities.

CSV EXPORT:
- Add "Export" button to the transaction register page
- Exports all visible transactions (respecting current filters) to a CSV file
- Columns: Date, Payee, Memo, Category, Tag, Amount, Check Number, Account
- Amount should be in dollar format (positive for deposits, negative for payments)
- Trigger a browser download of the CSV file
- Also add export to the reports page for report data

CSV IMPORT:
- Add "Import" button to the transaction register page (or a dedicated /import route)
- Upload UI: drag-and-drop zone + file browser button for CSV files
- Column mapping step:
  1. Parse the CSV and show a preview of the first 5 rows
  2. Show dropdowns for each CSV column to map to: Date, Payee, Memo, Category, Amount, Check Number, (Skip)
  3. Auto-detect common column names (Date, Description, Amount, etc.)
- Import preview: show how the transactions will look before committing
- Import execution: create all transactions on the selected account
- Handle common CSV formats from major banks (Chase, Bank of America, etc.)
  - Some banks put amount in one column (negative for debits)
  - Some banks have separate Debit and Credit columns
- Error handling: show which rows failed to import and why

API ROUTES:
- POST /api/transactions/import — Accept CSV data + column mapping, create transactions
- GET /api/transactions/export?accountId=X&dateStart=Y&dateEnd=Z — Return CSV data
```

### Prompt 8.2: Search & Keyboard Shortcuts

```
Add global search and keyboard shortcuts.

GLOBAL SEARCH:
- Search icon in the top navigation bar
- Clicking opens a search modal/overlay (similar to Cmd+K patterns)
- Search across all transactions: payee, memo, amount, category
- Show results grouped by account
- Click a result to navigate to that transaction in its register
- Debounced search (300ms) as user types
- API: GET /api/search?q=<query>&limit=20

KEYBOARD SHORTCUTS:
Implement these shortcuts (show a help modal listing them via ? key):
- Ctrl/Cmd + K: Open search
- Ctrl/Cmd + N: New transaction (focus the new transaction row)
- Escape: Cancel current edit / close modal
- Enter: Save current transaction edit
- Up/Down arrows: Navigate between transaction rows
- Ctrl/Cmd + S: Save all pending changes

Use a lightweight keyboard shortcut library or implement with useEffect + event listeners.
Add a small "?" icon in the bottom right that shows the shortcuts reference.
```

### Prompt 8.3: Final Polish

```
Final polish pass on the entire application.

1. LOADING STATES:
   - Add loading.tsx files for each route that show a skeleton/shimmer state
   - Sidebar should show shimmer placeholders while accounts load
   - Transaction table should show row placeholders while loading

2. EMPTY STATES:
   - New account with no transactions: "No transactions yet. Add your first transaction below."
   - No bills set up: "No bill reminders. Add your first bill to get started."
   - No budgets: "Set up your monthly budget to track spending."
   - Reports with no data in range: "No data for the selected period."

3. ERROR HANDLING:
   - API routes should return proper error responses with messages
   - Forms should show inline validation errors
   - Toast/notification for successful operations (transaction created, bill paid, etc.)

4. RESPONSIVE SIDEBAR:
   - On smaller screens (<1024px), sidebar collapses to icons only or hides behind a hamburger menu
   - Content area takes full width when sidebar is collapsed

5. DATA BACKUP:
   - Add a "Backup" button in settings/header
   - Creates a timestamped copy of openledger.db in a data/backups/ directory
   - "Restore" option that lists available backups and replaces the current database

6. PRINT STYLES:
   - Add @media print CSS rules
   - Hide sidebar and navigation when printing
   - Reports pages should be print-friendly

7. PERFORMANCE:
   - Add database indexes for common queries:
     - transactions(account_id, date)
     - transactions(category_id)
     - transactions(payee)
     - categories(parent_id)
   - Ensure the sidebar balance query is efficient even with thousands of transactions

Review the entire application for consistency in:
- Color usage (negative values always red, consistent chart colors)
- Currency formatting (consistent decimal places, comma separators)
- Date formatting (consistent M/D/YYYY throughout)
- Spacing and alignment (consistent padding, aligned numbers)
```

---

## Appendix: Useful Reference Commands

```bash
# Generate a new migration after schema changes
npm run db:generate

# Apply migrations
npm run db:migrate

# Re-seed the database (warning: clears existing data)
npm run db:seed

# Start development server
npm run dev

# Check TypeScript types
npx tsc --noEmit

# Inspect the SQLite database directly
sqlite3 data/openledger.db ".tables"
sqlite3 data/openledger.db "SELECT name, group_name FROM accounts ORDER BY group_name, sort_order;"
sqlite3 data/openledger.db "SELECT COUNT(*) FROM transactions;"

# Build for production
npm run build && npm start
```

---

## Appendix: Verification Checklist

After completing all phases, verify:

- [ ] App starts cleanly with `npm run dev`
- [ ] Fresh database is created and migrated automatically on first run
- [ ] Seed data populates correctly and can be re-run safely
- [ ] Sidebar shows all accounts with correct balances
- [ ] Net Worth calculation matches: sum of all account balances
- [ ] Transaction register shows correct running balances
- [ ] Creating a transaction updates the account balance in the sidebar
- [ ] Transfers create paired transactions on both accounts
- [ ] Dashboard spending chart shows real aggregated data
- [ ] Bill reminders show correct due dates and statuses
- [ ] "Mark as Paid" creates a transaction and advances the due date
- [ ] Budgets show accurate budget vs. actual spending
- [ ] Reports generate correct visualizations
- [ ] CSV import creates valid transactions
- [ ] CSV export downloads a correct file
- [ ] Search finds transactions across accounts
- [ ] No console errors in browser or terminal
- [ ] Database file persists across dev server restarts
