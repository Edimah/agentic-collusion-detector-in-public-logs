"""Build the analysis tables from the raw sources.

Outputs (data/processed/):
  agent_revisions.csv  one row per agent edit from the collusion.wiki dump, body dropped
                       (keeps wiki, page, label, ip16, time, body_len, body_sha256, page_family)
  daily_counts.csv     one row per (source, wiki, date): n_edits, n_editors, n_pages
                       sources: 'rc' = live RecentChanges (humans + agents + moderator),
                                'dump' = collusion.wiki agent-only reconstruction

Run: python src/build_tables.py
"""
import json
import pathlib

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
CW = ROOT / "data" / "raw" / "collusion_wiki"
PROC = ROOT / "data" / "processed"


def main():
    pages = pd.read_json(CW / "pages.jsonl", lines=True)[["page_id", "page_family", "bucket", "n_deletions"]]
    keep = ["rev_id", "page_id", "wiki", "name", "seq", "label", "ip16", "time", "time_grade",
            "body_len", "body_sha256", "lines", "request_action", "change_summary", "body_encoding"]
    revs = pd.DataFrame([{k: r.get(k) for k in keep}
                         for r in map(json.loads, open(CW / "revisions.jsonl"))])
    revs = revs.merge(pages, on="page_id", how="left")
    revs["time"] = pd.to_datetime(revs["time"], utc=True)
    revs["date"] = revs["time"].dt.strftime("%Y-%m-%d")
    revs["hour_utc"] = revs["time"].dt.hour
    revs.to_csv(PROC / "agent_revisions.csv", index=False)

    daily = []
    g = revs.groupby(["wiki", "date"])
    d = g.agg(n_edits=("rev_id", "size"), n_editors=("label", "nunique"), n_pages=("page_id", "nunique")).reset_index()
    d.insert(0, "source", "dump")
    daily.append(d)
    for p in sorted(PROC.glob("rc_*_edits.csv")):
        rc = pd.read_csv(p)
        d = rc.groupby(["wiki", "date"]).agg(n_edits=("page", "size"), n_editors=("editor", "nunique"),
                                             n_pages=("page", "nunique")).reset_index()
        d.insert(0, "source", "rc")
        daily.append(d)
    out = pd.concat(daily).sort_values(["source", "wiki", "date"])
    out.to_csv(PROC / "daily_counts.csv", index=False)
    print(len(revs), "agent revisions;", len(out), "daily rows")


if __name__ == "__main__":
    main()
