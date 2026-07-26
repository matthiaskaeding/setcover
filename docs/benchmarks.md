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

## This is not an apples-to-apples comparison

Read the ratio as "the published R package takes ~5× as long to do its job",
not "the Rust solver is 5× faster than the C++ one". Three reasons, all of
which inflate the ratio:

**The two functions return different things.** `greedySetCover()` — the only
function CRAN 0.1.1 exports — returns one row per *element*, an assignment of
every element to the set that covered it. `py-setcover` returns one row per
*chosen set*. On these inputs that is thousands of rows versus dozens, so the R
side is doing strictly more work before it can return.

**The C++ always materializes that assignment.** `greedy_set_cover2`
preallocates one output row per element and fills every one of them, so the
cost is structural rather than a formatting step at the end. The Rust path
never builds it.

**Representation differs.** The C++ maintains a `boost::multi_index` of set
sizes over `unordered_set` members, so each round chases pointers and hashes
elements individually. The dense Rust solver scans flat `Vec`s against a `bool`
array — cache-friendly, though it rescans every candidate each round rather
than updating incrementally.

None of this is a language effect. Both sides are compiled native code, and
nothing measured here is faster in Rust than the same approach would be in C++.
A labels-only entry point in the C++, or a lazy priority queue on either side,
would move the number more than the choice of language does.

For calibration: a like-for-like comparison against this repository's newer
`setcover()` entry point, which also returns one row per chosen set, came out
at **3.7–4.2×** rather than ~5×. That gap between the two figures is the price
of the different return type. It is not included as a headline because that
entry point is unreleased, and comparing against unreleased code is exactly the
kind of claim that goes stale.

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
