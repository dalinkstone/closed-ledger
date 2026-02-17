# IMPLEMENTATION.md — Closed Ledger Development Plan

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

2. **Data is sacred.** The SQLite database in `data/closed-ledger.db` must never be deleted by any build step, script, or migration. Migrations must be additive and non-destructive. Every write operation should be wrapped in a transaction.

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
  institution: text('institution'),
  initialBalance: integer('initial_balance').notNull().default(0),
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
  date: text('date').notNull(),
  payee: text('payee').notNull().default(''),
  memo: text('memo').default(''),
  categoryId: integer('category_id').references(() => categories.id),
  tag: text('tag').default(''),
  amount: integer('amount').notNull(),
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
  amount: integer('amount').notNull(),
  categoryId: integer('category_id').references(() => categories.id),
  accountId: integer('account_id').references(() => accounts.id),
  frequency: text('frequency', { 
    enum: ['weekly', 'biweekly', 'monthly', 'quarterly', 'annually', 'once'] 
  }).notNull().default('monthly'),
  nextDueDate: text('next_due_date').notNull(),
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
  amount: integer('amount').notNull(),
  year: integer('year').notNull(),
  month: integer('month').notNull(),
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
```typescript
// src/lib/db/index.ts
import Database from 'better-sqlite3';
import { drizzle } from 'drizzle-orm/better-sqlite3';
import { migrate } from 'drizzle-orm/better-sqlite3/migrator';
import path from 'path';
import fs from 'fs';

const DB_PATH = path.join(process.cwd(), 'data', 'closed-ledger.db');
fs.mkdirSync(path.dirname(DB_PATH), { recursive: true });

const sqlite = new Database(DB_PATH);
sqlite.pragma('journal_mode = WAL');
sqlite.pragma('foreign_keys = ON');

export const db = drizzle(sqlite, { schema });
migrate(db, { migrationsFolder: './drizzle/migrations' });
```

### Layout Shell
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
│    ...              │                                           │
│                     │                                           │
│  Net Worth $373,787 │                                           │
│  + Add an Account   │                                           │
└─────────────────────┴───────────────────────────────────────────┘
```

---

## Phase 2: Account Sidebar

### Goal
A fully interactive account sidebar matching the Quicken screenshots, with real-time balance computation, collapsible groups, and account management.

### Balance Computation
```sql
SELECT a.*, (a.initial_balance + COALESCE(SUM(t.amount), 0)) as current_balance
FROM accounts a LEFT JOIN transactions t ON t.account_id = a.id
WHERE a.is_hidden = 0 GROUP BY a.id ORDER BY a.group, a.sort_order, a.name
```

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

### Column Specification (from Screenshot 1)

| Column | Width | Align | Content |
|--------|-------|-------|---------|
| Status | 30px | center | Icons: ⓘ (info), ⏰ (scheduled), ✓ (reconciled) |
| Flag | 24px | center | Red flag icon for flagged transactions |
| Date | 90px | left | M/D/YYYY format |
| Check # | 60px | left | Optional check number |
| Payee | 200px | left | Payee name |
| Memo | 150px | left | Optional notes |
| Category | 200px | left | Full category path "Parent:Child" |
| Tag | 80px | left | Optional tag |
| ✓ (Cleared) | 24px | center | Cleared/reconciled checkbox |
| Payment | 90px | right | Amount if negative, formatted without sign |
| Deposit | 90px | right | Amount if positive |
| Balance | 100px | right | Running balance |

### Running Balance
```
runningBalance[0] = account.initialBalance + transaction[0].amount
runningBalance[i] = runningBalance[i-1] + transaction[i].amount
```

---

## Phase 4: Home Dashboard

### Dashboard Layout
```
┌─────────────────────────────────────────────────┐
│  Overview                                       │
│  ┌─ Spending By Category ────────────────────┐  │
│  │            [DONUT CHART]    Last Month ▼   │  │
│  │         TOTAL SPENDING $4,463.49          │  │
│  └───────────────────────────────────────────┘  │
│  ┌─ Bill & Income Reminders ─────────────────┐  │
│  │  TODAY: Feb 16          Next 7 Days  ▼    │  │
│  │  ⏰ Cable Bill        Due in 5 days  -$150│  │
│  │  ⏰ Car Insurance     Due in 5 days  -$150│  │
│  └───────────────────────────────────────────┘  │
│  ┌─ Budget ──────────────────────────────────┐  │
│  │  $2,581 left                              │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

### Category Color Mapping
- Home: Green (#2E8B57)
- Auto & Transport: Purple (#6A5ACD)
- Bills & Utilities: Pink (#DB7093)
- Food & Dining: Orange (#FF8C00)
- Cash & ATM: Blue (#4169E1)
- Health & Fitness: Red (#CD5C5C)
- Entertainment: Teal (#20B2AA)
- Tax: Olive (#808000)
- Other: Light Steel Blue (#B0C4DE)

---

## UI Reference Notes

### Key Visual Details from Screenshots

**Screenshot 1 — Transaction Register (Quicken 2013 Windows):**
- Title shows "Family Checking" as page header
- Steel blue tab bar: Home, Spending, Bills, Planning, Investing, Property & Debt
- Filter bar: "All Dates", "Any Type", "All Transactions" + Reset button
- Alternating rows: white and light blue (#F0F5FA)
- Date format: M/D/YYYY (8/5/2013, not 08/05/2013)
- Currency: no $ sign in cells, just "300.00" and "3,556.31"
- Status bar: "647 Transactions" left, "Current Balance: 2,506.31" center, "Ending Balance: 543.81" right
- Scheduled transactions with clock icon (⏰)

**Screenshot 2 — Home Dashboard (Quicken Mac):**
- "Overview" page title, "Spending By Category" donut chart
- "$4,463.49" total, "Last Month (Sep)" dropdown
- "Bill & Income Reminders" with "Next 7 Days" dropdown, "TODAY Oct 11"
- Bills: Cable Bill (-$150), Car Insurance (-$150), Cell Phone (-$90), Credit Card Payment (-$750), Internet Service (-$65), Transfer To Savings (-$200)
- Net Worth: $816,781

**Screenshot 3 — Home Dashboard (Quicken 2017 Windows):**
- "LAST 30 DAYS SPENDING (9/2016 - 10/2016)", "TOTAL SPENDING $3,954"
- Donut with legend: Home, Auto & Transport, Bills & Utilities, Food & Dining, Cash & ATM, Health & Fitness, Entertainment
- "BILL AND INCOME REMINDERS - NEXT 14 DAYS" with Overdue (red) and Auto items
- "WHAT'S LEFT $823 in your checking accounts"
- Net Worth $373,787

### Color Palette

```css
--sidebar-bg: #F5F5F5;
--header-bg: #4A7AB5;
--header-text: #FFFFFF;
--content-bg: #FFFFFF;
--text-primary: #333333;
--text-secondary: #666666;
--text-negative: #CC0000;
--text-positive: #006600;
--row-alt: #F0F5FA;
--row-hover: #E3EDF7;
--row-selected: #D0E0F0;
--border-light: #E0E0E0;
```

---

## Testing Strategy

### Data Integrity Checks (run after any phase)
- Sum of all transaction amounts for an account + initial balance = displayed balance in sidebar
- Net worth = sum of all account balances
- Running balance in register: last row's balance = account's current balance
- No orphaned transactions (all reference valid accounts)
- No orphaned categories in use by transactions
