# Setup — make this kit yours

> **For the person who downloaded this:** open this folder in Claude Code and say
> **"set up this project"** (or run **`/setup`**). Claude will walk you through
> the questions below and wire everything up. You can also do it by hand — every
> step says exactly which file changes.

> **For Claude Code:** this is your script. Run the interview, then apply. Ask
> **one question at a time**. Accept "skip" / "keep default" for any answer.
> Never invent API keys.

---

## Step 0 — Orient

1. Read `app.config.ts` (the single source of truth) and `.env.example` (the keys
   this kit can use). The `integrations` array in `app.config.ts` explains what
   each key powers — use those descriptions when you ask.
2. Tell the user, in one sentence, what this app is (from `appConfig.description`)
   and that **it already runs in demo mode with no keys** — setup just makes it
   theirs.

> **Bilingual:** every copy field in `app.config.ts` is `{ tr, en }`. When you
> write answers, fill **both** languages (translate if the user gives one). The
> default language lives in `lib/i18n/config.ts` (`DEFAULT_LANG`) — ask the user
> if they want `tr` or `en` as default. `/login` + `/signup` already work as a
> demo bypass; they only do real auth once Supabase is wired below.

## Step 1 — Brand (ask, then edit `app.config.ts`)

Ask for each; write the answers into `app.config.ts` (both `tr` and `en`):

| Question | Field in `app.config.ts` |
|---|---|
| Product name? | `name` |
| One-line tagline? | `tagline` |
| One-sentence description? | `description` |
| Domain (e.g. `acme.app`)? | `domain` |
| 1–3 letter wordmark for the logo tile? | `logoText` |

Also offer to tailor the hero: `marketing.heroTitle`, `marketing.heroSubtitle`.
Keep it short — don't rewrite the whole config unless asked.

## Step 2 — Color (ask, then edit `app/globals.css`)

Ask: **"What's your brand color?"** (a name like *emerald*, a hex, or "keep default").

- Convert it to `oklch(...)` and update `--color-primary`, `--color-accent`, and
  `--color-ring` in the `@theme` block of `app/globals.css`.
- Optionally nudge `--color-sidebar` to a dark tint of the same hue.
- Quick recipe: pick the hue (H) of their color and reuse the existing L/C, e.g.
  emerald ≈ `oklch(58% 0.16 155)`, blue ≈ `oklch(58% 0.18 255)`,
  rose ≈ `oklch(60% 0.2 15)`, amber ≈ `oklch(70% 0.16 70)`.

## Step 3 — Logo (ask, then place file)

Ask: **"Do you have a logo file? Paste a path, or say 'use the text logo'."**

- If they give a path: copy it to `public/logo.svg` (or `.png`), then edit
  `components/ui/logo.tsx` to render `<img src="/logo.svg" .../>` instead of the
  gradient tile.
- If not: keep the gradient tile (it uses `logoText`). That's a fine default.

## Step 4 — Fonts (optional, edit `app/layout.tsx`)

Ask if they want a specific font vibe (modern / editorial / technical). If yes,
swap the three `next/font/google` imports in `app/layout.tsx`. Keep the CSS
variable names (`--font-sans-app`, `--font-display-app`, `--font-mono-app`).

## Step 5 — API keys (ask per integration, then write `.env.local`)

For **each** entry in `appConfig.integrations` (and each var in `.env.example`):

1. Say what it powers (use `integration.purpose`) and link `integration.docsUrl`.
2. Ask: **"Do you want to connect `<name>` now? Paste the key, or say 'later'."**
3. If they paste a value, add it to `.env.local`. If "later", leave it blank —
   that feature stays in demo mode and the app still runs.

Create `.env.local` by copying `.env.example` and filling only what they gave you.
**Never commit `.env.local`** (it's already gitignored).

## Step 6 — Boot

```bash
npm install
npm run dev
```

Open the printed URL (usually http://localhost:3000). Then tell the user:

- ✅ what's **live** (integrations whose keys are set), and
- 🟡 what's still in **demo mode** (and how to enable it later — just re-run setup).

## Step 7 — Optional next steps

- Deploy: push to GitHub and import into Vercel; add the same env vars there.
- Replace `lib/demo/data.ts` with real queries once an integration is connected.
- Add pages: copy an existing file in `app/(app)/…` and add a `nav` entry in
  `app.config.ts`.
