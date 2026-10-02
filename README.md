# Token Snack by Vikas

**A daily snack for token optimization.**

**Read every day:** [https://token-snack.vercel.app/](https://token-snack.vercel.app/)

Brand mark: three tiles (green · purple · bitten orange snack) — see `assets/logo.svg` and `assets/favicon.svg`. Homepage hero and social preview use `assets/hero-banner.png` / `assets/og-banner.jpg` (no domain URL in the art).

## Why the name?

LLMs bill in tokens. Attention is a token too. Most “AI news” burns both — long feeds, hype, and tools you will never open.

**Token Snack** is a small daily bite: a few verified AI tooling picks that help you code smarter and spend tokens (and time) on what actually matters. Snack-sized. Eval-gated. Not a buffet of slop.

## What this is

Token Snack is a short daily brief on what is going on in AI tooling — the kind of updates that help a software engineer code faster, stay current, and actually use new tools the same week they ship.

I started it for myself. I am a software engineer, a PhD research scholar (working on ideas around semantic code knowledge graphs), and an entrepreneur at heart who wants to build real things. Every day there is too much news: new models, new CLIs, LinkedIn threads, YouTube videos, research notes. I needed one place that answers a simple question:

> What changed today that can make my coding life easier — and what research or product work is worth my attention?

So I built a private pipeline that gathers candidates, cuts hard, and runs a serious evaluation before anything reaches me. I get a daily email. I mark things useful or not useful. That feedback makes the next day’s filter better. All of that eval and personal feedback lives in my own setup — it is not dumped into this public repo.

**What you see here is only the final, filtered result.** After that personal filtration, the brief that clears the bar is published on this website, every day, for anyone who wants the same help.

This is not AI slop. Links are first-party. Claims are checked. Items that fail the eval do not make it. If you read Token Snack regularly, you should walk away knowing what is going on and what you can try today — not feeling buried in hype.

## Feedback

I want this to be useful for you, not only for me. If something should be better — topics, length, format, sources — please connect on LinkedIn and message me:

**[Connect on LinkedIn →](https://www.linkedin.com/in/vikas008/)**

Like / dislike notes on items and general suggestions both help. Thank you for using Token Snack.

## What you will find on the site

Each day’s edition is short on purpose. Sections may include:

- **Shipped** — real product or tooling changes you can try
- **On LinkedIn** — concrete posts you can apply this week
- **Trending on X** — signal with a clear “where do I use this” angle
- **Study** — deeper tools or research worth a look (including open source)
- **Watch Queue** — a couple of videos worth listening to while driving or commuting

An empty section (or even an empty day) is fine. Better nothing than filler.

Browse the archive, subscribe via RSS, or open a dated page such as [token-snack.vercel.app/2026-10-02/](https://token-snack.vercel.app/2026-10-02/).

## Installation (run the site locally)

You need **Python 3.12+** (no pip packages required) and **git**.

```bash
git clone https://github.com/vikas434/token-snack.git
cd token-snack
python3 scripts/build.py --check          # validate all briefs
python3 scripts/build.py                  # write HTML into _site/
python3 -m http.server -d _site 8000      # open http://127.0.0.1:8000
```

The live site is built the same way on [Vercel](https://token-snack.vercel.app/) from [`vercel.json`](vercel.json) (`buildCommand` → `_site`).

## Contribution guide

Thank you for wanting to help. Two paths:

### 1. Improve the brief (readers)

The daily picks are curated through a private eval pipeline. The best contribution is **feedback** on what was useful or not, and what you wish the brief covered — connect on LinkedIn and message me:

**[Connect on LinkedIn →](https://www.linkedin.com/in/vikas008/)**

Please do **not** open PRs that only add random news links to `data/briefs/` without going through that quality bar. Empty days and hard cuts are intentional.

### 2. Improve the website (engineers)

PRs are welcome for the **public renderer and docs**, for example:

- Clearer layout, accessibility, or print styles in `assets/style.css`
- Safer validation or clearer errors in `scripts/build.py`
- README / schema docs that help new readers
- Bug fixes in RSS, archive, markdown, or standalone HTML output

Suggested flow:

1. Fork the repo and create a branch.
2. Run `python3 scripts/build.py --check` and a local preview before you open a PR.
3. Keep changes focused. Do not commit `_site/` (it is gitignored and rebuilt on deploy).
4. Never add emails, API keys, private Google / Claude links, or personal notes to public brief JSON — the build will reject them.
5. Open a PR against `main` with a short note on *why* the change helps readers.

Repo layout:

```
data/briefs/YYYY-MM-DD.json   ← daily public brief (from the private pipeline)
scripts/build.py              ← validate + render _site/
assets/style.css
.github/workflows/pages.yml
vercel.json
```

### Brief schema (for contributors)

```jsonc
{
  "date": "2026-10-02",
  "notice": "optional",
  "skipped": [{ "section": "WATCH QUEUE", "reason": "…" }],
  "items": [{
    "slug": "unique-kebab",
    "section": "SHIPPED | ON LINKEDIN | TRENDING ON X | STUDY | WATCH QUEUE",
    "title": "…",
    "summary": "optional",
    "why": "one plain sentence",
    "actionLabel": "Try this | Angle for you | Worth the drive",
    "action": "one concrete step",
    "permalink": "https://…",
    "image": "https://…",
    "watch": { "label": "…", "url": "https://…" },
    "eval": [{ "check": "Meaningful", "result": "PASS | FAIL | N/A", "reason": "…" }]
  }],
  "dropped": [{ "title": "…", "stage": "step 3 | eval gate", "reason": "…" }]
}
```

### Public data only

This repo and the site are public. The build fails if a brief contains emails, phone numbers, private Google / `claude.ai` links, or API-key-shaped secrets. Keep eval reasons short and public. Personal feedback stays in the private pipeline — not in these files.
