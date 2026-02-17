# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Closed Ledger is a local-first, single-user personal finance desktop app modeled after Quicken Classic (2013-2017). No cloud, no auth, no external APIs — everything runs on localhost:3000 with a single SQLite file.

## Build & Dev Commands

```bash
npm install              # Install dependencies
npm run dev              # Start dev server (localhost:3000)
npm run build            # Production build
npm start                # Start production server
npm run db:generate      # Generate Drizzle migrations from schema
npm run db:migrate       # Run pending migrations (tsx src/lib/db/migrate.ts)
npm run db:seed          # Seed database with demo data (tsx src/lib/db/seed.ts)
npx tsc --noEmit         # TypeScript check (no test framework configured)
```

## Tech Stack

Next.js 14 (App Router), TypeScript (strict), SQLite via better-sqlite3, Drizzle ORM, Tailwind CSS 3, Recharts, date-fns, Lucide React. Scripts run via `tsx`.

## Architecture

### Key Reference Files

- **README.md** — Project overview, tech stack rationale, data model diagram
- **IMPLEMENTATION.md** — Full technical spec: schema definitions, UI column specs, color palette, category seed list, phase-by-phase details
- **INSTRUCTIONS.md** — Phased Claude Code workflow with copy-paste prompts and testing checklists

**Read IMPLEMENTATION.md before starting any phase.** It is the source of truth for schema, UI specs, and conventions.

### Development Phases

The project is built in 8 sequential phases, each designed for a fresh Claude Code session:

1. Foundation (Next.js setup, schema, migrations, seed data, layout shell)
2. Account Sidebar (live balances, groups, CRUD, net worth)
3. Transaction Register (table, CRUD, inline editing, filters, running balance)
4. Home Dashboard (spending donut chart, bill reminders, budget summary)
5. Categories & Budgets (category CRUD, budget tracking, progress bars)
6. Bills & Scheduling (bill CRUD, mark-as-paid, recurring date advancement)
7. Reports & Analytics (spending over time, net worth, income vs expenses, category breakdown)
8. Polish (CSV import/export, Cmd+K search, keyboard shortcuts, backup/restore)

### Server vs Client Components

Server components by default for all data reads. Client components (`"use client"`) only for: forms, dropdowns, charts (Recharts requires it), click handlers, `usePathname`. Data mutations go through API routes (`src/app/api/`).

### Data Conventions

- **All monetary values stored as integers in cents** (e.g., `$1,234.56` → `123456`). Conversion to dollars only in the UI layer.
- **Negative amounts** = money leaving account (payments, expenses). **Positive** = money entering (deposits, income).
- **Account balances are never stored** — always computed: `initialBalance + SUM(transactions.amount)`.
- **Transfers** create two linked transactions referencing each other via `transferTransactionId`.
- **Running balance** in register: sort by `date ASC, id ASC`, accumulate from `initialBalance`.
- **Dates** stored as TEXT in ISO format. Display format in register: `M/D/YYYY` (no zero-padding).
- **Currency in transaction table**: no `$` sign, just `"300.00"` (tabular-nums). In sidebar/dashboard: `$1,234` format with `$` sign.

### Database

SQLite file at `data/closed-ledger.db`. The `data/` directory is gitignored but must never be deleted by any build step. Drizzle migrations in `drizzle/` are committed. Schema source of truth: `src/lib/db/schema.ts`. Five tables: accounts, transactions, categories, bill_reminders, budgets.

### Color Palette

```
Sidebar: #F5F5F5 | Header: #4A7AB5 (steel blue) | Negative: #CC0000 (red) | Positive: #006600
Row alt: #F0F5FA | Row hover: #E3EDF7 | Row selected: #D0E0F0 | Borders: #E0E0E0
```

### UI Density

Dense layout matching Quicken: 13-14px base font, 30-34px row heights, 240px fixed sidebar. Negative balances in red.
