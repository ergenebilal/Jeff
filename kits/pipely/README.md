# Pipely — GoatStarter kit

**A pipeline your sales team will actually update.** A sales CRM with a visual
deal pipeline (contacts, deals, activities, forecasting), inspired by **Pipedrive**
and **HubSpot CRM**. A production-grade **Next.js 16** starter (light, clean
design) you can rebrand in five minutes.

## Quick start

```bash
npm install
npm run dev          # → http://localhost:3000  (runs in demo mode, no keys needed)
```

## Make it yours

Open this folder in **Claude Code** and:

> open **`START-HERE.md`** — or just say **"set up this project"** (or run **`/setup`**)

Claude interviews you for your **brand**, **logo**, **colors**, and the **API keys
this app needs**, then writes your `app.config.ts` and `.env.local` and boots it.
Prefer to do it by hand? Follow [`SETUP.md`](./SETUP.md) — every step names the
exact file to change.

## What's inside

```
app.config.ts            ← single source of truth (brand, copy, nav, integrations)
app/(marketing)/         ← landing page (config-driven, interactive pipeline demo)
app/(app)/               ← dashboard cockpit + Pipeline (Deals) + Contacts + Settings
components/ui/           ← buttons, cards, badges, inputs, the pipeline logomark
components/app/          ← sidebar, topbar, SVG charts, SVG-initial avatars
components/marketing/    ← interactive pipeline demo + inline-SVG company marks
lib/demo/data.ts         ← sample deals, contacts, activities, forecast (demo mode)
.env.example             ← the keys this kit can use (all optional)
SETUP.md                 ← the guided-setup script
```

## The product

- **Visual pipeline** — a drag-and-drop kanban (Lead → Qualified → Proposal →
  Negotiation → Won). Move a deal and pipeline value + win rate recompute live.
- **Deals & contacts** — a deals list view and a contacts panel; every deal ties
  back to a person and a company.
- **Activities** — calls, emails and meetings due today, check them off.
- **Forecasting** — a probability-weighted, month-by-month revenue forecast,
  hand-rolled inline SVG (no chart library).
- **Rep leaderboard** — quota attainment per rep.

## Stack

Next.js 16 (App Router) · React 19 · Tailwind v4 · lucide-react · Plus Jakarta
Sans + JetBrains Mono. Charts and avatars are hand-rolled inline SVG (no chart
lib, **no photos** — every person is SVG initials). No database required to run —
it falls back to realistic demo data.

## Integrations (all optional)

Supabase (db & auth) · Google Workspace / Outlook (email & calendar sync) ·
Clearbit (lead enrichment) · Slack (deal notifications). Run `/setup` and Claude
collects the keys you want and writes `.env.local`.
