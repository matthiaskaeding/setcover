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

3. Time the Rcpp implementation:

```bash
Rscript scripts/benchmark/time_r.r scripts/benchmark/data.csv
```

The `just bench` recipe automates this (`prep-bench`, `pytime`, and `rtime`) so
you can compare outputs side by side after a single command.
