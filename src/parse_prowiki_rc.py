"""Parse ProWiki RecentChanges HTML (all=1) into one CSV row per edit.

Output columns: wiki, ts (UTC, wiki-server clock), date, time, page, editor,
summary, is_agent_window (2026-05-11 .. 2026-07-02 inclusive).

Run: python src/parse_prowiki_rc.py
"""
import csv
import html
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
RC = ROOT / "data" / "raw" / "prowiki_rc"
OUT = ROOT / "data" / "processed"

MONTHS = {m: i + 1 for i, m in enumerate(
    ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August",
     "September", "Oktober", "November", "Dezember"])}
DAY_DE = re.compile(r"<p><strong>(\d{1,2})\. (\w+) (\d{4})</strong></p>")      # 11. September 2026
DAY_EN = re.compile(r"<p><strong>(\w+) (\d{1,2}), (\d{4})</strong></p>")        # September 5, 2026
MONTHS_EN = {m: i + 1 for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July", "August",
     "September", "October", "November", "December"])}
LI_RE = re.compile(
    r"<li>.*?<a href='wiki\.cgi\?([^']+)' class='body'>(?P<page>[^<]*)</a>\s*"
    r"(?P<time>\d{1,2}:\d{2})\s*(?:\[(?P<summary>[^\]]*)\])?\s*\. \. \. \. \.\s*"
    r"(?:<a href='wiki\.cgi\?[^']*' class='body'>(?P<editor>[^<]*)</a>|(?P<editor2>[^<]+))</li>", re.S)
WINDOW = ("2026-05-11", "2026-07-02")


def parse(path, wiki):
    raw = path.read_bytes().decode("latin-1")
    rows, day = [], None
    for m in re.finditer(r"<p><strong>.*?</strong></p>|<li>.*?</li>", raw, re.S):
        chunk = m.group(0)
        d = DAY_DE.match(chunk)
        if d:
            mon = MONTHS.get(d.group(2), MONTHS["März"])  # umlaut lost in latin-1 decode
            day = f"{d.group(3)}-{mon:02d}-{int(d.group(1)):02d}"
            continue
        d = DAY_EN.match(chunk)
        if d:
            day = f"{d.group(3)}-{MONTHS_EN[d.group(1)]:02d}-{int(d.group(2)):02d}"
            continue
        e = LI_RE.match(chunk)
        if not e or day is None:
            continue
        editor = html.unescape((e.group("editor") or e.group("editor2") or "").strip())
        hh, mm = e.group("time").split(":")
        rows.append({
            "wiki": wiki, "ts": f"{day}T{int(hh):02d}:{mm}:00", "date": day,
            "time": f"{int(hh):02d}:{mm}", "page": html.unescape(e.group("page")),
            "editor": editor, "summary": html.unescape(e.group("summary") or ""),
            "is_agent_window": int(WINDOW[0] <= day <= WINDOW[1]),
        })
    return rows


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for p in sorted(RC.glob("rc_*_10000.html")):
        wiki = p.name.split("_")[1]
        rows = parse(p, wiki)
        if not rows:
            print(wiki, "no rows parsed"); continue
        dest = OUT / f"rc_{wiki}_edits.csv"
        with dest.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        print(wiki, len(rows), "edits", rows[-1]["date"], "->", rows[0]["date"])


if __name__ == "__main__":
    main()
