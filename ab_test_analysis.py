"""A/B test analysis: new checkout page (Control vs Treatment)."""
import sys
import numpy as np
import pandas as pd
from scipy import stats

PATH = sys.argv[1] if len(sys.argv) > 1 else "day3_ab_test_checkout.csv"
raw = pd.read_csv(PATH)

# ---------------------------------------------------------------- Task 1
print("=== TASK 1: DATA QUALITY ===")
print("Rows:", len(raw))
print("Duplicate session_id rows (beyond first):", raw.session_id.duplicated().sum())
print("Missing values per column:\n", raw.isna().sum().to_string())
print("Variant values:", raw.variant.value_counts().to_dict())
print("Invalid variant rows:", (~raw.variant.isin(["Control", "Treatment"])).sum())
print("converted not in {0,1}:", (~raw.converted.isin([0, 1])).sum())
print("Negative revenue:", (raw.order_revenue_eur < 0).sum())
print("Revenue > 0 on non-converted:", ((raw.converted != 1) & (raw.order_revenue_eur > 0)).sum())
print("Converted with revenue <= 0:", ((raw.converted == 1) & (raw.order_revenue_eur <= 0)).sum())
print("Country values:", raw.country.value_counts().to_dict())
canon = {c.lower(): c for c in raw.country.unique() if c == c.title()}
print("Country rows not matching canonical spelling:", (raw.country != raw.country.str.lower().map(canon)).sum())

# Cleaning: keep first occurrence of each session_id (the appended repeats are the
# defective / conflicting records), then standardise text and drop anything still invalid.
df = raw.drop_duplicates("session_id", keep="first").copy()
df["variant"] = df.variant.str.strip().str.title()
df["country"] = df.country.str.strip().str.lower().map(canon)
valid = (
    df.variant.isin(["Control", "Treatment"])
    & df.converted.isin([0, 1])
    & (df.order_revenue_eur >= 0)
    & ~((df.converted == 0) & (df.order_revenue_eur > 0))
    & df.isna().sum(axis=1).eq(0)
)
print(f"Rows removed: {len(raw) - valid.sum()} -> valid sessions: {valid.sum()}")
df = df[valid].copy()

# ---------------------------------------------------------------- Task 2
print("\n=== TASK 2: KPIs ===")


def kpis(g):
    n, c = len(g), int(g.converted.sum())
    rev = g.order_revenue_eur.sum()
    return pd.Series({
        "sessions": n, "conversions": c, "conv_rate_%": c / n * 100,
        "avg_order_rev_EUR": rev / c if c else np.nan,
        "total_rev_EUR": rev, "rev_per_session_EUR": rev / n,
    })


k = df.groupby("variant").apply(kpis, include_groups=False).loc[["Control", "Treatment"]]
print(k.round(3).to_string())
cr_c, cr_t = k.loc["Control", "conv_rate_%"], k.loc["Treatment", "conv_rate_%"]
print(f"Absolute lift: {cr_t - cr_c:.3f} pp | Relative lift: {(cr_t - cr_c) / cr_c * 100:.2f}%")
rps_c, rps_t = k.loc["Control", "rev_per_session_EUR"], k.loc["Treatment", "rev_per_session_EUR"]
print(f"Revenue/session diff: EUR {rps_t - rps_c:.3f} ({(rps_t - rps_c) / rps_c * 100:.2f}%)")

# ---------------------------------------------------------------- Task 3
print("\n=== TASK 3: TWO-PROPORTION Z-TEST ===")


def ztest(x1, n1, x2, n2):
    """x1/n1 = Control, x2/n2 = Treatment. Pooled z-test, two-sided."""
    p1, p2 = x1 / n1, x2 / n2
    pp = (x1 + x2) / (n1 + n2)
    se = np.sqrt(pp * (1 - pp) * (1 / n1 + 1 / n2))
    z = (p2 - p1) / se
    p = 2 * (1 - stats.norm.cdf(abs(z)))
    se_u = np.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    ci = (p2 - p1 - 1.96 * se_u, p2 - p1 + 1.96 * se_u)
    return z, p, ci


C, T = df[df.variant == "Control"], df[df.variant == "Treatment"]
z, p, ci = ztest(C.converted.sum(), len(C), T.converted.sum(), len(T))
print(f"z = {z:.4f}, p = {p:.4f}, 95% CI of diff = [{ci[0]*100:.3f}, {ci[1]*100:.3f}] pp")
print("Reject H0 at alpha=0.05" if p < 0.05 else "Fail to reject H0 at alpha=0.05")

# Revenue per session (Welch t-test, supplementary)
t, pt = stats.ttest_ind(T.order_revenue_eur, C.order_revenue_eur, equal_var=False)
print(f"Revenue/session Welch t-test: t = {t:.3f}, p = {pt:.4f}")
# AOV among converters
t2, p2 = stats.ttest_ind(T[T.converted == 1].order_revenue_eur,
                         C[C.converted == 1].order_revenue_eur, equal_var=False)
print(f"AOV (converters) Welch t-test: t = {t2:.3f}, p = {p2:.4f}")

# Sample-size context: power for observed effect and MDE
p1 = C.converted.mean()
n = min(len(C), len(T))
mde = (1.96 + 0.84) * np.sqrt(2 * p1 * (1 - p1) / n)
print(f"Approx. minimum detectable effect (80% power): {mde*100:.2f} pp absolute")
d = abs(T.converted.mean() - p1)
if d > 0:
    need = 2 * ((1.96 + 0.84) ** 2) * p1 * (1 - p1) / d ** 2
    print(f"Sessions per arm needed to detect observed diff at 80% power: {need:,.0f}")

# ---------------------------------------------------------------- Task 4
print("\n=== TASK 4: SEGMENTS ===")
rows = []
for dim in ["device", "customer_type", "country", "acquisition_channel"]:
    for val, g in df.groupby(dim):
        c, t_ = g[g.variant == "Control"], g[g.variant == "Treatment"]
        z_, p_, ci_ = ztest(c.converted.sum(), len(c), t_.converted.sum(), len(t_))
        crc, crt = c.converted.mean() * 100, t_.converted.mean() * 100
        rows.append({
            "dimension": dim, "segment": val, "n_ctrl": len(c), "n_trt": len(t_),
            "conv_ctrl_%": crc, "conv_trt_%": crt, "abs_lift_pp": crt - crc,
            "rel_lift_%": (crt - crc) / crc * 100 if crc else np.nan,
            "z": z_, "p_value": p_,
            "rps_ctrl": c.order_revenue_eur.mean(), "rps_trt": t_.order_revenue_eur.mean(),
            "small_segment": min(len(c), len(t_)) < 300,
        })
seg = pd.DataFrame(rows)
print(seg.round(3).to_string(index=False))
n_tests = len(seg)
print(f"\nBonferroni threshold for {n_tests} segment tests: {0.05 / n_tests:.4f}")
print("Segments with p<0.05 (uncorrected):")
print(seg[seg.p_value < 0.05][["dimension", "segment", "n_ctrl", "n_trt", "abs_lift_pp", "p_value"]]
      .round(4).to_string(index=False))

# daily consistency check
daily = df.groupby(["experiment_date", "variant"]).converted.mean().unstack() * 100
daily["diff_pp"] = daily.Treatment - daily.Control
print("\nDays where Treatment > Control:", int((daily.diff_pp > 0).sum()), "of", len(daily))

# save outputs
k.round(4).to_csv("kpi_table.csv")
seg.round(4).to_csv("segment_results.csv", index=False)
df.to_csv("clean_data.csv", index=False)
