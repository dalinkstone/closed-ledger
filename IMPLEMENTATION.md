# IMPLEMENTATION.md — OpenLedger Development Plan

> This document is the guiding architecture and implementation reference for Claude Code. It defines the phased development plan, data model details, UI specifications, and technical decisions. Read this document fully before beginning any phase.

---

## Table of Contents

1. [Philosophy & Constraints](#philosophy--constraints)
2. [Data Model Deep Dive](#data-model-deep-dive)
3. [Phase Overview](#phase-overview)
4. [Phase 1: Foundation](#phase-1-foundation)
5. [Phase 2: Account Sidebar](#phase-2-account-sidebar)
6. [Phase 3: Transaction Register](#phase-3-transaction-register)
7. [Phase 4: Home Dashboard](#phase-4-home-dashboard)
8. [Phase 5: Categories & Budgets](#phase-5-categories--budgets)
9. [Phase 6: Bills & Scheduling](#phase-6-bills--scheduling)
10. [Phase 7: Reports & Analytics](#phase-7-reports--analytics)
11. [Phase 8: Polish & Power Features](#phase-8-polish--power-features)
12. [UI Reference Notes](#ui-reference-notes)
13. [Testing Strategy](#testing-strategy)

---

## Philosophy & Constraints

### Core Principles

1. **Local-first, single-user.** There is no authentication, no multi-tenancy, no cloud sync. One person, one machine, one SQLite file.

2. **Data is sacred.** The SQLite database in `data/openledger.db` must never be deleted by any build step, script, or migration. Migrations must be additive and non-destructive. Every write operation should be wrapped in a transaction.

3. **Dense but readable UI.** Quicken's UI is information-dense — it packs a lot of data into every screen. This is intentional. Financial software users want to see numbers, not whitespace. We use small font sizes (13–14px), tight row heights (30–34px), and minimal padding. However, the UI should still feel clean and organized, not cramped.

4. **Server components by default.** Use Next.js server components for all read operations. Only use client components (`"use client"`) when the component needs interactivity (forms, dropdowns, charts, click handlers). This keeps the app fast and avoids unnecessary client-side JavaScript.

5. **Incremental complexity.** Each phase should produce a working, usable application. Phase 1 gives you a running app with a database. Phase 2 adds the sidebar. Phase 3 adds the register. Each phase builds on the last without requiring rewrites.

### Technical Constraints

- **No network calls.** The app runs on localhost. No external APIs, no CDN resources at build time (Tailwind/fonts should be local or inline).
- **No authentication.** No login page, no session management.
- **SQLite only.** Do not introduce PostgreSQL, MySQL, or any other database.
- **No ORM magic.** Use Drizzle's explicit query builder. No lazy loading, no implicit joins. Every query should be readable and predictable.
- **Amounts stored as integers.** All monetary values are stored as integers in cents (e.g., `$1,234.56` → `123456`). This avoids floating-point errors. Display formatting happens in the UI layer only.

---

## Data Model Deep Dive

### Accounts Table

```typescript
export const accounts = sqliteTable('accounts', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  name: text('name').notNull(),
  type: text('type', { 
    enum: ['checking', 'savings', 'credit_card', 'cash', 'brokerage', 'retirement_401k', 'ira', 
           'property', 'vehicle', 'loan', 'mortgage', 'other_asset', 'other_liability'] 
  }).notNull(),
  group: text('group', { 
    enum: ['banking', 'investing', 'property_debt', 'savings_goals'] 
  }).notNull(),
  institution: text('institution'),           // e.g., "Chase", "Fidelity"
  initialBalance: integer('initial_balance').notNull().default(0),  // in cents
  isDebt: integer('is_debt', { mode: 'boolean' }).notNull().default(false),
  isHidden: integer('is_hidden', { mode: 'boolean' }).notNull().default(false),
  sortOrder: integer('sort_order').notNull().default(0),
  createdAt: text('created_at').notNull().default(sql`(datetime('now'))`),
});
```

**Account groups** map to sidebar sections:
- `banking` → "Banking" (checking, savings, credit cards, cash)
- `investing` → "Investing" (brokerage, 401k, IRA)
- `property_debt` → "Property & Debt" (property, vehicles, loans, mortgages)
- `savings_goals` → "Savings Goals" (savings goals are special savings accounts with target amounts)

**Balance calculation**: An account's current balance is computed as:
```
currentBalance = account.initialBalance + SUM(transactions.amount WHERE account_id = account.id)
```
The balance is **never stored directly** on the account row (except initial balance). It is always computed from transactions. This ensures consistency.

**Debt accounts**: Credit cards, loans, and mortgages have `isDebt = true`. Their balance is displayed as negative in the sidebar when the sum is positive (because a positive transaction on a credit card means spending/owing more).

### Transactions Table

```typescript
export const transactions = sqliteTable('transactions', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  accountId: integer('account_id').notNull().references(() => accounts.id),
  date: text('date').notNull(),                // ISO date string: '2013-08-05'
  payee: text('payee').notNull().default(''),
  memo: text('memo').default(''),
  categoryId: integer('category_id').references(() => categories.id),
  tag: text('tag').default(''),
  amount: integer('amount').notNull(),          // in cents, negative = payment/expense, positive = deposit/income
  checkNumber: text('check_number').default(''),
  isReconciled: integer('is_reconciled', { mode: 'boolean' }).notNull().default(false),
  transferAccountId: integer('transfer_account_id').references(() => accounts.id),
  transferTransactionId: integer('transfer_transaction_id').references(() => transactions.id),
  createdAt: text('created_at').notNull().default(sql`(datetime('now'))`),
});
```

**Amount convention**: 
- **Negative amounts** = money leaving the account (payments, expenses, withdrawals)
- **Positive amounts** = money entering the account (deposits, income, refunds)
- For credit cards, this is inverted in display: a $75 restaurant charge is stored as `-7500` on the checking account or `+7500` on the credit card (increasing the balance owed).

**Transfers**: When money moves between accounts, two linked transactions are created:
- Transaction A on source account (negative amount)
- Transaction B on destination account (positive amount)  
- Each references the other via `transferTransactionId`

**Running balance**: In the transaction register view, the "Balance" column shows a running balance computed by ordering transactions by date (then by id for same-date ordering) and accumulating from the account's initial balance.

### Categories Table

```typescript
export const categories = sqliteTable('categories', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  name: text('name').notNull(),
  parentId: integer('parent_id').references(() => categories.id),
  type: text('type', { enum: ['income', 'expense', 'transfer'] }).notNull().default('expense'),
  isSystem: integer('is_system', { mode: 'boolean' }).notNull().default(false),
  sortOrder: integer('sort_order').notNull().default(0),
});
```

**Hierarchical categories**: Quicken uses a colon-delimited hierarchy:
- "Food & Dining" (parent)
  - "Food & Dining:Restaurants" (child)
  - "Food & Dining:Groceries" (child)
- "Auto & Transport" (parent)
  - "Auto & Transport:Auto Pay" (child)
  - "Auto & Transport:Gas & Fuel" (child)

The `parentId` field creates this tree. Display uses "Parent:Child" format.

**Default categories to seed** (based on screenshots):
- Income: Salary, Spouse Salary, Interest, Dividends, Bonus
- Expense: Food & Dining (Restaurants, Groceries, Coffee), Auto & Transport (Auto Pay, Gas & Fuel, Insurance, Parking), Home (Mortgage, Rent, Home Services, Lawn & Garden), Bills & Utilities (Electric, Gas, Water, Internet, Phone, Cable), Entertainment (Movies, Music, Games), Health & Fitness (Gym, Doctor, Pharmacy), Cash & ATM, Shopping, Personal Care, Education, Gifts & Donations, Travel, Taxes
- Transfer: Transfer (between accounts), Credit Card Payment

### Bill Reminders Table

```typescript
export const billReminders = sqliteTable('bill_reminders', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  name: text('name').notNull(),
  amount: integer('amount').notNull(),          // in cents
  categoryId: integer('category_id').references(() => categories.id),
  accountId: integer('account_id').references(() => accounts.id),
  frequency: text('frequency', { 
    enum: ['weekly', 'biweekly', 'monthly', 'quarterly', 'annually', 'once'] 
  }).notNull().default('monthly'),
  nextDueDate: text('next_due_date').notNull(), // ISO date
  isIncome: integer('is_income', { mode: 'boolean' }).notNull().default(false),
  isAutomatic: integer('is_automatic', { mode: 'boolean' }).notNull().default(false),
  createdAt: text('created_at').notNull().default(sql`(datetime('now'))`),
});
```

### Budgets Table

```typescript
export const budgets = sqliteTable('budgets', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  categoryId: integer('category_id').notNull().references(() => categories.id),
  amount: integer('amount').notNull(),          // monthly budget in cents
  year: integer('year').notNull(),
  month: integer('month').notNull(),            // 1-12
});
```

---

## Phase Overview

| Phase | Name | Deliverable | Depends On |
|-------|------|-------------|------------|
| 1 | Foundation | Running Next.js app with SQLite, schema, seed data, basic layout shell | — |
| 2 | Account Sidebar | Fully functional account sidebar with groups, balances, net worth | Phase 1 |
| 3 | Transaction Register | Full transaction table with CRUD, filtering, running balance | Phase 2 |
| 4 | Home Dashboard | Overview page with spending chart, bill reminders, summary stats | Phase 3 |
| 5 | Categories & Budgets | Category management, budget creation, budget vs. actual views | Phase 4 |
| 6 | Bills & Scheduling | Bill reminder CRUD, recurring transaction generation, due date alerts | Phase 4 |
| 7 | Reports & Analytics | Spending over time, net worth tracking, category comparison reports | Phase 5 |
| 8 | Polish & Power Features | CSV import/export, keyboard shortcuts, search, dark mode | Phase 7 |

---

## Phase 1: Foundation

### Goal
A running Next.js application with SQLite database, complete schema, seed data, and the basic layout shell (sidebar placeholder + top navigation + content area).

### Deliverables
1. Next.js 14 project with TypeScript, Tailwind CSS, App Router
2. SQLite database via better-sqlite3 with Drizzle ORM
3. Complete schema for all tables (accounts, transactions, categories, bill_reminders, budgets)
4. Migration system that auto-runs on app start
5. Seed script that populates realistic demo data
6. Root layout with three-panel structure: sidebar | top-nav + content
7. Basic route stubs for all main pages

### Database Initialization Pattern
The database connection should be a singleton module that:
1. Creates the `data/` directory if it doesn't exist
2. Opens/creates `data/openledger.db`
3. Enables WAL mode for better concurrent read performance
4. Runs any pending Drizzle migrations
5. Exports the `db` instance for use throughout the app

```typescript
// src/lib/db/index.ts — conceptual pattern
import Database from 'better-sqlite3';
import { drizzle } from 'drizzle-orm/better-sqlite3';
import { migrate } from 'drizzle-orm/better-sqlite3/migrator';
import path from 'path';
import fs from 'fs';

const DB_PATH = path.join(process.cwd(), 'data', 'openledger.db');

// Ensure data directory exists
fs.mkdirSync(path.dirname(DB_PATH), { recursive: true });

const sqlite = new Database(DB_PATH);
sqlite.pragma('journal_mode = WAL');
sqlite.pragma('foreign_keys = ON');

export const db = drizzle(sqlite, { schema });

// Run migrations on import
migrate(db, { migrationsFolder: './drizzle/migrations' });
```

### Seed Data Specification
The seed script should create data that mirrors the Quicken screenshots:

**Accounts:**
- Banking: Family Checking ($1,491), My Checking ($2,832), My Savings ($13,200), My Credit Card (-$5,325)
- Investing: Brokerage ($95,164), 401(k) ($82,930)
- Property & Debt: Car Value ($20,000), House ($800,000), Auto Loan (-$18,288), Home Loan (-$283,043), Loan (-$339,924)
- Savings Goals: Dream Home Fund ($4,050), Vacation Fund ($700)

**Transactions:** Generate 200+ transactions across the accounts spanning 6 months, using realistic payees and categories from the screenshots:
- Car Payment, ATM Withdrawal, Bo-bo- Chili And Ribs, GameStop, Trader Joe's, Credit Card Payment, Spouse Paycheck, Restaurant, Grocery Store, Gym Membership, Netflix, Gas & Electric, Mortgage Payment, Water Bill, Yard Work, Garden Bill

**Categories:** All default categories with hierarchy as described in the data model section.

**Bill Reminders:** Cable Bill, Car Insurance, Cell Phone, Credit Card Payment, Internet Service, Transfer To Savings — all monthly.

### Layout Shell Specification
The root layout establishes the three-panel structure visible in all screenshots:

```
┌─────────────────────────────────────────────────────────────────┐
│  [Accounts ↻ + ⚙]  │  HOME │ SPENDING │ BILLS │ PLANNING │ ...│
├─────────────────────┼───────────────────────────────────────────┤
│                     │                                           │
│  All Transactions   │        (content area)                     │
│                     │                                           │
│  ▼ Banking  $12,199 │                                           │
│    Family Checking  │                                           │
│    My Checking      │                                           │
│    My Savings       │                                           │
│    My Credit Card   │                                           │
│                     │                                           │
│  ▼ Investing        │                                           │
│    Brokerage        │                                           │
│    401(k)           │                                           │
│                     │                                           │
│  ▼ Property & Debt  │                                           │
│    Car Value        │                                           │
│    House            │                                           │
│    Auto Loan        │                                           │
│    Home Loan        │                                           │
│                     │                                           │
│  ▼ Savings Goals    │                                           │
│    Dream Home Fund  │                                           │
│    Vacation Fund    │                                           │
│                     │                                           │
│  Net Worth $373,787 │                                           │
│  + Add an Account   │                                           │
└─────────────────────┴───────────────────────────────────────────┘
```

- Sidebar: fixed width 240px, full viewport height, light gray background (`#F5F5F5`), scrollable independently
- Top nav: steel blue background (`#4A7AB5`), white text, tab items for Home, Spending, Bills, Planning, Investing, Property & Debt, Reports
- Content: white background, fills remaining space, scrollable

---

## Phase 2: Account Sidebar

### Goal
A fully interactive account sidebar matching the Quicken screenshots, with real-time balance computation, collapsible groups, and account management.

### Deliverables
1. `Sidebar` component with collapsible account groups
2. `AccountGroup` component with group name, total balance, expand/collapse
3. Account links that navigate to `/accounts/[id]` (transaction register)
4. "All Transactions" link at top that shows all transactions across accounts
5. Net Worth calculation at bottom of sidebar
6. "+ Add an Account" button that opens a modal
7. Account creation/edit modal with type selection, name, initial balance

### Balance Computation
Account balances must be computed server-side using SQL aggregation:

```sql
SELECT 
  a.id,
  a.name,
  a.initial_balance + COALESCE(SUM(t.amount), 0) as current_balance
FROM accounts a
LEFT JOIN transactions t ON t.account_id = a.id
WHERE a.is_hidden = 0
GROUP BY a.id
ORDER BY a.group, a.sort_order, a.name
```

Group totals are the sum of all account balances in that group.

Net Worth = SUM(all account balances). Debt accounts naturally contribute negative values.

### Sidebar Visual Specification
From the screenshots:
- Group headers: Bold, slightly larger text, with a disclosure triangle (▼/▶). Group total balance right-aligned.
- Account names: Indented under group, regular weight. Balance right-aligned.
- Negative balances: Red text (e.g., `-$5,325` for credit card, `-$283,043` for home loan)
- Active account: Highlighted with a light blue background
- "All Transactions" link at very top, before any groups
- Net Worth at bottom: Bold label "Net Worth" with the total right-aligned
- "+ Add an Account" link at very bottom

### Account Types → Groups Mapping

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

---

## Phase 3: Transaction Register

### Goal
The core data entry interface — a spreadsheet-like transaction register that matches the Quicken register view from screenshot 1.

### Deliverables
1. `TransactionTable` component with all columns from the screenshot
2. Inline editing of existing transactions (click to edit)
3. New transaction row at the bottom (always present, like a spreadsheet)
4. Running balance column computed in order
5. `FilterBar` with date range, transaction type, and category filters
6. Status bar showing: "{N} Transactions | Current Balance: $X | Ending Balance: $Y"
7. Transaction deletion with confirmation
8. Category autocomplete dropdown with hierarchical display

### Column Specification (from Screenshot 1)

| Column | Width | Align | Content |
|--------|-------|-------|---------|
| Status | 30px | center | Icons: ⓘ (info), ⏰ (scheduled), ✓ (reconciled) |
| Flag | 24px | center | Red flag icon for flagged transactions |
| Date | 90px | left | MM/DD/YYYY format, sorted ascending by default |
| Check # | 60px | left | Optional check number |
| Payee | 200px | left | Payee name — the primary description |
| Memo | 150px | left | Optional additional notes |
| Category | 200px | left | Full category path "Parent:Child" |
| Tag | 80px | left | Optional tag |
| ✓ (Cleared) | 24px | center | Cleared/reconciled status checkbox |
| Payment | 90px | right | Amount if negative (money out), formatted without sign |
| Deposit | 90px | right | Amount if positive (money in) |
| Balance | 100px | right | Running balance |

### Running Balance Calculation
The running balance is computed by ordering all transactions for the account by date (ascending), then by id (ascending) for same-date transactions, and accumulating from the account's initial balance:

```
runningBalance[0] = account.initialBalance + transaction[0].amount
runningBalance[i] = runningBalance[i-1] + transaction[i].amount
```

This must be computed server-side and passed to the component. When filters are active, the running balance should still reflect ALL transactions (not just filtered ones), but only filtered transactions should be displayed.

### Filter Bar Specification (from Screenshot 1)
Three dropdowns in a row:
1. **Date Range**: "All Dates", "This Month", "Last Month", "This Year", "Last Year", "Last 12 Months", "Custom Range..."
2. **Type**: "Any Type", "Payment", "Deposit", "Transfer", "Check"
3. **Transaction Filter**: "All Transactions", "Unreconciled", "Reconciled"
4. **Reset button**: Clears all filters back to defaults

### Inline Editing Behavior
- Click any cell in an existing transaction to enter edit mode for that row
- The entire row becomes editable (all fields show as inputs)
- Press Enter or click away to save
- Press Escape to cancel
- Tab moves between fields within the row
- New transaction row at the bottom is always in "edit mode" style

### Transaction Form Fields
When editing a transaction (inline or via the new row):
- **Date**: Date picker, defaults to today
- **Check #**: Text input, optional
- **Payee**: Text input with autocomplete from existing payees
- **Memo**: Text input, optional  
- **Category**: Dropdown with searchable, hierarchical categories. Shows "Parent:Child" format. Typing filters the list.
- **Tag**: Text input, optional
- **Payment/Deposit**: Only one can have a value. Entering in Payment makes amount negative; entering in Deposit makes it positive.

---

## Phase 4: Home Dashboard

### Goal
The landing page / overview dashboard matching screenshots 2 and 3. This is what the user sees when they open the app or click "Home."

### Deliverables
1. "Spending By Category" donut chart with dollar total in center
2. Date range selector for the spending chart (Last Month, This Month, Last 30 Days, etc.)
3. "Bill & Income Reminders" section showing upcoming bills
4. "What's Left" budget summary widget
5. Responsive layout with widgets stacked/arranged sensibly

### Spending By Category Donut Chart
This is the centerpiece of the dashboard (see screenshots 2 and 3).

**Data source**: Aggregate all expense transactions (negative amounts) within the selected date range, grouped by top-level category. Exclude transfers.

**Visual specification**:
- Donut chart (not pie — there's a hole in the center)
- Center of donut shows: "TOTAL SPENDING" label and dollar amount (e.g., "$3,954")
- Below center: "in All Categories / All accounts"
- Color-coded segments with legend on the right side
- Legend shows category name and color swatch
- Segment colors should be consistent per category (always the same color for "Home", etc.)

**Category color mapping** (from screenshots):
- Home: Green
- Auto & Transport: Purple/Blue  
- Bills & Utilities: Pink/Magenta
- Food & Dining: Orange/Red
- Cash & ATM: Dark Blue
- Health & Fitness: Light Red/Coral
- Entertainment: Teal/Cyan
- Tax: Olive/Dark Green
- Employer Benefit: Red/Orange
- Other: Light Teal

### Bill & Income Reminders Widget
From screenshot 2:
- Header: "Bill & Income Reminders" with a date range selector ("Next 7 Days", "Next 14 Days", "Next 30 Days")
- "TODAY" marker with current date
- List of upcoming bills showing: status icon, bill name, due date description ("Due in 5 days"), and amount in red
- Bills from the `bill_reminders` table where `next_due_date` falls within the selected range

### What's Left Widget
From screenshot 3:
- Shows "WHAT'S LEFT" with a large dollar amount
- Computed as: budgeted income for the month minus total expenses so far this month
- Subtitle: "in your checking accounts"

### Dashboard Layout
```
┌─────────────────────────────────────────────────┐
│  Overview                                       │
│                                                 │
│  ┌─ Spending By Category ────────────────────┐  │
│  │                               $4,463.49   │  │
│  │            [DONUT CHART]    Last Month ▼   │  │
│  │                                           │  │
│  └───────────────────────────────────────────┘  │
│                                                 │
│  ┌─ Bill & Income Reminders ─────────────────┐  │
│  │                          Next 7 Days  ▼   │  │
│  │  TODAY: Feb 16                            │  │
│  │  ⏰ Cable Bill        Due in 5 days  -$150│  │
│  │  ⏰ Car Insurance     Due in 5 days  -$150│  │
│  │  ⏰ Cell Phone        Due in 5 days   -$90│  │
│  └───────────────────────────────────────────┘  │
│                                                 │
│  ┌─ Budget ──────────────────────────────────┐  │
│  │  $2,581 left                              │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

---

## Phase 5: Categories & Budgets

### Goal
Full category management and monthly budget tracking.

### Deliverables
1. Category management page (add, edit, rename, reparent categories)
2. Budget creation page — set monthly budget amounts per category
3. Budgets page showing budget vs. actual spending per category for the selected month
4. Budget progress bars (green = under budget, yellow = near budget, red = over budget)
5. Category picker component used in transaction forms and budget forms

### Budget vs. Actual View
A table showing:

| Category | Budgeted | Actual | Remaining |
|----------|----------|--------|-----------|
| Food & Dining | $500.00 | $375.00 | $125.00 |
| Entertainment | $100.00 | $112.50 | -$12.50 |

With a progress bar for each row. Monthly navigation (← Jan 2026 →).

---

## Phase 6: Bills & Scheduling

### Goal
Comprehensive bill reminder management and recurring transaction support.

### Deliverables
1. Bills page listing all bill reminders with status (overdue, due soon, upcoming)
2. Bill reminder CRUD — add/edit/delete bill reminders
3. "Mark as Paid" action that creates a transaction from the bill reminder and advances the next due date
4. Overdue bill indicators (red) in the sidebar and dashboard
5. Recurring transaction logic: when a bill is marked as paid, the next_due_date advances based on frequency

### Bill Status Logic
- **Overdue**: `next_due_date < today` → Red indicator
- **Due Soon**: `next_due_date <= today + 7 days` → Orange/yellow indicator  
- **Upcoming**: `next_due_date > today + 7 days` → Gray/neutral
- **Auto**: `is_automatic = true` → Shows "Auto" badge (the bank handles it)

### Mark as Paid Flow
1. User clicks "Mark as Paid" on a bill reminder
2. System creates a transaction on the linked account with the bill's amount, category, and today's date
3. System advances `next_due_date` by the frequency interval (e.g., +1 month for monthly)
4. Dashboard and sidebar refresh to reflect the new transaction and updated bill

---

## Phase 7: Reports & Analytics

### Goal
Data visualization and reporting tools for financial analysis.

### Deliverables
1. Spending Over Time — Bar or line chart showing monthly spending totals
2. Spending By Category — Detailed breakdown for a selected period
3. Net Worth Over Time — Line chart tracking total net worth month over month
4. Income vs. Expenses — Side-by-side comparison per month
5. Category Comparison — Compare spending between two periods

### Net Worth Over Time
Compute net worth at the end of each month by summing all account balances (initial + transactions through that month-end). Plot as a line chart.

### Report Date Range Controls
All reports should have:
- Predefined ranges: This Month, Last Month, Last 3 Months, Last 6 Months, This Year, Last Year
- Custom date range picker
- Account filter (All Accounts, specific account, specific account group)

---

## Phase 8: Polish & Power Features

### Goal
Quality-of-life improvements and advanced features.

### Deliverables
1. **CSV Import**: Import transactions from bank CSV exports. Column mapping UI.
2. **CSV Export**: Export transactions and reports to CSV.
3. **Global Search**: Search transactions across all accounts by payee, memo, amount, category.
4. **Keyboard Shortcuts**: 
   - `Ctrl+N` — New transaction
   - `Ctrl+S` — Save current transaction
   - `Escape` — Cancel editing
   - `↑/↓` — Navigate between transactions
5. **Data Backup/Restore**: Copy the SQLite file to a backup location, restore from backup.
6. **Dark Mode**: Alternate color scheme for the entire app.
7. **Print-friendly Reports**: CSS print stylesheet for reports.

---

## UI Reference Notes

### Key Visual Details from Screenshots

**Screenshot 1 — Transaction Register (Quicken 2013 Windows):**
- Title bar shows "Family Checking" as page header
- Steel blue tab bar with: Home, Spending, Bills, Planning, Investing, Property & Debt, Rental Property, Mobile & Alerts, Tips & Tutorials
- Filter bar has three dropdowns: "All Dates", "Any Type", "All Transactions" + Reset button
- Table headers: dot icon, flag, Date ▲, Check #, Payee, Memo, Category, Tag, ✓ (reconciled), Payment, Deposit, Balance
- Alternating row colors: white and very light blue (#F0F5FA or similar)
- Date format: M/D/YYYY (8/5/2013, not 08/05/2013)
- Currency format: no $ sign in table cells, just "300.00" and "3,556.31"
- Status bar at bottom: "647 Transactions" on left, "Current Balance: 2,506.31" center, "Ending Balance: 543.81" right
- Scheduled/recurring transactions shown with clock icon (⏰) and slightly different styling
- Sidebar shows account groups with ▼ disclosure triangles, accounts indented below

**Screenshot 2 — Home Dashboard (Quicken Mac):**
- Title bar: "Jolene's Quicken File"
- Tab bar: Home, Reports ▾, Budgets ▾, Bills, Calendars ▾, Alerts
- Sidebar: Accounts with ▼ disclosure triangles, All Transactions at top
- "Overview" as page title
- "Spending By Category" with donut chart, "$4,463.49" total, "Last Month (Sep)" dropdown
- Donut has a hole with page indicators below (three dots)
- "Bill & Income Reminders" with "Next 7 Days" dropdown, "TODAY Oct 11" marker
- Bill items: status icon, name, "Due in 5 days", amount in red
- Bills listed: Cable Bill (-$150.00), Car Insurance (-$150.00), Cell Phone (-$90.00), Credit Card Payment (-$750.00), Internet Service (-$65.00), Transfer To Savings (-$200.00)
- "Budget" section at bottom with "$2,581 left"
- Net Worth at bottom of sidebar: $816,781

**Screenshot 3 — Home Dashboard (Quicken 2017 Windows):**
- Title: "Quicken 2017 Premier - Jolene's Finances - [Home]"
- Menu bar: File, Edit, View, Tools, Reports, Help
- Toolbar icons: arrows, sync, calculator, house, folder, sync, tag
- Tab bar: HOME, SPENDING, BILLS, PLANNING, INVESTING, PROPERTY & DEBT, ADD-ON SERVICES
- "Main View" subtitle, "Customize" button
- "See Where Your Money Goes" section — collapsible
- "LAST 30 DAYS SPENDING (9/2016 - 10/2016)"
- "TOTAL SPENDING $3,954 in All Categories All accounts"
- Donut chart with legend: Home, Auto & Tra(nsport), Bills & Util(ities), Food & Di(ning), Cash & ATM, Health & F(itness), Entertainm(ent), Total
- "Examine Your Spending" button below chart
- "Stay On Top of Monthly Bills" section — collapsible
- "BILL AND INCOME REMINDERS - NEXT 14 DAYS"
- Bill items: Overdue (red), Auto (automatic), with Payee, "Link it now", Due date
- "WHAT'S LEFT $823 in your checking accounts"
- Sidebar: Net Worth $373,787, Credit Score "View..." link

### Color Palette

```css
/* Primary */
--sidebar-bg: #F5F5F5;
--header-bg: #4A7AB5;     /* Steel blue tab bar */
--header-text: #FFFFFF;
--content-bg: #FFFFFF;

/* Text */
--text-primary: #333333;
--text-secondary: #666666;
--text-negative: #CC0000;  /* Red for negative values / debts */
--text-positive: #006600;  /* Green for positive values (optional) */

/* Table */
--row-alt: #F0F5FA;        /* Alternating row highlight */
--row-hover: #E3EDF7;      /* Row hover state */
--row-selected: #D0E0F0;   /* Selected/active row */
--border-light: #E0E0E0;   /* Table cell borders */

/* Chart Colors (consistent per category) */
--chart-home: #2E8B57;
--chart-auto: #6A5ACD;
--chart-bills: #DB7093;
--chart-food: #FF8C00;
--chart-cash: #4169E1;
--chart-health: #CD5C5C;
--chart-entertainment: #20B2AA;
--chart-tax: #808000;
--chart-other: #B0C4DE;
```

---

## Testing Strategy

### Manual Testing Checkpoints
After each phase, verify:

1. **Phase 1**: App starts, database is created, seed data is visible in SQLite
2. **Phase 2**: Sidebar shows all accounts with correct balances, groups collapse/expand, net worth is accurate
3. **Phase 3**: Can create, edit, delete transactions. Running balance is correct. Filters work. Amount displays match screenshot format.
4. **Phase 4**: Dashboard loads with chart showing real data. Bills list is populated. Spending totals are correct.
5. **Phase 5**: Can set budgets and see budget vs actual. Category management works.
6. **Phase 6**: Can CRUD bill reminders. Mark as paid creates transaction and advances date.
7. **Phase 7**: Reports generate with correct data. Charts render properly.
8. **Phase 8**: CSV import creates real transactions. Search returns correct results.

### Data Integrity Checks
After any phase that modifies transaction or account data:
- Sum of all transaction amounts for an account + initial balance = displayed balance in sidebar
- Net worth = sum of all account balances (including debts as negative)
- Running balance in register: last row's balance = account's current balance
- No orphaned transactions (all reference valid accounts)
- No orphaned categories in use by transactions
