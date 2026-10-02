# Token Snack by Vikas

[Token Snack](https://token-snack.in) is a daily AI tooling brief curated by Vikas for engineers who ship with agents, IDEs, and model APIs — and who would rather spend five minutes on signal than an hour on hype.

AI tooling moves every day: new CLI capabilities, open-source harnesses, workflow tips, and “listen while driving” videos. Most of that stream is noise — pricing posts, benchmark theater, and aggregator links. Token Snack cuts hard, keeps only first-party permalinks, and runs a five-check eval gate before anything reaches the page. An empty day is a valid outcome. That discipline is the product.

**Read the latest edition:** [https://token-snack.in](https://token-snack.in)

## Why it matters

- **Depth over volume.** A few verified picks beat a long digest. Ceilings (not quotas) keep the brief short enough to finish after work.
- **Actionable, not ornamental.** Every item includes why it matters and a concrete next step — try this, angle for you, or worth the drive.
- **Eval before publish.** Meaningful, link works, summary accurate, watch material, worth his time — any FAIL drops the item.
- **Public and private stay separate.** This repo and the live site hold only public brief data. No emails, secrets, or private links.

## What you get on the site

- Daily editions at [token-snack.in](https://token-snack.in) and dated permalinks such as [token-snack.in/2026-10-02/](https://token-snack.in/2026-10-02/)
- Sections: Shipped, On LinkedIn, Trending on X, Study, Watch Queue
- Archive of past briefs, RSS, Markdown and standalone HTML twins per day
- Dark / light theme and a print-friendly layout

## How the repo works

Every day the curation job writes one public JSON file. GitHub Actions validates it, builds the static site, and deploys to Pages at [token-snack.in](https://token-snack.in).

```
data/briefs/YYYY-MM-DD.json   ← the only thing the routine writes each day
scripts/build.py              ← validates every brief + renders _site/ (no dependencies)
assets/style.css
.github/workflows/pages.yml   ← build + deploy on every push to main
```

Local preview:

```bash
python3 scripts/build.py && python3 -m http.server -d _site 8000
```

Validate only:

```bash
python3 scripts/build.py --check
```

## Deploy (GitHub Pages + Vercel)

The site is **not** a Node app. There is no root `index.html` in git — Python writes HTML into `_site/` (gitignored). That is why a bare Vercel import shows `NOT_FOUND` at https://token-snack.vercel.app/ until a build is configured.

- **GitHub Pages** — Actions runs `scripts/build.py` and publishes `_site/` (custom domain [token-snack.in](https://token-snack.in)).
- **Vercel** — [`vercel.json`](vercel.json) sets `buildCommand` to the same Python build and `outputDirectory` to `_site`. In the Vercel project, Framework Preset should be **Other**, Output Directory **`_site`**.

## Brief schema

```jsonc
{
  "date": "2026-10-02",                 // must equal the file name
  "notice": "optional one-line note shown at the top (e.g. sections skipped)",
  "skipped": [{ "section": "WATCH QUEUE", "reason": "…" }],
  "items": [                            // [] on a "nothing cleared the bar" day
    {
      "slug": "codegraph-code-knowledge-graph",   // unique, lowercase-kebab
      "section": "SHIPPED | ON LINKEDIN | TRENDING ON X | STUDY | WATCH QUEUE",
      "title": "…",
      "summary": "optional — omit the key when the title is enough",
      "why": "one plain-English sentence",
      "actionLabel": "Try this | Angle for you | Worth the drive",
      "action": "one concrete ≤10-minute step",
      "permalink": "https://… (first-party only)",
      "image": "https://…",                       // optional card image
      "watch": { "label": "…", "url": "https://…" },   // optional, SHIPPED demo video
      "eval": [{ "check": "Meaningful", "result": "PASS | FAIL | N/A", "reason": "…" }]
    }
  ],
  "dropped": [{ "title": "…", "stage": "step 3 | eval gate", "reason": "…" }]
}
```

## Public data only

This repository and [token-snack.in](https://token-snack.in) are public. The build fails (and nothing deploys) if a brief is malformed, has keys outside this schema, a URL is not `https://`, or the file contains anything that looks private:

- Email addresses
- Phone numbers
- Private links (`claude.ai`, Google Docs / Drive / Gmail)
- API-key or token shapes (`sk-…`, `ghp_…`, `github_pat_…`, `AKIA…`, `AIza…`, `xox…`, bearer tokens, `api_key=`)

Eval reasons are included in that scan. Keep them to one public line. Never paste feedback notes, inbox contents, or secrets into the JSON. The site byline “by Vikas” lives in the HTML template only — not inside brief fields.

## Build outputs

`python3 scripts/build.py` writes `_site/` (gitignored):

| Path | Purpose |
|------|---------|
| `index.html` | Latest edition |
| `YYYY-MM-DD/index.html` | Permalink for that day |
| `YYYY-MM-DD.md` | Markdown twin of the edition |
| `YYYY-MM-DD-standalone.html` | Same edition with CSS inlined |
| `archive/index.html` | All days |
| `feed.xml` | RSS |
| `CNAME` | Custom domain (`token-snack.in`) |
| `assets/style.css` | Styles |

## Custom domain

GitHub Pages serves the site. The registrar only holds DNS for [token-snack.in](https://token-snack.in).

1. Push to `main` on https://github.com/vikas434/token-snack (Actions builds `_site/` including `CNAME`).
2. In the repo: **Settings → Pages**. Source: GitHub Actions. Custom domain: `token-snack.in`. Enable **Enforce HTTPS** after the certificate appears.
3. At the registrar, set:

| Host | Type | Value |
|------|------|-------|
| `@` | A | `185.199.108.153` |
| `@` | A | `185.199.109.153` |
| `@` | A | `185.199.110.153` |
| `@` | A | `185.199.111.153` |
| `www` | CNAME | `vikas434.github.io` |

4. Wait for DNS, then open [https://token-snack.in](https://token-snack.in).
