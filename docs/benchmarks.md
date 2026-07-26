# Benchmarks

`py-setcover` against **`RcppGreedySetCover` 0.1.1 as published on CRAN**
(released 2025-12-17), installed with `install.packages("RcppGreedySetCover")`.

The baseline is deliberately the released package rather than this repo's copy
of it. A published release is a fixed artifact, so these numbers stay
reproducible and meaningful no matter how the R package in this repository
evolves — including if it is eventually ported onto the Rust core (#35).

## Results

Reproduce with `make bench_alot`. Each scenario generates a random long-form
dataset with a fixed seed, then times the solve only — CSV loading is excluded.

Times are seconds, lower is better.

Both sides return the same thing: one row per element. `setcover(..., pairs=True)`
matches what `greedySetCover()` returns, so this is a like-for-like comparison.

| n_sets  | universe | rows | seed | `setcover(pairs=True)` | `greedySetCover` 0.1.1 | ratio |
| ------- | -------- | ---- | ---- | ---------------------- | ---------------------- | ----- |
| 150,000 | 2,000    | 12M  | 111  | 7.9                    | 35.2                   | 4.5×  |
| 40,000  | 8,000    | 9M   | 222  | 4.3                    | 20.4                   | 4.7×  |
| 80,000  | 4,000    | 10M  | 333  | 4.9                    | 25.2                   | 5.1×  |

The default return shape, one row per chosen set, times about the same: 6.0 /
4.5 / 4.6 seconds.

Measured on an Intel Xeon @ 2.10GHz (4 vCPU), 15 GB RAM, Ubuntu 24.04, with
rustc 1.97.1 (release profile), Python 3.11.15 / polars 1.35.2 / narwhals
2.12.0, and R 4.3.3 / data.table 1.14.10. Both packages compile with the same
toolchain; `RcppGreedySetCover` builds as `gnu++17`.

These are single runs on a shared 4 vCPU container, not a quiet benchmarking
machine. Repeat runs moved individual timings by 10–30%. Treat the order of
magnitude as solid and any given digit as not.

Still two independent implementations rather than one engine behind two
bindings, so the gap is design rather than language — both sides are compiled
native code.

## Tie-breaking

The two implementations break ties differently — Rust takes the first set with
the maximal gain, while boost's `ordered_non_unique` index picks an arbitrary
one among equals. Both answers are valid greedy covers, but they need not be
identical, which is why cover sizes can differ by one. Do not assert
equal output across the two.

## Running them yourself

```r
install.packages("RcppGreedySetCover")   # the baseline, currently 0.1.1
```

```bash
make bench_alot                       # the three scenarios above
make bench N_SETS=... N_ELEMENTS=... N_ROWS=... SEED=...
```

`time_py.py --mode picks|pairs` and `time_r.r`'s second argument select the
return shape; run one per process, since sharing one gives the second a warm
cache. `time_r.r` prints the `RcppGreedySetCover` version it loaded, so the
output records which package was measured. See `scripts/benchmark/README.md`
for the individual steps.
