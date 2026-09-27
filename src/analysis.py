"""All results and figures of the report, from data/processed/ (plus revisions.jsonl for the intent lexicon).

Writes figures/fig1_*.png ... fig8_*.png and results.json. Every number quoted in the report is a key of results.json.
Run: python src/analysis.py
"""
import json
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROC, RAW, FIG = ROOT / "data/processed", ROOT / "data/raw/collusion_wiki", ROOT / "figures"
FIG.mkdir(exist_ok=True)

SAGE, PLUM, OCHRE, INK, GREY, BG = "#2F8A55", "#93498B", "#B07A2E", "#3A3A3A", "#7A756E", "#FCFCFB"
plt.rcParams.update({"figure.dpi": 150, "savefig.dpi": 200, "figure.facecolor": BG, "axes.facecolor": BG,
                     "axes.edgecolor": INK, "axes.spines.top": False, "axes.spines.right": False,
                     "text.color": INK, "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK, "font.size": 9})

WINDOW = (pd.Timestamp("2026-05-11"), pd.Timestamp("2026-07-02"))   # first probe .. last dump edit
FIRST_WRITE = pd.Timestamp("2026-05-24")
WIKIS = ["dse", "probier", "fractal", "wiki4d"]
R = {}                                                              # results.json


def save(fig, name):
    fig.tight_layout()
    fig.savefig(FIG / f"{name}.png")
    plt.close(fig)
    print("saved", name)


# ---------------------------------------------------------------- data
rc = {w: pd.read_csv(PROC / f"rc_{w}_edits.csv", parse_dates=["ts"]) for w in WIKIS}
agents = pd.read_csv(PROC / "agent_revisions.csv", parse_dates=["time"])
agents["time"] = agents.time.dt.tz_convert(None)                    # UTC, made naive to align with the live index
events = pd.read_json(RAW / "events.jsonl", lines=True, convert_dates=False, keep_default_dates=False) if (RAW / "events.jsonl").exists() else None

IDX = pd.date_range("2003-01-01", "2026-09-11", freq="D")
D = {w: rc[w].set_index("ts").resample("D").size().reindex(IDX, fill_value=0) for w in WIKIS}
D["dump"] = agents.set_index("time").resample("D").size().reindex(IDX, fill_value=0)
W = {k: v.resample("W-MON").sum() for k, v in D.items()}           # weeks labelled by their closing Monday

R["edits_total"] = {w: int(len(rc[w])) for w in WIKIS}
R["dump_revisions"] = {"total": int(len(agents)), **{k: int(v) for k, v in agents.wiki.value_counts().items()}}
R["dump_period"] = [str(agents.time.min().date()), str(agents.time.max().date())]
R["dse_pre_decade_edits"] = int(D["dse"]["2016-05-11":"2026-05-10"].sum())
R["dse_window_live_edits"] = int(D["dse"][WINDOW[0]:WINDOW[1]].sum())
R["dse_peak_day_live"] = [str(D["dse"]["2026"].idxmax().date()), int(D["dse"]["2026"].max())]
R["dse_peak_day_dump"] = [str(D["dump"].idxmax().date()), int(D["dump"].max())]

# ---------------------------------------------------------------- Figure 1: 23 years of daily edits
fig, ax = plt.subplots(figsize=(7.2, 2.6))
ax.plot(D["dse"].index, D["dse"].values + 1, color=SAGE, lw=0.6, label="DSE wiki, live RecentChanges")
ax.plot(D["dump"].index, D["dump"].values + 1, color=PLUM, lw=0.8, label="collusion.wiki dump (agents only)")
ax.axvspan(*WINDOW, color=OCHRE, alpha=0.3, label="incident window, 11 May to 2 Jul 2026")
ax.set_yscale("log"); ax.set_ylabel("edits per day + 1")
ax.xaxis.set_major_locator(mdates.YearLocator(2)); ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax.legend(frameon=False, loc="upper center", ncol=3, fontsize=7.5, bbox_to_anchor=(0.5, 1.12))
save(fig, "fig1_dse_daily_history")

# ---------------------------------------------------------------- Table 1: reconciling the counts
w = rc["dse"][(rc["dse"].ts >= WINDOW[0]) & (rc["dse"].ts < WINDOW[1] + pd.Timedelta(days=1))]
R["reconcile"] = {"live_window_edits": int(len(w)), "live_by_moderator": int(w.editor.eq("MarkusLude").sum()),
                  "live_by_others": int((~w.editor.eq("MarkusLude")).sum()),
                  "dump_saves_dse": int((agents.wiki == "dse").sum())}
if events is not None:
    R["reconcile"].update({f"events_{k}": int(v) for k, v in events.event_type.value_counts().items()})
    R["reconcile"]["events_rows"] = int(len(events))
post = rc["dse"][rc["dse"].ts > WINDOW[1]]
R["moderator_edits_after_window"] = int(post.editor.eq("MarkusLude").sum())

# ---------------------------------------------------------------- naive Poisson and dispersion
pre = D["dse"]["2016-05-11":"2026-05-10"]
lam0 = pre.mean() * (WINDOW[1] - WINDOW[0]).days
k_obs = R["dse_window_live_edits"]
R["poisson"] = {"rate_per_day": float(pre.mean()), "expected_in_window": float(lam0), "observed": k_obs,
                "p_value": float(stats.poisson.sf(k_obs - 1, lam0)),
                "dispersion_pre_decade_daily": float(pre.var(ddof=1) / pre.mean()),
                "dispersion_2003_daily": float(D["dse"]["2003"].var(ddof=1) / D["dse"]["2003"].mean()),
                "dispersion_2003_weekly": float(W["dse"]["2003"].var(ddof=1) / W["dse"]["2003"].mean())}

# ---------------------------------------------------------------- Figure 2: noise floor
ref_weeks = pd.concat({w: W[w][:"2026-05-10"] for w in WIKIS})
window_weeks = W["dse"][WINDOW[0]:WINDOW[1]]
def empirical_tail(x, ref):                                          # Phipson & Smyth (2010): never zero
    return float((np.sum(np.asarray(ref) >= x) + 1) / (len(ref) + 1))
R["noise_floor"] = {"n_reference_weeks": int(len(ref_weeks)), "max_reference_week": int(ref_weeks.max()),
                    "max_reference_week_where": [ref_weeks.idxmax()[0], str(ref_weeks.idxmax()[1].date())],
                    "dse_record_week_before_2026": [int(W["dse"][:"2025"].max()), str(W["dse"][:"2025"].idxmax().date())],
                    "window_weeks_top3": [[int(x), empirical_tail(x, ref_weeks.values)]
                                          for x in sorted(window_weeks.values, reverse=True)[:3]]}
fig, ax = plt.subplots(figsize=(5.2, 2.5))
bins = np.logspace(0, np.log10(max(ref_weeks.max(), window_weeks.max()) + 1), 40)
ax.hist(ref_weeks.values + 1, bins=bins, color=GREY, alpha=0.85, label=f"{len(ref_weeks):,} pre-incident weeks, four wikis")
for x in window_weeks.values:
    ax.axvline(x + 1, color=OCHRE, lw=0.9)
ax.plot([], [], color=OCHRE, label="incident weeks on DSE")
ax.set_xscale("log"); ax.set_xlabel("edits per week + 1"); ax.set_ylabel("number of weeks"); ax.legend(frameon=False, fontsize=7.5)
save(fig, "fig2_noise_floor")

# ---------------------------------------------------------------- Figure 3: change point
def poisson_changepoint(counts):
    x = np.asarray(counts, dtype=float); n = len(x); cs = np.cumsum(x); S = cs[-1]
    ll = lambda s, m: s * np.log(s / m) - s if s > 0 else 0.0     # Poisson segment log-likelihood at its MLE
    prof = np.full(n, np.nan)
    for tau in range(1, n):
        prof[tau] = ll(cs[tau - 1], tau) + ll(S - cs[tau - 1], n - tau) - ll(S, n)
    t = int(np.nanargmax(prof)); return t, float(prof[t]), prof

series = D["dse"]["2026-03-01":"2026-07-14"]
tau, llr, prof = poisson_changepoint(series.values)
rng = np.random.default_rng(0)
sims = np.array([poisson_changepoint(rng.poisson(series.mean(), len(series)))[1] for _ in range(500)])
R["changepoint"] = {"date": str(series.index[tau].date()), "llr": llr, "bootstrap_p": float((np.sum(sims >= llr) + 1) / 501)}
fig, ax = plt.subplots(figsize=(6.4, 2.5))
ax.plot(series.index, prof, color=SAGE, lw=1)
ax.axvline(series.index[tau], color=OCHRE, label=f"estimated break, {series.index[tau]:%d %b}")
ax.axvline(FIRST_WRITE, color=PLUM, ls="--", label="first agent write, 24 May")
ax.set_ylabel("log-likelihood ratio"); ax.xaxis.set_major_locator(mdates.MonthLocator()); ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
ax.legend(frameon=False, fontsize=7.5)
save(fig, "fig3_changepoint")

# ---------------------------------------------------------------- Figure 4: DiD and placebo
t, c = np.log1p(W["dse"]), np.log1p(W["wiki4d"])
def did(pre_sl, post_sl, loc=True):
    g = (lambda s, sl: s.loc[sl]) if loc else (lambda s, sl: s.iloc[sl])
    return float((g(t, post_sl).mean() - g(t, pre_sl).mean()) - (g(c, post_sl).mean() - g(c, pre_sl).mean()))
d_obs = did(slice("2026-03-16", "2026-05-10"), slice("2026-05-11", "2026-07-05"))
d_alt = did(slice("2026-03-30", "2026-05-24"), slice("2026-05-25", "2026-07-19"))
idx = t.index; plac = np.array([did(slice(i - 8, i), slice(i, i + 8), loc=False) for i in range(8, len(idx) - 8)
                               if pd.Timestamp("2016-01-01") <= idx[i] <= pd.Timestamp("2025-12-31")])
R["did"] = {"effect_log_points": d_obs, "effect_window_from_24_may": d_alt, "n_placebo": int(len(plac)),
            "placebo_p": float((np.sum(np.abs(plac) >= abs(d_obs)) + 1) / (len(plac) + 1)), "placebo_max_abs": float(np.abs(plac).max())}
fig, ax = plt.subplots(figsize=(5.2, 2.5))
ax.hist(plac, bins=40, color=GREY, label=f"{len(plac)} placebo start dates, 2016 to 2025")
ax.axvline(d_obs, color=OCHRE, label=f"observed, {d_obs:.2f}")
ax.set_xlabel("difference-in-differences, log points"); ax.set_ylabel("number of placebo dates"); ax.legend(frameon=False, fontsize=7.5)
save(fig, "fig4_did_placebo")

# ---------------------------------------------------------------- Figure 5: hour of day
h_human = rc["dse"][rc["dse"].ts < "2007-01-01"].ts.dt.hour.value_counts().reindex(range(24), fill_value=0)
h_agent = agents.hour_utc.value_counts().reindex(range(24), fill_value=0)
def profile_test(a, b):
    tab = np.vstack([a, b]); chi2, p, dof, _ = stats.chi2_contingency(tab)
    return {"chi2": float(chi2), "dof": int(dof), "p": float(p), "cramers_v": float(np.sqrt(chi2 / tab.sum()))}
R["hour_profile"] = profile_test(h_human.values, h_agent.values)
R["hour_profile"]["human_shifted_2h"] = profile_test(h_human.reindex((np.arange(24) - 2) % 24).values, h_agent.values)
R["hour_profile"].update({"human_peak_hour": int(h_human.idxmax()), "agent_peak_hour_utc": int(h_agent.idxmax()),
                          "agent_share_18_21_utc": float(h_agent[18:22].sum() / h_agent.sum()),
                          "n_human": int(h_human.sum()), "n_agent": int(h_agent.sum())})
fig, ax = plt.subplots(figsize=(6.4, 2.5))
ax.bar(np.arange(24) - 0.2, h_human / h_human.sum(), 0.4, color=SAGE, label=f"humans 2003 to 2006, n = {h_human.sum():,} (server local time)")
ax.bar(np.arange(24) + 0.2, h_agent / h_agent.sum(), 0.4, color=PLUM, label=f"agents May to Jul 2026, n = {h_agent.sum():,} (UTC)")
ax.set_xticks(range(0, 24, 2)); ax.set_xlabel("hour of day"); ax.set_ylabel("share of edits"); ax.legend(frameon=False, fontsize=7.5)
save(fig, "fig5_hour_profiles")

# ---------------------------------------------------------------- Figure 6: page families; churn
fam = agents.assign(week=agents.time.dt.to_period("W").dt.start_time).groupby(["week", "page_family"]).size().unstack(fill_value=0)
top = fam.sum().sort_values(ascending=False).head(6).index
R["page_families_top"] = {k: int(v) for k, v in fam.sum().sort_values(ascending=False).head(6).items()}
sh6 = fam[top].div(fam.sum(axis=1), axis=0)
fig, ax = plt.subplots(figsize=(6.4, 2.8))
ax.stackplot(sh6.index, [sh6[c].values for c in top], labels=list(top), colors=plt.get_cmap("Set2").colors[:len(top)], lw=0)
ax.set_ylabel("share of the week's edits"); ax.set_ylim(0, 1)
ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MO)); ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
ax.legend(frameon=False, fontsize=6.5, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.22))
save(fig, "fig6_page_families")

def churn(names):
    cnt = names.value_counts(); return {"n_names": int(len(cnt)), "single_use_share": float((cnt == 1).mean()), "median_edits_per_name": float(cnt.median())}
R["name_churn"] = {"humans_2003_06": churn(rc["dse"][rc["dse"].ts < "2007-01-01"].editor), "agents": churn(agents.label.fillna(""))}

# ---------------------------------------------------------------- Figure 7: intent lexicon
if (RAW / "revisions.jsonl").exists():
    bodies = pd.DataFrame([(r["time"], r["body"]) for r in map(json.loads, open(RAW / "revisions.jsonl"))], columns=["time", "body"])
    bodies["time"] = pd.to_datetime(bodies.time, utc=True).dt.tz_convert(None)
    INTENTS = {"asks for an answer": r"\bplease\b|\brequest\b|\bneed(s|ed)?\b|\banyone\b",
               "shares an answer": r"\banswer(ed|s)?\b|\bconfirmed\b|\bresult\b|\bsolution\b",
               "relay / coordination": r"\brelay\b|\bsequence\b|\bcohort\b|\bpointer\b|\bnext\b|\bcache\b",
               "timer / deadline": r"\bdeadline\b|\btimer\b|\bclock\b|\bcooldown\b|\bimmediately\b",
               "bypass / sandbox": r"\bbypass\b|\bproxy\b|\bssh\b|\btunnel\b|\bsandbox\b|\bblock(ed)?\b|\brestrict|\bworkaround\b|\bxss\b|<script",
               "task data URL": r"datausa|tesseract|api\.|jsonrecords"}
    day = bodies.time.dt.floor("D")
    shares = pd.DataFrame({k: bodies.body.str.contains(rx, case=False, regex=True).groupby(day).mean() for k, rx in INTENTS.items()})
    n_day = bodies.groupby(day).size()
    R["intent_shares_peak_week_mean"] = {k: float(v) for k, v in shares["2026-06-16":"2026-06-22"].mean().items()}
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    sh = shares[n_day >= 20]                                        # days with fewer than 20 messages are not shown
    for k in INTENTS: ax.plot(sh.index, sh[k], marker="o", ms=2.5, lw=1, label=k)
    ax.set_ylabel("share of the day's messages"); ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b")); ax.set_ylim(0, 1)
    ax.legend(frameon=False, fontsize=6.5, ncol=3, loc="upper left")
    save(fig, "fig7_intent_shares")

# ---------------------------------------------------------------- Figure 8: weekly check
def weekly_features(edits):
    e = edits.set_index("ts").sort_index(); e = e.assign(evening=(e.index.hour >= 18).astype(float)); g = e.resample("W-MON")
    f = pd.DataFrame({"n_edits": g.size(), "n_editors": g.editor.nunique(), "n_pages": g.page.nunique(), "share_evening": g.evening.mean()})
    return f.reindex(pd.date_range("2003-01-06", "2026-09-14", freq="W-MON")).fillna(0.0)
feats = {w: weekly_features(rc[w]) for w in WIKIS}
ref = pd.concat([f[:"2026-05-10"] for f in feats.values()])
cols = ["n_edits", "n_editors", "n_pages", "share_evening"]
refv = {c: np.sort(ref.loc[ref.n_edits >= 20, c].values if c.startswith("share") else ref[c].values) for c in cols}
def tail(c, x):                                                     # strict '>' so a record-equalling week reaches the floor 1/(n+1)
    r = refv[c]; return (len(r) - np.searchsorted(r, x, side="right") + 1) / (len(r) + 1)
def score(f):
    s = pd.Series(0.0, index=f.index)
    for tt, row in f.iterrows():
        if row.n_edits == 0: continue
        use = cols if row.n_edits >= 20 else cols[:3]                # a share on a handful of edits is noise
        s[tt] = max(-np.log10(tail(cc, row[cc])) for cc in use)
    return s
scores = {w: score(f) for w, f in feats.items()}
floor = np.log10(len(ref) + 1); n_tests = sum(len(s["2016":]) for s in scores.values())
R["weekly_check"] = {"n_reference_weeks": int(len(ref)), "score_floor": float(floor), "weeks_tested_since_2016": int(n_tests),
                     "bonferroni_score": float(-np.log10(0.05 / n_tests)), "alarms": {}}
for w, s in scores.items():
    al = s[s >= floor - 1e-9]
    R["weekly_check"]["alarms"][w] = {"in_window": [str(d.date()) for d in al.index if WINDOW[0] <= d <= WINDOW[1] + pd.Timedelta(days=7)],
                                      "2016_2025": [str(d.date()) for d in al.index if pd.Timestamp("2016-01-01") <= d < pd.Timestamp("2026-01-01")],
                                      "all": [str(d.date()) for d in al.index]}
fig, ax = plt.subplots(figsize=(7.2, 2.5))
for w, s in scores.items():
    ss = s["2016":]; ax.plot(ss.index, ss.values, lw=0.8, label=w, color=SAGE if w == "dse" else PLUM, alpha=1 if w == "dse" else 0.45)
ax.axhline(floor, color=OCHRE, ls=":", lw=0.8, label="alarm level (beats all reference weeks)")
ax.axvspan(*WINDOW, color=OCHRE, alpha=0.3); ax.set_ylabel("score, -log10 empirical tail")
ax.xaxis.set_major_locator(mdates.YearLocator()); ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax.set_ylim(0, floor + 0.6); ax.legend(frameon=False, fontsize=7, ncol=5, loc="upper center", bbox_to_anchor=(0.5, -0.18))
save(fig, "fig8_weekly_check")

# ---------------------------------------------------------------- robustness: dump vs live inside the window
ld = D["dse"][WINDOW[0]:WINDOW[1]]; ad = D["dump"][WINDOW[0]:WINDOW[1]]
R["robustness"] = {"live_vs_dump_spearman_daily": float(stats.spearmanr(ld, ad).statistic),
                   "live_window_edits_without_moderator": R["reconcile"]["live_by_others"]}

json.dump(R, open(ROOT / "results.json", "w"), indent=1, default=str)
print(json.dumps(R, indent=1, default=str)[:3000])
