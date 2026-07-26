# Run benchmarks

1. Generate a shared dataset:

```bash
uv run scripts/benchmark/make_data.py \
  --n-sets 100000 --n-elements 2000 --n-rows 10000000 --seed 333 \
  --output scripts/benchmark/data.csv
```

2. Time the Python/Rust bindings:

```bash
uv run scripts/benchmark/time_py.py --data-csv scripts/benchmark/data.csv
```

3. Time the Rcpp implementation. Install the CRAN release first — that is the
   documented baseline:

```r
install.packages("RcppGreedySetCover")
```

```bash
Rscript scripts/benchmark/time_r.r scripts/benchmark/data.csv pairs
```

   `pairs` times `greedySetCover()`, the only function the CRAN release
   exports. The script prints the package version it loaded, so the output
   records what was actually measured.

   `setcover` times this repo's newer entry point instead, which returns one
   row per chosen set and so is closer to a like-for-like comparison — but it
   does not exist in the released package, and the script errors if you ask
   for it against a version that lacks it. Run one function per process:
   sharing one gives the second a warm cache.

`make bench` automates all of this (`prep-bench`, `pytime`, `rtime`, then
cleanup) so you can compare outputs side by side after a single command, and
`make bench_alot` runs the three scenarios reported in the root README. Both
accept `N_SETS`, `N_ELEMENTS`, `N_ROWS` and `SEED` overrides.
