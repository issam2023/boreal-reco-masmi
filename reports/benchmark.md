# Boréal Marché — Apriori benchmark

Measured on Linux-7.2.11-200.fc44.x86_64-x86_64-with-glibc2.43

- RAM available: 39.11 GiB
- Python: 3.12.15
- Apriori `low_memory`: True
- Rule confidence threshold: 0.2
- Peak memory is sampled process RSS (MiB), not exact allocation peak.

| min_support | itemsets | rules | time_seconds | peak_rss_mib | outcome |
|---|---|---|---|---|---|
| 0.05 | 191 | 282 | 2.93 | 1155.26 | ok |
| 0.02 | 658 | 3159 | 6.37 | 1158.32 | ok |
| 0.01 | 2267 | 9736 | 14.98 | 1159.63 | ok |
| 0.005 | 7106 | 28433 | 33.48 | 1167.78 | ok |

## Interpretation

Lowest-support run: 7106 itemsets, 28433 rules in 33.48 seconds; outcome: ok.

## Apriori memory limitation

Candidate generation can allocate large intermediate arrays. `low_memory=True` trades speed for lower memory use. A default-mode MemoryError was not experimentally reproduced in this notebook.

## Recommendation coverage

58 of 98 catalogue products = 59.2%.

## Known limitations

1. **Cold start and sparse rules:** uncommon items may have no qualifying rules; use popularity fallback and consider content-based recommendations.
2. **Seasonal changes:** annual rules can become stale; re-mine periodically and monitor seasonal differences.
3. **Correlation is not causation:** co-purchase association alone does not prove one product causes purchase of another.
