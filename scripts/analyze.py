"""Did streaming behavior change during the COVID-19 pandemic? A pre/post design.

Runs on the synthetic weekly panel in data/synthetic_weekly.csv and prints
period comparisons plus three charts. See README for the reasoning and the
caveats: this demonstrates the analytical design, not a real finding.

Usage:  python3 scripts/analyze.py   (from the repo root)
"""
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "synthetic_weekly.csv"
CHARTS = ROOT / "charts"

PRE_START, PRE_END = "2019-01-07", "2019-12-30"          # baseline year
LOCK_START, LOCK_END = "2020-03-16", "2020-06-30"        # lockdown window
POST_START, POST_END = "2021-01-04", "2021-06-28"        # later period

GENRES = ["drama", "comedy", "action", "documentary"]


def period_mean(df, col, start, end):
    m = (df["week"] >= start) & (df["week"] <= end)
    return df.loc[m, col].mean()


def pct_change(before, after):
    return 100.0 * (after - before) / before


def main():
    if not DATA.exists():
        raise FileNotFoundError(
            f"{DATA} not found. Run python3 scripts/generate_data.py first.")
    df = pd.read_csv(DATA, parse_dates=["week"])
    CHARTS.mkdir(exist_ok=True)

    pre_h = period_mean(df, "avg_hours_per_user", PRE_START, PRE_END)
    lock_h = period_mean(df, "avg_hours_per_user", LOCK_START, LOCK_END)
    post_h = period_mean(df, "avg_hours_per_user", POST_START, POST_END)
    pre_s = period_mean(df, "new_signups", PRE_START, PRE_END)
    lock_s = period_mean(df, "new_signups", LOCK_START, LOCK_END)
    post_s = period_mean(df, "new_signups", POST_START, POST_END)

    print("=== H1: watch time per user ===")
    print(f"pre-pandemic (2019) mean:      {pre_h:.2f} h/week")
    print(f"lockdown mean:                 {lock_h:.2f} h/week "
          f"({pct_change(pre_h, lock_h):+.1f}%)")
    print(f"2021 mean:                     {post_h:.2f} h/week "
          f"({pct_change(pre_h, post_h):+.1f}% vs 2019)")
    print()
    print("=== H2: new signups ===")
    print(f"pre-pandemic (2019) mean:      {pre_s:,.0f} /week")
    print(f"lockdown mean:                 {lock_s:,.0f} /week "
          f"({pct_change(pre_s, lock_s):+.1f}%)")
    print(f"2021 mean:                     {post_s:,.0f} /week "
          f"({pct_change(pre_s, post_s):+.1f}% vs 2019)")
    print()
    print("=== H3: genre mix (share of watch hours) ===")
    for g in GENRES:
        col = f"share_{g}"
        b = period_mean(df, col, PRE_START, PRE_END)
        d = period_mean(df, col, LOCK_START, LOCK_END)
        print(f"{g:12s} 2019: {b:.1%}  lockdown: {d:.1%}  "
              f"({pct_change(b, d):+.1f}% relative change)")

    # --- charts ------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(df["week"], df["avg_hours_per_user"], lw=1.2)
    ax.axvspan(pd.Timestamp(LOCK_START), pd.Timestamp(LOCK_END),
               color="0.85", label="lockdown window")
    ax.set_title("Synthetic avg watch hours per user per week")
    ax.set_ylabel("hours / week")
    ax.legend()
    fig.tight_layout()
    fig.savefig(CHARTS / "hours_timeseries.png", dpi=110)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(df["week"], df["new_signups"], lw=1.2, color="tab:green")
    ax.axvspan(pd.Timestamp(LOCK_START), pd.Timestamp(LOCK_END), color="0.85")
    ax.set_title("Synthetic new signups per week")
    ax.set_ylabel("signups / week")
    fig.tight_layout()
    fig.savefig(CHARTS / "signups_timeseries.png", dpi=110)
    plt.close(fig)

    pre_shares = [period_mean(df, f"share_{g}", PRE_START, PRE_END) for g in GENRES]
    lock_shares = [period_mean(df, f"share_{g}", LOCK_START, LOCK_END) for g in GENRES]
    x = range(len(GENRES))
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar([i - 0.2 for i in x], pre_shares, 0.4, label="2019 baseline")
    ax.bar([i + 0.2 for i in x], lock_shares, 0.4, label="lockdown")
    ax.set_xticks(list(x), GENRES)
    ax.set_ylabel("share of watch hours")
    ax.set_title("Synthetic genre mix: baseline vs lockdown")
    ax.legend()
    fig.tight_layout()
    fig.savefig(CHARTS / "genre_shift.png", dpi=110)
    plt.close(fig)

    print()
    print(f"Charts written to {CHARTS}/")


if __name__ == "__main__":
    main()
