"""Generate the synthetic weekly panel used by analyze.py.

Every number here is invented for illustration. The generator is seeded so
the CSV is reproducible; the point is the analytical design, not the data.
"""
import numpy as np
import pandas as pd
from pathlib import Path

SEED = 7
START = "2019-01-07"
END = "2021-06-28"
# Lockdown window used as the "treatment" period in the analysis.
LOCKDOWN_START = "2020-03-16"
LOCKDOWN_END = "2020-06-30"

rng = np.random.default_rng(SEED)
weeks = pd.date_range(START, END, freq="W-MON")
n = len(weeks)
t = np.arange(n)

# --- avg watch hours per user per week -------------------------------------
# Base level with mild seasonality and noise, then a lockdown bump that
# fades, plus a small permanently elevated post level.
seasonal = 0.6 * np.sin(2 * np.pi * t / 52)
hours = 8.5 + seasonal + rng.normal(0, 0.35, n)
lock = (weeks >= LOCKDOWN_START) & (weeks <= LOCKDOWN_END)
weeks_since_lock = np.clip(
    (weeks - pd.Timestamp(LOCKDOWN_START)).days.to_numpy() / 7, 0, None)
bump = 3.2 * np.exp(-weeks_since_lock / 6.0)
hours = hours + np.where(lock | (weeks > LOCKDOWN_END), bump, 0.0)
hours = np.where(weeks > LOCKDOWN_END, hours + 0.7, hours)
hours = np.clip(hours, 1.0, None)

# --- new signups per week ---------------------------------------------------
signups = 1200 + rng.normal(0, 90, n)
spike = 1100 * np.exp(-weeks_since_lock / 5.0)
signups = signups + np.where(weeks >= LOCKDOWN_START, spike, 0.0)
signups = np.where(weeks > LOCKDOWN_END, signups + 150, signups)
signups = np.clip(signups, 100, None).round().astype(int)

# --- genre share of watch hours --------------------------------------------
# Comfort viewing tilt during lockdown: comedy and documentary up,
# drama and action down. Shares renormalized each week.
base = np.array([0.32, 0.28, 0.25, 0.15])  # drama, comedy, action, documentary
tilt = np.array([-0.04, 0.05, -0.04, 0.03])
noise = rng.normal(0, 0.008, (n, 4))
shares = base + noise + np.where(lock[:, None], tilt * np.exp(-weeks_since_lock / 8.0)[:, None], 0.0)
shares = np.clip(shares, 0.02, None)
shares = shares / shares.sum(axis=1, keepdims=True)

df = pd.DataFrame({
    "week": weeks.date.astype(str),
    "new_signups": signups,
    "avg_hours_per_user": np.round(hours, 2),
    "share_drama": np.round(shares[:, 0], 4),
    "share_comedy": np.round(shares[:, 1], 4),
    "share_action": np.round(shares[:, 2], 4),
    "share_documentary": np.round(shares[:, 3], 4),
})
out = Path(__file__).resolve().parent.parent / "data" / "synthetic_weekly.csv"
out.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(out, index=False)
print(f"Wrote {len(df)} synthetic weeks to {out}")
