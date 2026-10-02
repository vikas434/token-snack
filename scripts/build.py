#!/usr/bin/env python3
"""Build the Daily Dose of AI static site from data/briefs/*.json.

Usage:  python3 scripts/build.py            # writes the site into _site/
        python3 scripts/build.py --check    # validate data only, write nothing

Each brief is one JSON file named YYYY-MM-DD.json (schema in README.md).
Output:
  _site/index.html                 latest brief
  _site/YYYY-MM-DD/index.html      permalink for every day
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
SITE_TITLE = "Daily Dose of AI"
SITE_URL = os.environ.get("SITE_URL", "").rstrip("/")  # set by the Pages workflow; empty -> relative links

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
ITEM_KEYS = {"slug", "section", "title", "summary", "why", "actionLabel", "action", "permalink", "watch", "eval"}
# Generic privacy guard: no e-mail addresses, private Claude/Google links, or phone numbers.
PRIVATE_RE = re.compile(
    r"[\w.+-]+@[\w-]+\.[\w.]+|claude\.ai/|(docs|drive|mail)\.google\.com|\+?\d[\d ()-]{9,}\d", re.I)


class BriefError(ValueError):
    pass


def esc(s) -> str:
    return html.escape(str(s or ""), quote=True)


def safe_url(u: str, where: str) -> str:
    if not isinstance(u, str) or not u.startswith("https://"):
        raise BriefError(f"{where}: URL must be https:// (got {u!r})")
    return u


def load_brief(path: Path) -> dict:
    try:
        b = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise BriefError(f"{path.name}: invalid JSON ({e})") from e
    d = b.get("date")
    if not (isinstance(d, str) and DATE_RE.match(d)) or path.stem != d:
        raise BriefError(f"{path.name}: 'date' must equal the file name (YYYY-MM-DD)")
    dt.date.fromisoformat(d)
    extra = set(b) - BRIEF_KEYS
    if extra:
        raise BriefError(f"{path.name}: unexpected top-level keys {sorted(extra)}")
    raw = path.read_text(encoding="utf-8")
    hit = PRIVATE_RE.search(raw) if "claude.ai/" in raw else PRIVATE_RE.search(re.sub(r"https://\S+", "", raw))
    if hit:
        raise BriefError(f"{path.name}: looks like private data ({hit.group(0)!r}) — remove it")
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
        if it.get("watch"):
            safe_url(it["watch"].get("url"), where + " watch")
        for e in it.get("eval", []):
            if e.get("result") not in ("PASS", "FAIL", "N/A"):
                raise BriefError(f"{where}: eval result must be PASS/FAIL/N/A")
    return b


def pretty_date(d: str) -> str:
    x = dt.date.fromisoformat(d)
    return x.strftime("%A, %B ") + str(x.day) + x.strftime(", %Y")


def page(title: str, body: str, depth: int, description: str = "") -> str:
    up = "../" * depth
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description or 'A short, eval-gated daily brief on AI tooling for engineers.')}">
<link rel="stylesheet" href="{up}assets/style.css">
<link rel="alternate" type="application/rss+xml" title="{SITE_TITLE}" href="{up}feed.xml">
<script>try{{var t=localStorage.getItem('ddai-theme');if(t)document.documentElement.dataset.theme=t}}catch(e){{}}</script>
</head>
<body>
<header class="top">
  <a class="brand" href="{up}index.html"><span class="dot"></span>{SITE_TITLE}</a>
  <nav><a href="{up}archive/index.html">Archive</a><a href="{up}feed.xml">RSS</a>
  <button class="theme" type="button" aria-label="Toggle dark mode" onclick="var r=document.documentElement,n=(r.dataset.theme||(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'))==='dark'?'light':'dark';r.dataset.theme=n;try{{localStorage.setItem('ddai-theme',n)}}catch(e){{}}">◐</button></nav>
</header>
<main class="wrap">
{body}
</main>
<footer class="foot">Picked, cut and eval-checked daily. Every link is first-party.</footer>
</body>
</html>
"""


def render_item(it: dict) -> str:
    color, default_label = SECTIONS[it["section"]]
    label = it.get("actionLabel") or default_label
    parts = [f'<article class="card" id="{esc(it["slug"])}" style="--accent:{color}">',
             f'<h3>{esc(it["title"])}</h3>']
    if it.get("summary"):
        parts.append(f'<p class="summary">{esc(it["summary"])}</p>')
    parts.append(f'<p class="why"><strong>Why it matters:</strong> {esc(it["why"])}</p>')
    parts.append(f'<p class="action"><strong>{esc(label)}:</strong> {esc(it["action"])}</p>')
    w = it.get("watch")
    if w:
        parts.append(f'<p class="action"><strong>Watch:</strong> <a href="{esc(w["url"])}">{esc(w.get("label") or w["url"])}</a></p>')
    shown = re.sub(r"^https://(www\.)?", "", it["permalink"])
    parts.append(f'<a class="permalink" href="{esc(it["permalink"])}">{esc(shown)}</a>')
    ev = it.get("eval") or []
    if ev:
        passed = sum(1 for e in ev if e.get("result") == "PASS")
        scored = sum(1 for e in ev if e.get("result") != "N/A")
        rows = "".join(
            f'<li><span class="res res-{esc(e.get("result","")).lower().replace("/","")}">{esc(e.get("result"))}</span>'
            f' <b>{esc(e.get("check"))}</b> — {esc(e.get("reason"))}</li>' for e in ev)
        parts.append(f'<details class="eval"><summary>Eval gate: {passed}/{scored} checks passed</summary><ul>{rows}</ul></details>')
    parts.append("</article>")
    return "\n".join(parts)


def render_brief(b: dict, depth: int, prev_d: str | None, next_d: str | None) -> str:
    up = "../" * depth
    out = [f'<p class="kicker">AI Tooling Brief</p><h1>{esc(pretty_date(b["date"]))}</h1>']
    if b.get("notice"):
        out.append(f'<p class="notice">{esc(b["notice"])}</p>')
    items = b["items"]
    if not items:
        out.append('<p class="empty">Nothing cleared today\'s bar — no picks today.</p>')
    for sec in SECTIONS:
        group = [i for i in items if i["section"] == sec]
        if group:
            out.append(f'<section><h2 class="sec">{esc(LABELS[sec])}</h2>')
            out.extend(render_item(i) for i in group)
            out.append("</section>")
    skipped = b.get("skipped") or []
    dropped = b.get("dropped") or []
    if skipped or dropped:
        out.append('<details class="meta"><summary>What didn\'t make it today</summary>')
        if skipped:
            out.append("<h4>Skipped sections</h4><ul>" + "".join(
                f'<li><b>{esc(s.get("section"))}</b> — {esc(s.get("reason"))}</li>' for s in skipped) + "</ul>")
        if dropped:
            out.append("<h4>Cut candidates</h4><ul>" + "".join(
                f'<li><b>{esc(x.get("title"))}</b> <span class="stage">{esc(x.get("stage",""))}</span> — {esc(x.get("reason"))}</li>'
                for x in dropped) + "</ul>")
        out.append("</details>")
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
        chips = "".join(f'<span class="chip" style="--accent:{SECTIONS[s][0]}">{esc(LABELS[s])} {n}</span>'
                        for s, n in counts.items()) or '<span class="chip">no picks</span>'
        tops = "".join(f"<li>{esc(i['title'])}</li>" for i in b["items"][:3])
        rows.append(f'<li class="day"><a href="../{b["date"]}/index.html"><span class="d">{esc(pretty_date(b["date"]))}</span>'
                    f'<span class="chips">{chips}</span></a><ul class="tops">{tops}</ul></li>')
    return '<p class="kicker">Archive</p><h1>Every brief</h1><ul class="days">' + "".join(rows) + "</ul>"


def render_feed(briefs: list[dict]) -> str:
    entries = []
    for b in briefs[:30]:
        d = dt.date.fromisoformat(b["date"])
        pub = dt.datetime(d.year, d.month, d.day, 6, 0, tzinfo=dt.timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
        desc = "".join(f"<p><b>{esc(i['section'])}</b> — <a href=\"{esc(i['permalink'])}\">{esc(i['title'])}</a><br>{esc(i['why'])}</p>"
                       for i in b["items"]) or "<p>No picks today.</p>"
        entries.append(f"<item><title>{esc(SITE_TITLE)} — {esc(pretty_date(b['date']))}</title>"
                       f"<link>{SITE_URL}/{b['date']}/</link><guid isPermaLink=\"false\">{b['date']}</guid>"
                       f"<pubDate>{pub}</pubDate><description>{esc(desc)}</description></item>")
    return ('<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel>'
            f"<title>{SITE_TITLE}</title><link>{SITE_URL or '.'}/</link>"
            "<description>A short, eval-gated daily brief on AI tooling for engineers.</description>"
            + "".join(entries) + "</channel></rss>\n")


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

    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "assets").mkdir(parents=True)
    shutil.copy(ROOT / "assets" / "style.css", OUT / "assets" / "style.css")
    (OUT / ".nojekyll").write_text("")

    dates = [b["date"] for b in briefs]
    for idx, b in enumerate(briefs):
        prev_d = dates[idx + 1] if idx + 1 < len(dates) else None
        next_d = dates[idx - 1] if idx > 0 else None
        desc = "; ".join(i["title"] for i in b["items"][:3])
        day_dir = OUT / b["date"]
        day_dir.mkdir()
        (day_dir / "index.html").write_text(
            page(f"{SITE_TITLE} — {pretty_date(b['date'])}", render_brief(b, 1, prev_d, next_d), 1, desc), encoding="utf-8")
        if idx == 0:
            (OUT / "index.html").write_text(
                page(f"{SITE_TITLE} — {pretty_date(b['date'])}", render_brief(b, 0, prev_d, None), 0, desc), encoding="utf-8")
    (OUT / "archive").mkdir()
    (OUT / "archive" / "index.html").write_text(page(f"{SITE_TITLE} — Archive", render_archive(briefs), 1), encoding="utf-8")
    (OUT / "feed.xml").write_text(render_feed(briefs), encoding="utf-8")
    print(f"Built {OUT.relative_to(ROOT)}/")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
