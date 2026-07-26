# RcppGreedySetCover 0.2.0

## Breaking changes

`setcover()` returns a `data.table`, not a vector of labels.

It previously returned the chosen set labels sorted alphabetically. It now
returns one row per chosen set, **in greedy selection order**, with four
columns:

| column  | meaning                                              |
| ------- | ---------------------------------------------------- |
| `set`   | the chosen set label                                 |
| `step`  | selection order, starting at 1                       |
| `n_new` | elements this pick was the first to cover            |
| `n_cum` | running total, reaching the universe size in the last row |

The ordering is the point: greedy set cover builds its answer as a sequence, so
any prefix is itself a good partial cover. `head(res, 10)` is the ten sets that
cover the most. Sorting the labels threw that away, along with the marginal
gain the solver had already computed.

To restore the old return value exactly:

```r
sort(setcover(X)$set)
```

`setcover()` is also quiet now. It previously printed the solver's coverage
progress on every call; pass `verbose = TRUE` if you relied on that output.

`greedySetCover()` is **not** affected. Its return value and its console output
are unchanged.

## New features

* `setcover()` takes `set_col`/`el_col` by name or position, defaulting to the
  first two columns. Other columns are ignored, so the input no longer has to
  be exactly two columns wide.
* `greedySetCover()` gained a `verbose` argument. It defaults to `TRUE`, so
  existing behaviour is unchanged; pass `FALSE` to silence the coverage
  progress it previously always printed.

# RcppGreedySetCover 0.1.0

* Initial release of implementation of the greedy set cover algorithm via Rcpp.
