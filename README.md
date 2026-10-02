# Token Snack by Vikas

**Read every day:** [https://token-snack.vercel.app/](https://token-snack.vercel.app/)

## What this is

Token Snack is a short daily brief on what is going on in AI tooling — the kind of updates that help a software engineer code faster, stay current, and actually use new tools the same week they ship.

I started it for myself. I am a software engineer, a PhD research scholar (working on ideas around semantic code knowledge graphs), and an entrepreneur at heart who wants to build real things. Every day there is too much news: new models, new CLIs, LinkedIn threads, YouTube videos, research notes. I needed one place that answers a simple question:

> What changed today that can make my coding life easier — and what research or product work is worth my attention?

So I built a private pipeline that gathers candidates, cuts hard, and runs a serious evaluation before anything reaches me. I get a daily email. I mark things useful or not useful. That feedback makes the next day’s filter better. All of that eval and personal feedback lives in my own setup — it is not dumped into this public repo.

**What you see here is only the final, filtered result.** After that personal filtration, the brief that clears the bar is published on this website, every day, for anyone who wants the same help.

This is not AI slop. Links are first-party. Claims are checked. Items that fail the eval do not make it. If you read Token Snack regularly, you should walk away knowing what is going on and what you can try today — not feeling buried in hype.

## Feedback

I want this to be useful for you, not only for me. If something should be better — topics, length, format, sources — please tell me:

**[Send feedback →](https://claude.ai/code/artifact/0623b2e2-d9bb-417a-b18d-ce1d1ee61fb4)**

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

## For builders of this repo

Public content only. Every day one JSON file is written; Vercel (and optionally GitHub Actions) builds the static site from it. The live site is [https://token-snack.vercel.app/](https://token-snack.vercel.app/).

```
data/briefs/YYYY-MM-DD.json   ← daily public brief
scripts/build.py              ← validate + render _site/
assets/style.css
.github/workflows/pages.yml
vercel.json
```

```bash
python3 scripts/build.py --check
python3 scripts/build.py && python3 -m http.server -d _site 8000
```

### Brief schema

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
