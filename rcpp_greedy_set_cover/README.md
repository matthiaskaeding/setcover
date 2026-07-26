
<!-- README.md is generated from README.Rmd. Please edit that file -->

# RcppGreedySetCover

A fast implementation of the greedy algorithm for the set cover problem
using ‘Rcpp’.

## Installation

Newest version from github:

``` r
devtools::install_github("matthiaskaeding/RcppGreedySetCover")
```

CRAN:

``` r
install.packages("RcppGreedySetCover")
```

## Usage example

``` r
# Create some data
set.seed(333)
X <- data.table::data.table(
  set = sample(1e5, 1e7, TRUE), 
  element = sample(2e3, 1e7, TRUE), 
  key = c("set", "element")
)
# Input is in long format
head(X) 
#>    set element
#> 1:   1      12
#> 2:   1      19
#> 3:   1      32
#> 4:   1      45
#> 5:   1      51
#> 6:   1      62
# Run set cover
tictoc::tic()
res <- RcppGreedySetCover::greedySetCover(X)
#> 100% covered by 42 sets.
tictoc::toc() # Takes about 10 seconds for 10 million rows on a Macbook Air M1
#> 10.509 sec elapsed
# Result is in long format
head(res) 
#>     set element
#> 1: 1689     447
#> 2: 1689     458
#> 3: 1689     505
#> 4: 1689     792
#> 5: 1689     798
#> 6: 1689     816
# Check if all elements are covered:
setequal(res$element, X$element)
#> [1] TRUE
```

## Breaking change in 0.2.0

`setcover()` used to return the chosen labels as an alphabetically sorted
vector. It now returns a `data.table` in greedy selection order — see below —
and is silent unless `verbose = TRUE`. `sort(setcover(X)$set)` reproduces the
old return value exactly. `greedySetCover()` is unaffected.

## API summary

- `greedySetCover(X, data.table = TRUE)`
  - Returns long-form pairs of `(set, element)` for the chosen cover.
  - Defaults to a keyed `data.table`; set `data.table = FALSE` for `data.frame`.

- `setcover(X, set_col = 1L, el_col = 2L, verbose = FALSE)`
  - Returns a `data.table` with one row per chosen set, **in greedy selection
    order**: `set`, `step` (starting at 1), `n_new` (elements this pick was the
    first to cover) and `n_cum` (running total). Any prefix is itself a good
    partial cover, so `head(res, 10)` is the ten sets covering the most.
  - `set_col`/`el_col` take a column name or position; other columns are ignored.
  - Quiet by default; `verbose = TRUE` prints the solver's coverage progress.

``` r
df <- data.frame(set = c("A", "A", "B", "B", "B", "C", "C"),
                 element = c(10L, 20L, 10L, 20L, 30L, 40L, 50L))
RcppGreedySetCover::setcover(df)
#>    set step n_new n_cum
#> 1:   B    1     3     3
#> 2:   C    2     2     5
```

Note `step` is 1-based here, matching R's conventions; the Python package uses
0-based `step`. The other columns are identical across the two.
