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

| n_sets  | universe | rows | seed | `py-setcover` | `greedySetCover` 0.1.1 | ratio | cover size (Py / R) |
| ------- | -------- | ---- | ---- | ------------- | ---------------------- | ----- | ------------------- |
| 150,000 | 2,000    | 12M  | 111  | 8.2           | 46.3                   | 5.6×  | 47 / 47             |
| 40,000  | 8,000    | 9M   | 222  | 5.4           | 24.2                   | 4.5×  | 100 / 99            |
| 80,000  | 4,000    | 10M  | 333  | 6.2           | 31.5                   | 5.1×  | 72 / 72             |

Measured on an Intel Xeon @ 2.10GHz (4 vCPU), 15 GB RAM, Ubuntu 24.04, with
rustc 1.97.1 (release profile), Python 3.11.15 / polars 1.35.2 / narwhals
2.12.0, and R 4.3.3 / data.table 1.14.10. Both packages compile with the same
toolchain; `RcppGreedySetCover` builds as `gnu++17`.

These are single runs on a shared 4 vCPU container, not a quiet benchmarking
machine. Repeat runs moved individual timings by 10–30%. Treat the order of
magnitude as solid and any given digit as not.

## Not an apples-to-apples comparison

The two functions return different things. `greedySetCover()` — the only one
CRAN 0.1.1 exports — returns a row per *element*, while `py-setcover` returns a
row per *chosen set*: thousands of rows versus dozens. The R side does more work
to return more data, so the ratio overstates the difference between the solvers.

Against this repo's newer `setcover()`, which also returns a row per chosen set,
it is **3.7–4.2×**. The remaining gap is design rather than language — both
sides are compiled native code.

## Tie-breaking

The two implementations break ties differently — Rust takes the first set with
the maximal gain, while boost's `ordered_non_unique` index picks an arbitrary
one among equals. Both answers are valid greedy covers, but they need not be
identical, which is why scenario 2 lands on 100 sets versus 99. Do not assert
equal output across the two.

## Running them yourself

```r
install.packages("RcppGreedySetCover")   # the baseline, currently 0.1.1
```

```bash
make bench_alot                       # the three scenarios above
make bench N_SETS=... N_ELEMENTS=... N_ROWS=... SEED=...
```

`scripts/benchmark/time_r.r` prints the `RcppGreedySetCover` version it loaded,
so the output records which package was actually measured. See
`scripts/benchmark/README.md` for the individual steps.
