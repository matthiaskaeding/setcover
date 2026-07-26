# Set cover algorithms

High performance implementation of set-cover algorithms.

* `RcppGreedySetCover`: R package using C++.
* `crates/setcover-core`: Rust implementation of the greedy algorithm. Covers
  the same datasets roughly **5× faster** than `RcppGreedySetCover` 0.1.1 on
  CRAN — though the two return different things, so it is not a like-for-like
  comparison. [docs/benchmarks.md](docs/benchmarks.md) has the numbers and is
  explicit about what inflates that ratio.
* `py-setcover`: Python bindings for the Rust crates, using Narwhals to stay
  dataframe-agnostic.

Run the benchmarks with `make bench_alot`.
