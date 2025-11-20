# Run benchmarks

`scripts/benchmark/time_py.py` now generates its own datasets and benchmarks the
Rust-backed Python bindings. The defaults match the previous `make_data.r`
settings, but you can adjust them, e.g.:

```bash
uv run --with numpy --with polars scripts/benchmark/time_py.py \
  --n-sets 100000 --n-elements 2000 --n-rows 10000000 --seed 333
```

Pass `--export-csv scripts/benchmark/data.csv --skip-bench` to produce the
long-form dataset without running the Python timings; this is what `just
prep-bench` now does so that `just rtime` (which still uses the R benchmark) has
fresh input. As before, use `just pytime` to install the wheel in release mode
before running the benchmark.
