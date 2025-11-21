# Set cover algorithms

High performance implementation of set-cover algorithms.

* `RcppGreedySetCover`: R package using C++.
* `crates/setcover-core`: Rust algorithms. The greedy solver here is roughly **5× faster** than `RcppGreedySetCover` implementation.
* `py-setcover`: Python bindings for the Rust crates, using Narwhals to stay dataframe-agnostic.
