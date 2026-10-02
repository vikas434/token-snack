# Token Snack by Vikas

A short, eval-gated daily brief on AI tooling for engineers.

**Live site:** https://token-snack.in  
**Repo:** https://github.com/vikas434/token-snack

Every day an automated job gathers candidates from public sources, cuts hard,
runs a 5-check eval gate on each survivor, then commits one JSON file here —
the repo holds only public brief content and the code that renders it. GitHub Actions validates it, builds the static site and deploys it to Pages.

```
data/briefs/YYYY-MM-DD.json   ← the only thing the routine writes each day
scripts/build.py              ← validates every brief + renders _site/ (no dependencies)
assets/style.css
.github/workflows/pages.yml   ← build + deploy on every push to main
```

Local preview: `python3 scripts/build.py && python3 -m http.server -d _site 8000`  
Validate only: `python3 scripts/build.py --check`

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

This repository and https://token-snack.in are public. The build fails (and nothing deploys) if a brief is malformed, has keys outside this schema, a URL is not `https://`, or the file contains anything that looks private:

- Email addresses
- Phone numbers
- Private links (`claude.ai`, Google Docs / Drive / Gmail)
- API-key or token shapes (`sk-…`, `ghp_…`, `github_pat_…`, `AKIA…`, `AIza…`, `xox…`, bearer tokens, `api_key=`)

Eval reasons are included in that scan. Keep them to one public line. Never paste feedback notes, inbox contents, or secrets into the JSON. The site byline "by Vikas" lives in the HTML template only — not inside brief fields.

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

## Custom domain (token-snack.in)

GitHub Pages serves the site. The registrar only holds DNS.

1. Push this repo to `main` on https://github.com/vikas434/token-snack (GitHub Actions builds `_site/` including `CNAME`).
2. In the repo: **Settings → Pages**. Source: GitHub Actions. Custom domain: `token-snack.in`. Enable **Enforce HTTPS** after the certificate appears.
3. At the registrar for `token-snack.in`, set:

| Host | Type | Value |
|------|------|-------|
| `@` | A | `185.199.108.153` |
| `@` | A | `185.199.109.153` |
| `@` | A | `185.199.110.153` |
| `@` | A | `185.199.111.153` |
| `www` | CNAME | `vikas434.github.io` |

4. Wait for DNS, then open https://token-snack.in.
