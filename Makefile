.PHONY: venv ctest reqs pytest test pyinstall pyinstall-rel rsyn pydebug clean pylint \
	prep-bench bench bench_alot pytime rtime time help

# Defaults for benchmark parameters (override on command line)
N_SETS ?= 100000
N_ELEMENTS ?= 2000
N_ROWS ?= 10000000
SEED ?= 333

help:
	@echo "Common targets:"
	@echo "  make test            # Run Rust + Python tests"
	@echo "  make pyinstall       # Dev install Python extension"
	@echo "  make pyinstall-rel   # Release-mode dev install"
	@echo "  make pylint          # Format + lint Python"
	@echo "  make prep-bench      # Generate benchmark data (override N_* vars)"
	@echo "  make bench           # Prep data, time Python+R, clean up"
	@echo "  make bench_alot      # Run several benchmark scenarios"

venv:
	uv venv && source .venv/bin/activate

ctest:
	cargo test

reqs:
	uv pip install -r py-setcover/pyproject.toml --all-extras --group dev

pytest:
	cd py-setcover && uv run pytest

test: ctest pytest

pyinstall:
	@echo "Installing in development mode"
	uv tool run maturin develop -m py-setcover/Cargo.toml --uv

pyinstall-rel:
	@echo "Installing in release mode"
	uv tool run maturin develop --release -m py-setcover/Cargo.toml --uv

rsyn:
	reposyn -i rcpp_greedy_set_cover/ -c

pydebug: pyinstall
	uv run python -c "import sys; print(sys.path)"
	uv run python -c "import setcover; print('Success!')"

clean:
	rm -rf py-setcover/target/
	rm -rf .venv/lib/python*/site-packages/setcover*
	rm -rf .venv/lib/python*/site-packages/_setcover*
	rm -f scripts/benchmark/data.csv

pylint:
	uv tool run ruff format py-setcover
	uv tool run ruff check --fix py-setcover

prep-bench:
	@echo "Creating simulation data with:"
	@echo "  Number of sets: $(N_SETS)"
	@echo "  Number of elements: $(N_ELEMENTS)"
	@echo "  Number of rows: $(N_ROWS)"
	@echo "  Seed: $(SEED)"
	uv run scripts/benchmark/make_data.py --n-sets $(N_SETS) --n-elements $(N_ELEMENTS) --n-rows $(N_ROWS) --seed $(SEED) --output scripts/benchmark/data.csv

bench:
	@$(MAKE) prep-bench N_SETS=$(N_SETS) N_ELEMENTS=$(N_ELEMENTS) N_ROWS=$(N_ROWS) SEED=$(SEED)
	@$(MAKE) pytime
	@$(MAKE) rtime
	@echo "Deleting simulation data"
	rm -f scripts/benchmark/data.csv

bench_alot:
	@$(MAKE) bench N_SETS=150000 N_ELEMENTS=2000 N_ROWS=12000000 SEED=111
	@$(MAKE) bench N_SETS=40000 N_ELEMENTS=8000 N_ROWS=9000000 SEED=222
	@$(MAKE) bench N_SETS=80000 N_ELEMENTS=4000 N_ROWS=10000000 SEED=333

pytime: pyinstall-rel
	uv run scripts/benchmark/time_py.py --data-csv scripts/benchmark/data.csv

rtime:
	Rscript scripts/benchmark/time_r.r scripts/benchmark/data.csv

time: pytime rtime

