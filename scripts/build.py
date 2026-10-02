#!/usr/bin/env python3
"""Build the Token Snack by Vikas static site from data/briefs/*.json.

Usage:  python3 scripts/build.py            # writes the site into _site/
        python3 scripts/build.py --check    # validate data only, write nothing

Each brief is one JSON file named YYYY-MM-DD.json (schema in README.md).
Output:
  _site/index.html                 latest brief
  _site/YYYY-MM-DD/index.html      permalink for every day
  _site/YYYY-MM-DD.md              markdown twin
  _site/YYYY-MM-DD-standalone.html inlined CSS edition
  _site/archive/index.html         list of all days
  _site/feed.xml                   RSS feed
  _site/assets/style.css
No third-party dependencies.
"""
from __future__ import annotations

import datetime as dt
import html
import json
import os
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "briefs"
OUT = ROOT / "_site"
SITE_TITLE = "Token Snack"
SITE_BYLINE = "by Vikas"
SITE_NAME = f"{SITE_TITLE} {SITE_BYLINE}"
# Name meaning: a small daily bite of AI tooling — so you spend tokens on what matters.
SITE_TAGLINE = "A daily snack for token optimization"
SITE_DESCRIPTION = (
    "Token Snack by Vikas — a daily snack for token optimization. "
    "Short, eval-gated AI tooling picks for engineers who want signal, not slop."
)
# Prefer SITE_URL from the environment; otherwise the live Vercel URL.
SITE_URL = (os.environ.get("SITE_URL") or "https://token-snack.vercel.app").rstrip("/")
DEFAULT_OG_IMAGE = f"{SITE_URL}/assets/og-banner.jpg"


def logo_mark(mask_id: str = "bite") -> str:
    """Three-tile snack mark from the Token Snack brand banner."""
    return (
        f'<svg class="logo-mark" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 48" '
        f'width="72" height="29" role="img" aria-hidden="true">'
        f'<rect x="2" y="8" width="28" height="28" rx="7" fill="#1D9E75"/>'
        f'<rect x="38" y="8" width="28" height="28" rx="7" fill="#7F77DD"/>'
        f'<defs><mask id="{mask_id}">'
        f'<rect x="74" y="8" width="28" height="28" rx="7" fill="white"/>'
        f'<circle cx="102" cy="12" r="7" fill="black"/>'
        f'<circle cx="104" cy="22" r="4.5" fill="black"/>'
        f"</mask></defs>"
        f'<rect x="74" y="8" width="28" height="28" rx="7" fill="#C77D2E" mask="url(#{mask_id})"/>'
        f'<circle cx="104" cy="40" r="2.2" fill="#C77D2E"/>'
        f'<circle cx="110" cy="38" r="1.6" fill="#C77D2E"/>'
        f'<circle cx="107" cy="44" r="1.3" fill="#C77D2E"/>'
        f"</svg>"
    )

SECTIONS = {  # order on the page, accent colour, card action label
    "SHIPPED": ("#1D9E75", "Try this"),
    "ON LINKEDIN": ("#D4537E", "Angle for you"),
    "TRENDING ON X": ("#378ADD", "Angle for you"),
    "STUDY": ("#7F77DD", "Try this"),
    "WATCH QUEUE": ("#C77D2E", "Worth the drive"),
}
LABELS = {"SHIPPED": "Shipped", "ON LINKEDIN": "On LinkedIn", "TRENDING ON X": "Trending on X",
          "STUDY": "Study", "WATCH QUEUE": "Watch Queue"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
REQUIRED_ITEM = ("slug", "section", "title", "why", "action", "permalink")
# Only these keys may appear, so nothing else can leak into the public site.
BRIEF_KEYS = {"date", "notice", "skipped", "items", "dropped"}
ITEM_KEYS = {"slug", "section", "title", "summary", "why", "actionLabel", "action",
             "permalink", "watch", "eval", "image"}
# Public-site guard: emails, private links, phones, and common API-key shapes.
# Scanned against the whole file (including https:// URLs) so secrets in query strings fail.
PRIVATE_RE = re.compile(
    r"(?:"
    r"[\w.+-]+@[\w-]+\.[\w.]+"
    r"|claude\.ai/"
    r"|(?:docs|drive|mail)\.google\.com"
    # Phone-like: leading +country, or digits with separators (not bare LinkedIn/GitHub ids).
    r"|\+\d{1,3}[\d\s().-]{6,}\d"
    r"|\b\d{3}[-.\s()]\d{2,4}[-.\s()]\d{2,4}\b"
    r"|\bsk-[A-Za-z0-9_-]{10,}"
    r"|\bghp_[A-Za-z0-9]{20,}"
    r"|\bgithub_pat_[A-Za-z0-9_]{20,}"
    r"|\bAKIA[0-9A-Z]{16}"
    r"|\bAIza[0-9A-Za-z_-]{20,}"
    r"|\bxox[baprs]-[A-Za-z0-9-]{10,}"
    r"|\bbearer\s+[A-Za-z0-9._\-]{20,}"
    r"|api[_-]?key\s*[=:]\s*\S+"
    r")",
    re.I,
)


class BriefError(ValueError):
    pass


def esc(s) -> str:
    return html.escape(str(s or ""), quote=True)


def safe_url(u: str, where: str) -> str:
    if not isinstance(u, str) or not u.startswith("https://"):
        raise BriefError(f"{where}: URL must be https:// (got {u!r})")
    return u


def scan_private(raw: str, where: str) -> None:
    hit = PRIVATE_RE.search(raw)
    if hit:
        raise BriefError(f"{where}: looks like private data or a secret ({hit.group(0)!r}) — remove it")


def load_brief(path: Path) -> dict:
    try:
        raw = path.read_text(encoding="utf-8")
        b = json.loads(raw)
    except json.JSONDecodeError as e:
        raise BriefError(f"{path.name}: invalid JSON ({e})") from e
    d = b.get("date")
    if not (isinstance(d, str) and DATE_RE.match(d)) or path.stem != d:
        raise BriefError(f"{path.name}: 'date' must equal the file name (YYYY-MM-DD)")
    dt.date.fromisoformat(d)
    extra = set(b) - BRIEF_KEYS
    if extra:
        raise BriefError(f"{path.name}: unexpected top-level keys {sorted(extra)}")
    scan_private(raw, path.name)
    items = b.get("items")
    if not isinstance(items, list):
        raise BriefError(f"{path.name}: 'items' must be a list (empty is fine)")
    seen = set()
    for i, it in enumerate(items):
        where = f"{path.name} item {i}"
        if set(it) - ITEM_KEYS:
            raise BriefError(f"{where}: unexpected keys {sorted(set(it) - ITEM_KEYS)}")
        for k in REQUIRED_ITEM:
            if not it.get(k):
                raise BriefError(f"{where}: missing '{k}'")
        if it["section"] not in SECTIONS:
            raise BriefError(f"{where}: unknown section {it['section']!r}")
        if not SLUG_RE.match(it["slug"]) or it["slug"] in seen:
            raise BriefError(f"{where}: slug must be unique lowercase-kebab")
        seen.add(it["slug"])
        safe_url(it["permalink"], where)
        if it.get("image"):
            safe_url(it["image"], where + " image")
        if it.get("watch"):
            safe_url(it["watch"].get("url"), where + " watch")
        for e in it.get("eval", []):
            if e.get("result") not in ("PASS", "FAIL", "N/A"):
                raise BriefError(f"{where}: eval result must be PASS/FAIL/N/A")
    return b


def pretty_date(d: str) -> str:
    x = dt.date.fromisoformat(d)
    return x.strftime("%A, %B ") + str(x.day) + x.strftime(", %Y")


def pick_count_label(n: int) -> str:
    return f"{n} pick" if n == 1 else f"{n} picks"


def page(
    title: str,
    body: str,
    depth: int,
    description: str = "",
    *,
    canonical: str = "",
    og_image: str = "",
    inline_css: str = "",
) -> str:
    up = "../" * depth
    desc = description or SITE_DESCRIPTION
    style = (
        f"<style>\n{inline_css}\n</style>"
        if inline_css
        else f'<link rel="stylesheet" href="{up}assets/style.css">'
    )
    canon = f'<link rel="canonical" href="{esc(canonical)}">\n' if canonical else ""
    og = [
        f'<meta property="og:title" content="{esc(title)}">',
        f'<meta property="og:description" content="{esc(desc)}">',
        f'<meta property="og:type" content="article">',
        f'<meta name="twitter:card" content="summary">',
    ]
    if canonical:
        og.append(f'<meta property="og:url" content="{esc(canonical)}">')
    social = og_image or DEFAULT_OG_IMAGE
    og.append(f'<meta property="og:image" content="{esc(social)}">')
    og.append(f'<meta name="twitter:image" content="{esc(social)}">')
    og_block = "\n".join(og)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
{canon}{og_block}
<link rel="icon" href="{up}assets/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="{up}assets/favicon.svg">
<link rel="mask-icon" href="{up}assets/favicon.svg" color="#1D9E75">
{style}
<link rel="alternate" type="application/rss+xml" title="{esc(SITE_NAME)}" href="{up}feed.xml">
<script>try{{var t=localStorage.getItem('ddai-theme');if(t)document.documentElement.dataset.theme=t}}catch(e){{}}</script>
</head>
<body>
<header class="top">
  <div class="brand-block">
    <a class="brand" href="{up}index.html">{logo_mark("bite-h")}<span class="brand-text">{esc(SITE_TITLE)} <span class="byline">{esc(SITE_BYLINE)}</span></span></a>
    <p class="tagline">{esc(SITE_TAGLINE)}</p>
  </div>
  <nav><a href="{up}archive/index.html">Archive</a><a href="{up}feed.xml">RSS</a>
  <button class="theme" type="button" aria-label="Toggle dark mode" onclick="var r=document.documentElement,n=(r.dataset.theme||(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'))==='dark'?'light':'dark';r.dataset.theme=n;try{{localStorage.setItem('ddai-theme',n)}}catch(e){{}}">◐</button></nav>
</header>
<main class="wrap">
{body}
</main>
<footer class="foot"><span class="foot-brand">{logo_mark("bite-f")}</span> {esc(SITE_NAME)} — {esc(SITE_TAGLINE)}. Picked, cut and eval-checked daily. Every link is first-party.</footer>
</body>
</html>
"""


def render_item(it: dict, *, lead: bool = False) -> str:
    color, default_label = SECTIONS[it["section"]]
    label = it.get("actionLabel") or default_label
    cls = "card lead" if lead else "card"
    parts = [f'<article class="{cls}" id="{esc(it["slug"])}" style="--accent:{color}">']
    if it.get("image"):
        parts.append(f'<img class="card-image" src="{esc(it["image"])}" alt="" loading="lazy">')
    parts.append(f'<h3>{esc(it["title"])}</h3>')
    if it.get("summary"):
        parts.append(f'<p class="summary">{esc(it["summary"])}</p>')
    parts.append(f'<p class="why"><strong>Why it matters:</strong> {esc(it["why"])}</p>')
    parts.append(f'<p class="action"><strong>{esc(label)}:</strong> {esc(it["action"])}</p>')
    w = it.get("watch")
    if w:
        parts.append(
            f'<p class="action"><strong>Watch:</strong> '
            f'<a href="{esc(w["url"])}">{esc(w.get("label") or w["url"])}</a></p>'
        )
    shown = re.sub(r"^https://(www\.)?", "", it["permalink"])
    parts.append(f'<a class="permalink" href="{esc(it["permalink"])}">{esc(shown)}</a>')
    ev = it.get("eval") or []
    if ev:
        passed = sum(1 for e in ev if e.get("result") == "PASS")
        scored = sum(1 for e in ev if e.get("result") != "N/A")
        rows = "".join(
            f'<li><span class="res res-{esc(e.get("result", "")).lower().replace("/", "")}">'
            f'{esc(e.get("result"))}</span>'
            f' <b>{esc(e.get("check"))}</b> — {esc(e.get("reason"))}</li>'
            for e in ev
        )
        parts.append(
            f'<details class="eval"><summary>Eval gate: {passed}/{scored} checks passed</summary>'
            f"<ul>{rows}</ul></details>"
        )
    parts.append("</article>")
    return "\n".join(parts)


def lead_slug(items: list[dict]) -> str | None:
    for it in items:
        if it["section"] == "SHIPPED":
            return it["slug"]
    return items[0]["slug"] if items else None


def render_brief(
    b: dict,
    depth: int,
    prev_d: str | None,
    next_d: str | None,
    *,
    edition: int,
    total_editions: int,
    show_hero: bool = False,
) -> str:
    up = "../" * depth
    n = len(b["items"])
    out: list[str] = []
    if show_hero:
        out.append(
            f'<figure class="hero">'
            f'<img src="{up}assets/hero-banner.png" width="1024" height="537" '
            f'alt="{esc(SITE_NAME)} — The daily AI tooling brief. '
            f'Picked by an agent. Checked like an editor.">'
            f"</figure>"
        )
    out.extend(
        [
            '<header class="masthead">',
            f'<h1>{esc(pretty_date(b["date"]))}</h1>',
            f'<p class="edition-meta">Edition {edition} of {total_editions} · {esc(pick_count_label(n))}</p>',
            '<hr class="masthead-rule">',
            "</header>",
        ]
    )
    if b.get("notice"):
        out.append(f'<p class="notice">{esc(b["notice"])}</p>')
    items = b["items"]
    if not items:
        out.append('<p class="empty">Nothing cleared today\'s bar — no picks today.</p>')
    lead = lead_slug(items)
    for sec in SECTIONS:
        group = [i for i in items if i["section"] == sec]
        if group:
            out.append(f'<section><h2 class="sec">{esc(LABELS[sec])}</h2>')
            out.extend(render_item(i, lead=(i["slug"] == lead)) for i in group)
            out.append("</section>")
    skipped = b.get("skipped") or []
    dropped = b.get("dropped") or []
    if skipped or dropped:
        out.append('<details class="meta"><summary>What didn\'t make it today</summary>')
        if skipped:
            out.append(
                "<h4>Skipped sections</h4><ul>"
                + "".join(
                    f'<li><b>{esc(s.get("section"))}</b> — {esc(s.get("reason"))}</li>'
                    for s in skipped
                )
                + "</ul>"
            )
        if dropped:
            out.append(
                "<h4>Cut candidates</h4><ul>"
                + "".join(
                    f'<li><b>{esc(x.get("title"))}</b> <span class="stage">{esc(x.get("stage", ""))}</span>'
                    f' — {esc(x.get("reason"))}</li>'
                    for x in dropped
                )
                + "</ul>"
            )
        out.append("</details>")
    out.append(f'<p class="end-line">End of brief — {esc(pretty_date(b["date"]))}</p>')
    nav = []
    if prev_d:
        nav.append(f'<a href="{up}{prev_d}/index.html">← {esc(prev_d)}</a>')
    nav.append(f'<a href="{up}archive/index.html">All days</a>')
    if next_d:
        nav.append(f'<a href="{up}{next_d}/index.html">{esc(next_d)} →</a>')
    out.append('<nav class="pager">' + "".join(nav) + "</nav>")
    return "\n".join(out)


def render_archive(briefs: list[dict]) -> str:
    rows = []
    for b in briefs:  # newest first
        counts = {}
        for i in b["items"]:
            counts[i["section"]] = counts.get(i["section"], 0) + 1
        chips = "".join(
            f'<span class="chip" style="--accent:{SECTIONS[s][0]}">{esc(LABELS[s])} {n}</span>'
            for s, n in counts.items()
        ) or '<span class="chip">no picks</span>'
        tops = "".join(f"<li>{esc(i['title'])}</li>" for i in b["items"][:3])
        rows.append(
            f'<li class="day"><a href="../{b["date"]}/index.html">'
            f'<span class="d">{esc(pretty_date(b["date"]))}</span>'
            f'<span class="chips">{chips}</span></a><ul class="tops">{tops}</ul></li>'
        )
    return (
        f'<h1>Every brief</h1>'
        f'<ul class="days">{"".join(rows)}</ul>'
    )


def render_feed(briefs: list[dict]) -> str:
    entries = []
    for b in briefs[:30]:
        d = dt.date.fromisoformat(b["date"])
        pub = dt.datetime(d.year, d.month, d.day, 6, 0, tzinfo=dt.timezone.utc).strftime(
            "%a, %d %b %Y %H:%M:%S +0000"
        )
        desc = "".join(
            f"<p><b>{esc(i['section'])}</b> — "
            f"<a href=\"{esc(i['permalink'])}\">{esc(i['title'])}</a><br>{esc(i['why'])}</p>"
            for i in b["items"]
        ) or "<p>No picks today.</p>"
        entries.append(
            f"<item><title>{esc(SITE_NAME)} — {esc(pretty_date(b['date']))}</title>"
            f"<link>{SITE_URL}/{b['date']}/</link><guid isPermaLink=\"false\">{b['date']}</guid>"
            f"<pubDate>{pub}</pubDate><description>{esc(desc)}</description></item>"
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel>'
        f"<title>{esc(SITE_NAME)}</title><link>{SITE_URL}/</link>"
        f"<description>{esc(SITE_DESCRIPTION)}</description>"
        + "".join(entries)
        + "</channel></rss>\n"
    )


def render_markdown(b: dict, *, edition: int, total_editions: int) -> str:
    lines = [
        f"# {SITE_NAME}",
        "",
        f"*{SITE_TAGLINE}*",
        "",
        f"**{pretty_date(b['date'])}** · Edition {edition} of {total_editions} · "
        f"{pick_count_label(len(b['items']))}",
        "",
    ]
    if b.get("notice"):
        lines.extend([f"> {b['notice']}", ""])
    if not b["items"]:
        lines.extend(["Nothing cleared today's bar — no picks today.", ""])
    for sec in SECTIONS:
        group = [i for i in b["items"] if i["section"] == sec]
        if not group:
            continue
        lines.extend([f"## {LABELS[sec]}", ""])
        for it in group:
            label = it.get("actionLabel") or SECTIONS[it["section"]][1]
            lines.append(f"### {it['title']}")
            lines.append("")
            if it.get("summary"):
                lines.extend([it["summary"], ""])
            lines.extend([f"**Why it matters:** {it['why']}", ""])
            lines.extend([f"**{label}:** {it['action']}", ""])
            if it.get("watch"):
                w = it["watch"]
                lines.append(f"**Watch:** [{w.get('label') or w['url']}]({w['url']})")
                lines.append("")
            if it.get("image"):
                lines.append(f"![ ]({it['image']})")
                lines.append("")
            lines.extend([f"[{it['permalink']}]({it['permalink']})", ""])
    lines.extend([f"— End of brief — {pretty_date(b['date'])}", ""])
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    files = sorted(DATA.glob("*.json"))
    errors, briefs = [], []
    for f in files:
        try:
            briefs.append(load_brief(f))
        except BriefError as e:
            errors.append(str(e))
    if errors:
        print("Brief validation failed:\n  " + "\n  ".join(errors), file=sys.stderr)
        return 1
    if not briefs:
        print("No briefs in data/briefs/", file=sys.stderr)
        return 1
    briefs.sort(key=lambda b: b["date"], reverse=True)
    print(f"OK: {len(briefs)} brief(s), latest {briefs[0]['date']}")
    if "--check" in argv:
        return 0

    css = (ROOT / "assets" / "style.css").read_text(encoding="utf-8")
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "assets").mkdir(parents=True)
    (OUT / "assets" / "style.css").write_text(css, encoding="utf-8")
    for name in ("logo.svg", "favicon.svg", "og-banner.jpg", "hero-banner.png"):
        src = ROOT / "assets" / name
        if src.exists():
            shutil.copy(src, OUT / "assets" / name)
    (OUT / ".nojekyll").write_text("")

    chronological = sorted(b["date"] for b in briefs)
    total = len(chronological)
    edition_of = {d: i + 1 for i, d in enumerate(chronological)}

    dates = [b["date"] for b in briefs]
    for idx, b in enumerate(briefs):
        prev_d = dates[idx + 1] if idx + 1 < len(dates) else None
        next_d = dates[idx - 1] if idx > 0 else None
        edition = edition_of[b["date"]]
        desc = "; ".join(i["title"] for i in b["items"][:3]) or SITE_DESCRIPTION
        og_image = next((i["image"] for i in b["items"] if i.get("image")), "")
        canonical = f"{SITE_URL}/{b['date']}/"
        day_dir = OUT / b["date"]
        day_dir.mkdir()
        (day_dir / "index.html").write_text(
            page(
                f"{SITE_NAME} — {pretty_date(b['date'])}",
                render_brief(b, 1, prev_d, next_d, edition=edition, total_editions=total),
                1,
                desc,
                canonical=canonical,
                og_image=og_image,
            ),
            encoding="utf-8",
        )
        (OUT / f"{b['date']}.md").write_text(
            render_markdown(b, edition=edition, total_editions=total),
            encoding="utf-8",
        )
        (OUT / f"{b['date']}-standalone.html").write_text(
            page(
                f"{SITE_NAME} — {pretty_date(b['date'])}",
                render_brief(b, 0, None, None, edition=edition, total_editions=total),
                0,
                desc,
                canonical=canonical,
                og_image=og_image,
                inline_css=css,
            ),
            encoding="utf-8",
        )
        if idx == 0:
            (OUT / "index.html").write_text(
                page(
                    f"{SITE_NAME} — {pretty_date(b['date'])}",
                    render_brief(
                        b,
                        0,
                        prev_d,
                        None,
                        edition=edition,
                        total_editions=total,
                        show_hero=True,
                    ),
                    0,
                    desc,
                    canonical=f"{SITE_URL}/",
                    og_image=og_image or DEFAULT_OG_IMAGE,
                ),
                encoding="utf-8",
            )
    (OUT / "archive").mkdir()
    (OUT / "archive" / "index.html").write_text(
        page(
            f"{SITE_NAME} — Archive",
            render_archive(briefs),
            1,
            f"Archive of {SITE_NAME}",
            canonical=f"{SITE_URL}/archive/",
        ),
        encoding="utf-8",
    )
    (OUT / "feed.xml").write_text(render_feed(briefs), encoding="utf-8")
    print(f"Built {OUT.relative_to(ROOT)}/")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
