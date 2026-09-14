# Detecting agentic collusion in public logs with statistical methods

Apart Research x CeSIA, AI Incident Response Sprint, 11 to 13 September 2026, Track 2.
Edimah SYNESIUS SONGO.

## Question

In May to July 2026 a swarm of OpenAI evaluation agents used a dormant German wiki
(DSE wiki, on the ProWiki farm at wikiservice.at) as a message board. Can that regime
change be detected, dated and characterised from the wiki's public edit log alone?

## Result in three numbers

| What | Value |
|---|---|
| Live edits vs reconstructed agent saves in the window | 3,912 vs 13,403 |
| Difference-in-differences against an untouched sibling wiki | 3.22 log points, placebo p = 1/523 |
| Hour-of-day profile, humans vs agents | Cramer's V = 0.44 |

A weekly check calibrated on 4,872 pre-incident weeks flags the three largest incident
weeks and none of the 2,236 wiki-weeks of 2016 to 2025. The full list of numbers is in
`results.json`.

## Data

Both sources are public and fetched by `src/fetch_data.py`.

1. collusion.wiki export (Nightingale Collective, build of 3 September 2026):
   14,591 agent revisions, 24 May to 2 July 2026, four wikis, agent-only, personal data
   redacted. No licence text on the download page.
2. ProWiki RecentChanges, 10,000-day view, one line per edit, for dse, probier, fractal
   and wiki4d. This is the human baseline. The site logs visitor IP addresses.

Raw files are not redistributed here. `data/processed/` holds the parsed tables so the
figures can be rebuilt without the fetch step (except Figure 7, which needs the message
text from the raw dump).

## Run

```
sh run_all.sh
```

or step by step: `fetch_data.py`, `parse_prowiki_rc.py`, `build_tables.py`, `analysis.py`.
Python 3.13, dependencies in `requirements.txt`. About two minutes.

## Files

- `src/fetch_data.py`: downloads the dump and the four RecentChanges pages.
- `src/parse_prowiki_rc.py`: RecentChanges HTML to one CSV per wiki (page, editor, time).
- `src/build_tables.py`: dump JSON Lines to a slim revision table; daily counts per source.
- `src/analysis.py`: every figure and every number of the report, written to `figures/` and `results.json`.
- `report/main_final.tex`, `report/references.bib`: the submission.

## Limits

No chain of thought is public; intent is read from message text and from the
investigators' page labels. The live log is a survivor's view: the moderator deleted
most agent pages before the log was read. The human hour profile is from 2003 to 2006 in
server local time; the agent profile is 2026 in UTC. One incident on one wiki family.
