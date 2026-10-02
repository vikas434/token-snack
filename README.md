# Daily Dose of AI

A short, eval-gated daily brief on AI tooling for engineers, published with GitHub Pages.

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
      "summary": "optional",
      "why": "one plain-English sentence",
      "actionLabel": "Try this | Angle for you | Worth the drive",
      "action": "one concrete ≤10-minute step",
      "permalink": "https://… (first-party only)",
      "watch": { "label": "…", "url": "https://…" },   // optional, SHIPPED demo video
      "eval": [{ "check": "Meaningful", "result": "PASS | FAIL | N/A", "reason": "…" }]
    }
  ],
  "dropped": [{ "title": "…", "stage": "step 3 | eval gate", "reason": "…" }]
}
```

The build fails (and nothing deploys) if a brief is malformed, has keys outside this
schema, a URL is not `https://`, or it contains anything that looks private
(e-mail addresses, private Claude/Google links, phone numbers).
