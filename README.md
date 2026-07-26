# Set cover algorithms

High performance implementation of set-cover algorithms.

* `RcppGreedySetCover`: R package using C++.
* `crates/setcover-core`: Rust implementation of the greedy algorithm, roughly
  **5× faster** than `RcppGreedySetCover` 0.1.1 on CRAN. Not a perfect
  comparison — see [docs/benchmarks.md](docs/benchmarks.md) for details.
* `py-setcover`: Python bindings for the Rust crates, using Narwhals to stay
  dataframe-agnostic.

Run the benchmarks with `make bench_alot`.
