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

3. Time the Rcpp implementation. The second argument picks which entry point to
   time — `setcover` (one row per chosen set, the like-for-like comparison
   against Python) or `pairs` for `greedySetCover()`. Run them separately:
   sharing one process gives the second a warm cache.

```bash
Rscript scripts/benchmark/time_r.r scripts/benchmark/data.csv setcover
Rscript scripts/benchmark/time_r.r scripts/benchmark/data.csv pairs
```

`make bench` automates all of this (`prep-bench`, `pytime`, `rtime`, then
cleanup) so you can compare outputs side by side after a single command, and
`make bench_alot` runs the three scenarios reported in the root README. Both
accept `N_SETS`, `N_ELEMENTS`, `N_ROWS` and `SEED` overrides.
