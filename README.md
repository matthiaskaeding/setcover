# Set cover algorithms

High performance implementation of set-cover algorithms.

* `RcppGreedySetCover`: R package using C++.
* `crates/setcover-core`: Rust implementation of the greedy algorithm, roughly
  **3–4× faster** end to end than `RcppGreedySetCover` 0.1.1. That gap comes
  from design differences rather than the choice of language — see
  [docs/benchmarks.md](docs/benchmarks.md) for the numbers and the caveats.
* `py-setcover`: Python bindings for the Rust crates, using Narwhals to stay
  dataframe-agnostic.

Benchmarks can be run vis `make bench_alot`.
