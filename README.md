# Checkout A/B Test: Analysis and Recommendation

## Task 1: Data quality

| Check | Result | Action |
|---|---|---|
| Duplicate `session_id` | 5 repeated IDs (the last 5 rows of the file) | Kept first occurrence, dropped 5 repeats |
| Missing values | 0 in every column | None |
| Invalid `variant` | 1 row, `treatment` (lowercase) | Was in a dropped duplicate; standardised anyway |
| `converted` outside 0/1 | 1 row (value 2) | In a dropped duplicate |
| Negative revenue | 1 row (-15.00 EUR) | In a dropped duplicate |
| Revenue on non-converted sessions | 0 | None |
| Converted with zero revenue | 0 | None |
| Inconsistent country names | 1 row, `germany` vs `Germany` | In a dropped duplicate; standardised anyway |

Note: SES000001 appears twice with conflicting attributes (different date, country, device, customer type). I kept the original row. Result: 5,000 valid sessions (Control 2,464, Treatment 2,536). Sample-ratio check for the 50/50 split: p = 0.31, no imbalance.

## Task 2: KPIs

| Metric | Control | Treatment | Difference |
|---|---|---|---|
| Sessions | 2,464 | 2,536 | |
| Conversions | 303 | 354 | |
| Conversion rate | 12.30% | 13.96% | +1.66 pp |
| Relative lift | | | +13.5% |
| Avg order revenue (converted) | 111.44 EUR | 105.66 EUR | -5.78 EUR (-5.2%) |
| Total revenue | 33,766 EUR | 37,404 EUR | |
| Revenue per session | 13.70 EUR | 14.75 EUR | +1.05 EUR (+7.6%) |

## Task 3: Two-proportion z-test

H0: CR_T = CR_C, H1: CR_T ≠ CR_C, alpha = 0.05, pooled, two-sided.

- z = 1.739, p = 0.082
- 95% CI for the difference: -0.21 to +3.53 pp
- Conclusion: fail to reject H0. The lift is not statistically significant at 5%.
- Supplementary: revenue per session p = 0.39; average order value p = 0.23 (both not significant).
- Power: with ~2,500 sessions per arm the test could reliably detect only about 2.6 pp (80% power). Detecting the observed 1.66 pp would need about 6,100 sessions per arm.

**Statistical vs business significance.** Statistical significance asks whether the difference is unlikely to be noise. Business significance asks whether it is large enough to matter after cost, risk and effort. They can disagree: a huge test can flag a trivial lift as significant, and an underpowered test (like this one) can miss a valuable lift. Here the point estimate (+13.5% relative) would be commercially meaningful, but the evidence is not yet strong enough to rely on.

## Task 4: Segments (treatment vs control)

| Segment | n Ctrl / n Trt | CR Ctrl | CR Trt | Lift (pp) | p |
|---|---|---|---|---|---|
| Desktop | 818 / 842 | 14.55% | 15.68% | +1.13 | 0.52 |
| Mobile | 1,521 / 1,574 | 11.24% | 13.15% | +1.91 | 0.11 |
| Tablet* | 125 / 120 | 10.40% | 12.50% | +2.10 | 0.61 |
| New | 1,443 / 1,519 | 10.40% | 12.11% | +1.72 | 0.14 |
| Returning | 1,021 / 1,017 | 14.99% | 16.72% | +1.73 | 0.29 |
| Germany | 1,229 / 1,276 | 13.10% | 14.81% | +1.71 | 0.22 |
| France | 306 / 347 | 15.69% | 12.10% | -3.58 | 0.19 |
| Italy* | 335 / 299 | 9.55% | 12.04% | +2.49 | 0.31 |
| Netherlands | 323 / 351 | 12.07% | 17.38% | +5.31 | 0.053 |
| Spain* | 271 / 263 | 8.49% | 9.89% | +1.40 | 0.58 |
| Affiliate* | 204 / 193 | 11.77% | 15.03% | +3.26 | 0.34 |
| Direct | 380 / 381 | 11.32% | 12.60% | +1.28 | 0.59 |
| Email | 350 / 367 | 13.71% | 17.71% | +4.00 | 0.14 |
| Organic Search | 630 / 674 | 11.91% | 14.39% | +2.49 | 0.19 |
| Paid Search | 516 / 541 | 11.43% | 14.79% | +3.35 | 0.11 |
| Social | 384 / 380 | 14.06% | 9.21% | -4.85 | 0.037 |

*Fewer than 300 sessions in an arm: treat as directional only.

- Most promising: Mobile (largest segment with a positive lift), Email, Paid Search, and the Netherlands (+5.3 pp, borderline).
- Concerns: Social (-4.9 pp) and France (-3.6 pp) went the wrong way. Social is the only segment with p < 0.05, but with 16 segment tests the Bonferroni threshold is 0.003, so nothing here survives correction. These are hypotheses, not findings.
- The effect is positive in 13 of 16 segments and on 10 of 15 days, which is consistent with a modest real lift, but not proof.

## Task 5: Management summary

**Recommendation: do not launch on this evidence alone; extend the test.** The new checkout raised conversion from 12.30% to 13.96%, a gain of 1.66 percentage points (+13.5% relative). However, the result is not statistically significant (z = 1.74, p = 0.082), and the 95% confidence interval runs from -0.2 to +3.5 pp, so a small negative effect cannot be ruled out. The test was underpowered: it could only detect lifts of about 2.6 pp.

Revenue is encouraging but equally uncertain. Revenue per session rose from 13.70 to 14.75 EUR (+7.6%), but average order value fell about 5%, and the revenue difference is not significant (p = 0.39). If the lift is real, 100,000 monthly sessions would yield roughly 100,000 EUR extra revenue, but this is not guaranteed.

Segment results are mostly positive (Mobile, Email, Paid Search, Netherlands), but Social and France declined. These segments are too small for firm conclusions.

**Next steps:** (1) continue the test to about 6,100+ sessions per arm; (2) pre-register the primary metric (conversion) and a guardrail (revenue per session); (3) investigate why Social and France underperform; (4) if launched, use a staged rollout with monitoring of conversion, AOV and refunds, with a holdback group.
