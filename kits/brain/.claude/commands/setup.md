---
description: Guided, beginner-friendly setup — brand this kit and take it live, step by step with the visual guide.
---

You are guiding a possibly **non-technical** person through setting up this kit.
Be warm, plain-spoken, and **ask one thing at a time**. Never dump jargon. The
folder `setup-guide/` has 5 images that match the steps below — **open the
matching image at the start of each step** so the user can follow visually.

To open an image on macOS run: `open "setup-guide/<file>.png"` (on Windows:
`start`, on Linux: `xdg-open`). If opening fails, just tell them the file path.

## Step 0 — Overview (do this first)

1. Run `open "setup-guide/0-overview.png"`.
2. In 2-3 sentences explain the journey: **Claude Code** (brand the app) →
   **Supabase** (free backend) → **GitHub** (save code) → **Vercel** (go live) →
   **Stripe** (payments). Reassure them you'll handle the technical parts.
3. Ask: *"Want to brand it first, or just deploy the demo as-is?"*

## Step 1 — Build / Brand it (`open "setup-guide/1-build-with-claude.png"`)

Read `app.config.ts` first (it's the single source of truth). Then interview —
**one question at a time**, "skip" / "keep default" always allowed:
- Brand **name** + **tagline**
- **Logo**: ask for an SVG/PNG path, or offer to keep the generated SVG logomark
- **Brand color(s)** (a hex or "keep default")
- Any **marketing copy** they want changed

Apply answers to: `app.config.ts`, `app/globals.css` (colors), `app/layout.tsx`
(fonts, optional), `public/logo.svg` (if they gave a logo). Keep **both TR + EN**
for every string you touch. Show them `npm run dev` so they see it live locally.

## Step 2 — Supabase / backend (`open "setup-guide/2-connect-supabase.png"`)

Only if they want real data/login (the kit works in demo mode without it).
1. Explain: Supabase is a **free** backend (database + login).
2. Walk them: go to supabase.com → New project → copy **Project URL** + **anon key**
   from Settings → API.
3. Read this kit's required keys from `app.config.ts` (the `integrations` list) —
   ask for **each app-specific API key** that kit needs, one at a time, explaining
   what it's for and where to get it. **Never invent keys.**
4. Write everything to `.env.local` (copy from `.env.example`).

## Step 3 — GitHub (`open "setup-guide/3-push-to-github.png"`)

Walk them: create a repo on github.com → then run, in this folder:
`git init && git add . && git commit -m "my app" && git branch -M main &&
git remote add origin <their-repo-url> && git push -u origin main`.
Explain it just saves their code in the cloud.

## Step 4 — Vercel / go live (`open "setup-guide/4-deploy-to-vercel.png"`)

Walk them: vercel.com → New Project → import the GitHub repo → add the same
**environment variables** from `.env.local` → Deploy. They get a live URL.

## Step 5 — Stripe / payments (optional)

If the app charges money: stripe.com → get the **publishable + secret keys** →
add to `.env.local` and Vercel env. Explain test vs live mode.

## Finish

Run `npm install` then `npm run dev`, confirm it boots, and report the local URL.
Summarize what's done and what's left (e.g. "add your Stripe key when ready").
Congratulate them — their app is theirs now. 🎉
