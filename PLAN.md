# Next steps

Prioritized plan as of 2026-07-25. Items 1 and 2 are done; the rest are open.

## 1. CI — DONE

`.github/workflows/ci.yml` runs three jobs on push to `main` and on every PR:
Rust (`fmt --check`, `clippy -D warnings`, `test`), Python (`ruff` plus
`pytest` on 3.10 and 3.13), and `R CMD check` for `rcpp_greedy_set_cover`.

## 2. Correctness fixes (py-setcover) — DONE

- Deduped (set, element) pairs in `map_to_ints`. `greedy_set_cover_dense`
  scores a candidate by counting its elements, so a repeated long-format row
  inflated that set's apparent gain and could pull a redundant set into the
  cover.
- Finished the TODO in `test_map_to_ints_dense_ids_with_pandas`; both id
  columns are now asserted dense over `0..n-1`.

## 2b. Rich result format — Python DONE, R open

The solvers return `Pick { set, n_new }` in greedy selection order instead of
bare sorted indices. Python's `setcover()` surfaces that as `set`, `step`,
`n_new`, `n_cum` — a native DataFrame for the DataFrame path, a list of `Step`
named tuples for the mapping path. `only_sets=True` gives labels in selection
order.

Still to do for R:
- Return an equivalent `data.table` from `setcover()`; `greedy_set_cover2`
  already appends rows in selection order, and `setkey(Out)` in the R wrapper
  is what discards it.
- Decide whether R's `step` is 0-based (parity with Python) or 1-based
  (idiomatic R). Cross-language test fixtures depend on this.
- `greedySetCover()` prints coverage to the console unconditionally, with no
  way to silence it. Add a `verbose` argument while touching this code.

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

## 5. Repo hygiene — partly done

- DONE: `AGENTS.md` now documents `make`, not the removed `just` targets, and
  carries the uv extension-staleness warning.
- Delete leftover `rcpp_greedy_set_cover/Justfile` (root justfile was replaced
  by the Makefile).
- `make reqs` is broken: it runs `uv pip install -r py-setcover/pyproject.toml
  --group dev` from the repo root, but `--group` resolves relative to the
  working directory, so it fails with "No pyproject.toml found". Run it from
  `py-setcover/`.

## 6. Benchmarks & docs — partly done

- DONE: `py-setcover/README.md` documents both input modes and the new
  `set`/`step`/`n_new`/`n_cum` result format.
- Commit a benchmark results table (from `make bench_alot`) to back the "5×
  faster" claim in `README.md`. Note the comparison is between two independent
  implementations, not two bindings over one core — R runs its own C++.
- Root `README.md` still describes the old labels-only output.

## 7. Release path (later)

- Version and publish `py-setcover` wheels to PyPI via CI (maturin).
- Decide whether the R `setcover()` labels API warrants a CRAN update.
