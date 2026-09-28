# GoatStarter kit

A production-grade **Next.js 16** starter you can rebrand in five minutes.

## Quick start

```bash
npm install
npm run dev          # → http://localhost:3000  (runs in demo mode, no keys needed)
```

## Make it yours

Open this folder in **Claude Code** and say:

> **"set up this project"**  (or run **`/setup`**)

Claude interviews you for your **brand**, **logo**, **colors**, and the **API keys
this app needs**, then writes your `app.config.ts` and `.env.local` and boots it.
Prefer to do it by hand? Follow [`SETUP.md`](./SETUP.md) — every step names the
exact file to change.

## What's inside

```
app.config.ts            ← single source of truth (brand, copy, nav, integrations)
app/(marketing)/         ← landing page (config-driven)
app/(app)/               ← dashboard shell + pages
components/ui/           ← buttons, cards, badges, inputs…
components/app/          ← sidebar, topbar, KPI cards, charts
lib/demo/data.ts         ← sample data that powers demo mode
.env.example             ← the keys this kit can use (all optional)
SETUP.md                 ← the guided-setup script
```

## Stack

Next.js 16 (App Router) · React 19 · Tailwind v4 · lucide-react · recharts.
No database required to run — it falls back to realistic demo data.
