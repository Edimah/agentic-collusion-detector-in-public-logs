#!/bin/sh
# Rebuild everything from the two public sources. Takes about two minutes.
set -e
cd "$(dirname "$0")"
python src/fetch_data.py         # data/raw/ (git-ignored): collusion.wiki dump + four RecentChanges pages
python src/parse_prowiki_rc.py   # data/processed/rc_<wiki>_edits.csv
python src/build_tables.py       # data/processed/agent_revisions.csv, daily_counts.csv
python src/analysis.py           # figures/*.png and results.json
python src/check_nb_tail.py      # adds nb_tail_check to results.json (Model 2 tail crossing)
