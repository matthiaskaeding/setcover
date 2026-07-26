# Set cover algorithms

High performance implementation of set-cover algorithms.

Given a collection of sets, find the fewest of them whose union still contains
every element:

```
A = {1, 2}   B = {1, 2, 3}   C = {4, 5}
cover: B, C          A is redundant, B already covers 1 and 2
```

Finding the smallest cover is NP-hard, so these packages use the standard
greedy approximation: repeatedly take the set covering the most
still-uncovered elements. That lands within a `ln(n)` factor of optimal and
runs comfortably over tens of millions of rows.

* `RcppGreedySetCover`: R package using C++.
* `crates/setcover-core`: Rust implementation of the greedy algorithm, roughly
  **5× faster** than `RcppGreedySetCover` 0.1.1 on CRAN. Not a perfect
  comparison — see [docs/benchmarks.md](docs/benchmarks.md) for details.
* `py-setcover`: Python bindings for the Rust crates, using Narwhals to stay
  dataframe-agnostic.

Run the benchmarks with `make bench_alot`.
