# RcppGreedySetCover 0.1.1

* `setcover()` returns a `data.table` of the chosen sets in greedy selection
  order — `set`, `step`, `n_new`, `n_cum` — instead of a sorted label vector.
  Any prefix of the result is itself a good partial cover, and `n_new` gives
  each pick's marginal gain.
* `setcover()` takes `set_col`/`el_col` by name or position, defaulting to the
  first two columns, and ignores any other columns.
* `setcover()` is now quiet by default; pass `verbose = TRUE` for the solver's
  coverage progress.
* `greedySetCover()` gained a `verbose` argument. It defaults to `TRUE`, so
  existing behaviour is unchanged; pass `FALSE` to silence the coverage
  progress it previously always printed.

# RcppGreedySetCover 0.1.0

* Initial release of implementation of the greedy set cover algorithm via Rcpp.




