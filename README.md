# Closed Ledger — A Quicken-Inspired Personal Finance Manager

> A full-featured, single-user personal finance desktop application modeled after Quicken Classic (circa 2013–2017). Built as a local-first web application with persistent SQLite storage.

---

## Overview

Closed Ledger is a faithful recreation of Intuit's Quicken personal finance software — specifically the Quicken Premier 2013–2017 era desktop experience. It provides comprehensive personal finance management including account tracking, transaction registers, budgeting, bill reminders, spending analysis, and net worth calculation — all running locally on your machine with zero cloud dependency.

This project exists as a learning exercise and personal tool. It is not affiliated with Quicken Inc. or Intuit.

## Screenshots Reference

The UI is modeled after three core views captured from Quicken:

1. **Transaction Register** — The primary data entry view. A spreadsheet-like table showing Date, Check #, Payee, Memo, Category, Tag, Payment, Deposit, and running Balance. Includes filter bar (date range, transaction type) and a status bar showing transaction count and current/ending balance.

2. **Home Dashboard (Mac variant)** — The overview landing page featuring a "Spending By Category" donut chart with dollar total, a "Bill & Income Reminders" section showing upcoming bills with due dates and amounts, and a Budget summary. Left sidebar shows all accounts grouped by type with balances.

3. **Home Dashboard (Windows 2017)** — Similar overview with "See Where Your Money Goes" spending donut chart showing last 30 days of spending, "Stay On Top of Monthly Bills" reminder section, and a "What's Left" remaining budget indicator. Includes net worth and credit score in the sidebar.

## Architecture

### Tech Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Runtime** | Node.js 20+ | Universal JS runtime |
| **Framework** | Next.js 14 (App Router) | Full-stack React framework with API routes |
| **Language** | TypeScript (strict) | Type safety across the entire codebase |
| **Database** | SQLite via `better-sqlite3` | Single-file persistent storage, zero config, survives rebuilds |
| **ORM** | Drizzle ORM | Type-safe schema definitions, migrations, and queries |
| **Styling** | Tailwind CSS 3 | Utility-first CSS matching Quicken's dense UI |
| **Charts** | Recharts | React-native charting (donut charts, bar charts, line charts) |
| **Date Handling** | date-fns | Lightweight date manipulation |
| **Icons** | Lucide React | Clean, consistent icon set |
| **State** | React Context + Server Components | Minimal client state, server-driven data |

### Why This Stack?

- **SQLite** is the cornerstone choice. The database file (`closed-ledger.db`) lives in a `data/` directory at the project root. It persists across `npm run dev` restarts, rebuilds, and even full `node_modules` wipes. This mirrors how Quicken stored everything in a single `.qdf` file.
- **Next.js App Router** gives us server components for heavy data queries (transaction lists, reports) and API routes for mutations — all in one process.
- **Drizzle ORM** provides type-safe schema definitions that double as documentation and enable auto-migrations.
- **No external services** — everything runs on `localhost:3000`. No accounts, no API keys, no cloud.

### Data Persistence Strategy

```
project-root/
├── data/
│   └── closed-ledger.db   ← SQLite database (GITIGNORED but never deleted)
├── drizzle/
│   └── migrations/         ← Schema migration files (COMMITTED)
└── src/
    └── lib/
        └── db/
            ├── schema.ts   ← Drizzle schema definitions
            ├── index.ts    ← Database connection singleton
            └── seed.ts     ← Optional demo data seeder
```

The `data/` directory is `.gitignore`d but created automatically on first run. The database file survives:
- `npm run build` / `npm run dev` restarts
- `rm -rf node_modules && npm install`
- Git operations (it's gitignored, not deleted)

A seed script is provided to populate the database with realistic demo data matching the Quicken screenshots.

### Data Model (Core Entities)

```
┌─────────────┐     ┌──────────────────┐     ┌──────────────┐
│   Account    │────<│   Transaction    │>────│   Category   │
│              │     │                  │     │              │
│ id           │     │ id               │     │ id           │
│ name         │     │ date             │     │ name         │
│ type         │     │ payee            │     │ parent_id    │
│ group        │     │ memo             │     │ type         │
│ balance      │     │ category_id      │     └──────────────┘
│ is_debt      │     │ amount           │
│ institution  │     │ check_number     │     ┌──────────────┐
│ sort_order   │     │ tag              │     │   Budget     │
└─────────────┘     │ is_reconciled    │     │              │
                     │ account_id       │     │ category_id  │
                     │ transfer_acct_id │     │ amount       │
                     └──────────────────┘     │ period       │
                                               │ month/year   │
┌─────────────────┐                            └──────────────┘
│  BillReminder   │
│                 │
│ id              │
│ name            │
│ amount          │
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
- Account sidebar with grouped accounts (Banking, Investing, Property & Debt, Savings Goals)
- Running account balances and Net Worth calculation
- Full transaction register with inline editing
- Transaction filtering (date range, type, category, payee search)
- Hierarchical categories (e.g., "Food & Dining:Restaurants")
- Home dashboard with spending donut chart
- Bill & Income reminders with due date tracking

### Extended Features (Phase 5–7)
- Budget creation and tracking with monthly comparisons
- Spending tab with detailed category breakdowns
- Recurring/scheduled transactions
- Reports: Spending Over Time, Net Worth Over Time, Category Comparison
- Data import (CSV) and export
- Transaction search across all accounts

### Nice-to-Have (Phase 8)
- Keyboard shortcuts for power users
- Dark mode
- Printable reports
- Data backup/restore

## Getting Started

```bash
# Install dependencies
npm install

# Run database migrations
npm run db:migrate

# (Optional) Seed with demo data matching Quicken screenshots
npm run db:seed

# Start development server
npm run dev

# Open in browser
open http://localhost:3000
```

## Project Structure

```
src/
├── app/                          # Next.js App Router
│   ├── layout.tsx                # Root layout with sidebar
│   ├── page.tsx                  # Home dashboard
│   ├── accounts/
│   │   └── [id]/
│   │       └── page.tsx          # Transaction register for account
│   ├── spending/
│   │   └── page.tsx              # Spending analysis
│   ├── bills/
│   │   └── page.tsx              # Bill reminders management
│   ├── budgets/
│   │   └── page.tsx              # Budget tracking
│   ├── reports/
│   │   └── page.tsx              # Reports hub
│   └── api/                      # API routes for mutations
│       ├── accounts/
│       ├── transactions/
│       ├── categories/
│       ├── bills/
│       └── budgets/
├── components/
│   ├── layout/
│   │   ├── Sidebar.tsx           # Account sidebar (always visible)
│   │   ├── TopNav.tsx            # Tab navigation bar
│   │   └── StatusBar.tsx         # Bottom status bar
│   ├── accounts/
│   │   ├── AccountGroup.tsx      # Collapsible account group
│   │   └── AccountForm.tsx       # Add/edit account modal
│   ├── transactions/
│   │   ├── TransactionTable.tsx  # Main register table
│   │   ├── TransactionRow.tsx    # Editable row
│   │   ├── TransactionForm.tsx   # New transaction form
│   │   └── FilterBar.tsx         # Date/type/category filters
│   ├── dashboard/
│   │   ├── SpendingChart.tsx     # Donut chart component
│   │   ├── BillReminders.tsx     # Upcoming bills widget
│   │   ├── BudgetSummary.tsx     # Budget progress widget
│   │   └── WhatsLeft.tsx         # Remaining budget widget
│   └── shared/
│       ├── Currency.tsx          # Formatted currency display
│       ├── DatePicker.tsx        # Date input component
│       └── Modal.tsx             # Reusable modal
├── lib/
│   ├── db/
│   │   ├── schema.ts            # Drizzle schema
│   │   ├── index.ts             # DB connection
│   │   ├── seed.ts              # Demo data seeder
│   │   └── queries/             # Reusable query functions
│   ├── utils/
│   │   ├── currency.ts          # Currency formatting helpers
│   │   ├── dates.ts             # Date utilities
│   │   └── categories.ts        # Category tree helpers
│   └── types/
│       └── index.ts             # Shared TypeScript types
└── styles/
    └── globals.css              # Tailwind base + Quicken-specific styles
```

## Design Language

The UI closely follows Quicken's visual conventions:

- **Color Palette**: Steel blue header bar (`#4A7AB5`), white content area, light gray sidebar (`#F5F5F5`), red for debts/negative values, green/blue for positive
- **Typography**: System font stack, 13–14px base for dense data display
- **Layout**: Fixed left sidebar (240px), fixed top tab bar, scrollable content area
- **Tables**: Dense row height (~32px), alternating row colors, right-aligned numbers
- **Negative values**: Displayed in red (e.g., `-$283,043`), positive in black or dark gray
- **Account Groups**: Collapsible sections with bold group headers and indented accounts

## License

MIT — This is an educational project. Not affiliated with Quicken Inc.
