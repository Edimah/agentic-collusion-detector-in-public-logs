# Detecting agentic collusion in public logs with statistical methods

Apart Research x CeSIA, AI Incident Response Sprint, 11 to 13 September 2026, Track 2.
Edimah SYNESIUS SONGO.
Report: https://apartresearch.com/sprints/projects/detecting-agentic-collusion-in-public-logs-with-statistical-methods-4rdi

## Question

In May to July 2026 a swarm of OpenAI evaluation agents used a dormant German wiki
(DSE wiki, on the ProWiki farm at wikiservice.at) as a message board. Can that regime
change be detected, dated and characterised from the wiki's public edit log alone?

## Result in three numbers

| What                                                        | Value                              |
| ----------------------------------------------------------- | ---------------------------------- |
| Live edits vs reconstructed agent saves in the window       | 3,912 vs 13,403                    |
| Difference-in-differences against an untouched sibling wiki | 3.22 log points, placebo p = 1/523 |
| Hour-of-day profile, humans vs agents                       | Cramer's V = 0.44                  |

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

or step by step: `fetch_data.py`, `parse_prowiki_rc.py`, `build_tables.py`, `analysis.py`, `check_nb_tail.py`.
Python 3.13, dependencies in `requirements.txt`. About two minutes.

## Files

- `src/fetch_data.py`: downloads the dump and the four RecentChanges pages.
- `src/parse_prowiki_rc.py`: RecentChanges HTML to one CSV per wiki (page, editor, time).
- `src/build_tables.py`: dump JSON Lines to a slim revision table; daily counts per source.
- `src/analysis.py`: every figure and every number of the report, written to `figures/` and `results.json`.
- `src/check_nb_tail.py`: where the negative binomial tail overtakes the Poisson tail (Model 2); adds `nb_tail_check` to `results.json`.
- The report is on the Apart Research project page linked above. Its LaTeX source is not in this repository.

## Authorship and AI use

[Disclosure sentence, to be written by Edimah.]

Claude Code (Anthropic) worked in this repository and in a private working repository before it. "Claude Code" below means the commits carry a Co-Authored-By trailer for Claude. A commit without a trailer is not proof of human-only work.

| File or component | Who wrote it | Evidence (commits) |
| --- | --- | --- |
| Data fetching and parsing (`fetch_data.py`, `parse_prowiki_rc.py`, `build_tables.py`) | Claude Code | 0ba7241 (working repo), 8fb3264 |
| Analysis code (`analysis.py`, `run_all.sh`, `results.json`) | Claude Code | 5f72011, fab2309, 30b7542, 65e3a4c (working repo), 8fb3264, 99adcf0, aabc2ea |
| `check_nb_tail.py` | Claude Code | 99adcf0 |
| Tests | none | - |
| Figures | Claude Code | f4a5993, 5f72011 (working repo), 8fb3264 |
| `blog/fig_hour_profile.py` | no trailer | e77a3e5 |
| Report | mixed: Claude drafts, edited by Edimah | 2a9cf3f, bdae3e2, 174a21e, 9cf615d, 42ffc9d, ac49f8c, e9eef34, 99adcf0 (Claude); 7d86ee8, e77a3e5, eb8aac2 (no trailer) |
| README | mixed | 8fb3264, 174a21e, 99adcf0 (Claude); 8cf80ac, eb8aac2 (no trailer) |

## Limits

No chain of thought is public; intent is read from message text and from the
investigators' page labels. The live log is a survivor's view: the moderator deleted
most agent pages before the log was read. The human hour profile is from 2003 to 2006 in
server local time; the agent profile is 2026 in UTC. One incident on one wiki family.

## Changes since submission (27 Sept 2026)

The submitted version is the git tag `submitted-2026-09-14`. No number in `results.json` changed; the key `nb_tail_check` was added.

1. Abstract: the placebo statement was wrong. The largest placebo (0.37) is 12 percent of the effect (3.22), not under 10. It now reads "against at most 0.37 for any of 522 placebo start dates (p = 1/523)".
2. Model 2: the claim "for x > mu, the negative binomial tail exceeds the Poisson tail" is false in general (mu = k = 1, x = 2: 0.25 against 0.264). It now holds for x >= x*, proved by a single sign change (Shaked, 1980) instead of Jensen's inequality. In the report's setting x* = 2 and the observed count is 3,912, so the conclusion stands. Check: `src/check_nb_tail.py`.
3. Results: the live and reconstructed daily counts have a Spearman correlation of 0.59, not 0.60. The 25-fold change (e^3.22) is on the scale of 1 + weekly edits.

## Changes since submission (5 Oct 2026)

The report was missing the conclusion, it was added back for future reference.
