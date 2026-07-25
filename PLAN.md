# Next steps

Prioritized plan as of 2026-07-25. Rust suite passes (8/8); no CI exists yet.

## 1. CI (highest value)

No `.github/` directory — nothing runs on push/PR.

- Add a GitHub Actions workflow: `cargo fmt --check`, `cargo clippy`, `cargo test`,
  maturin build + `pytest` for `py-setcover`, `ruff check`.
- Optional second job: `R CMD check` for `rcpp_greedy_set_cover`.

## 2. Correctness fixes (py-setcover)

- **Dedupe (set, element) pairs in the DataFrame path.** The mapping path
  dedupes; the DataFrame path does not. `greedy_set_cover_dense` counts
  duplicate elements multiple times when scoring gains, so repeated long-format
  rows can make greedy pick a worse set. Add `.unique()` after `drop_nulls`
  plus a regression test with duplicated rows.
- Finish the TODO in `test_map_to_ints_dense_ids_with_pandas`: assert both id
  columns cover exactly `0..n-1`.

## 3. Error handling (setcover-core)

- `greedy_set_cover` / `run_greedy` panic on unknown algo or uncoverable input.
  Return `Result`/`Option` instead and map to Python exceptions in the
  bindings (the dense binding already does this; the four typed variants abort
  the interpreter on failure).

## 4. API cleanup

- Expose `algo` in the Python `setcover()` (currently only the dense path is
  reachable; bitset/textbook are dead from the public API). Alternatively pick
  the algorithm automatically from problem shape (bitset wins for small
  universes).
- Remove `greedy_set_cover_int_elements` (exact duplicate of
  `greedy_set_cover`) and the unused typed pyfunctions in `py-setcover/src/lib.rs`,
  or route `setcover()` through them.
- `materialize_sets` sorts keys via `format!("{:?}")` — use `Ord` directly.

## 5. Repo hygiene

- Delete leftover `rcpp_greedy_set_cover/Justfile` (root justfile was replaced
  by the Makefile).
- Update `AGENTS.md`: it still documents `just` targets; the workflow is `make`.

## 6. Benchmarks & docs

- Commit a benchmark results table (from `make bench_alot`) to back the "5×
  faster" claim in `README.md`.
- Document the Python API (DataFrame + mapping inputs) in `py-setcover/README.md`.

## 7. Release path (later)

- Version and publish `py-setcover` wheels to PyPI via CI (maturin).
- Decide whether the R `setcover()` labels API warrants a CRAN update.
