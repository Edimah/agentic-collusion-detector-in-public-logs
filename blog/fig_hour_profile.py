"""Blog figure: hour-of-day profiles, humans on DSE 2003-2006 vs agents May-July 2026.

Same data and filters as Figure 8 of the report (src/analysis.py, fig5_hour_profiles.png),
restyled for the blog in the Sage & Plum identity. Writes into the website repo.
Run: python blog/fig_hour_profile.py
"""
import json
import pathlib
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import MultipleLocator, PercentFormatter

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROJECTS = ROOT.parent
sys.path.insert(0, str(PROJECTS / "france-pathologies/scripts"))
from blog_style import SAGE, PLUM, SURFACE, apply_style  # noqa: E402

OUT = PROJECTS / "website/assets/img/agent-swarm/hour-of-day.png"

rc = pd.read_csv(ROOT / "data/processed/rc_dse_edits.csv", parse_dates=["ts"])
agents = pd.read_csv(ROOT / "data/processed/agent_revisions.csv")
h_human = rc[rc.ts < "2007-01-01"].ts.dt.hour.value_counts().reindex(range(24), fill_value=0)
h_agent = agents.hour_utc.value_counts().reindex(range(24), fill_value=0)

# ATTENTION: the blog figure must rest on the same counts as results.json
R = json.loads((ROOT / "results.json").read_text())["hour_profile"]
assert (h_human.sum(), h_agent.sum()) == (R["n_human"], R["n_agent"])
assert (h_human.idxmax(), h_agent.idxmax()) == (R["human_peak_hour"], R["agent_peak_hour_utc"])

apply_style()
fig, ax = plt.subplots(figsize=(7.2, 3.4))
x, w = np.arange(24), 0.4
ax.bar(x - w / 2, h_human / h_human.sum(), w, color=SAGE, edgecolor=SURFACE, linewidth=1,
       label="People editing the wiki, 2003 to 2006")
ax.bar(x + w / 2, h_agent / h_agent.sum(), w, color=PLUM, edgecolor=SURFACE, linewidth=1,
       label="AI agents, May to July 2026")
ax.set_xticks(range(0, 24, 3), [f"{h}h" for h in range(0, 24, 3)])
ax.set_xlim(-0.7, 23.7)
ax.set_xlabel("Time of day")
ax.set_ylabel("Share of the group's edits")
ax.yaxis.set_major_locator(MultipleLocator(0.05))
ax.yaxis.set_major_formatter(PercentFormatter(1, decimals=0))
ax.grid(axis="y")
ax.set_axisbelow(True)
ax.tick_params(axis="x", length=0)
ax.legend(loc="upper left")
fig.tight_layout()
OUT.parent.mkdir(exist_ok=True)
fig.savefig(OUT)
print("saved", OUT)
