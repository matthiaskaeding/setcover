# Repository Guidelines

## Project Structure & Module Organization
Rust sources live under `crates/setcover-core/src`, providing the shared greedy set-cover logic used by every consumer. The Python bindings reside in `py-setcover/src` with the wheel metadata in `py-setcover/pyproject.toml`; tests for that package are under `py-setcover/tests`. The Rcpp wrapper sits in `rcpp_greedy_set_cover`, and benchmarking scripts plus supporting data generators live in `scripts/benchmark`. Build artifacts are staged in `target/` (Rust) and `py-setcover/dist/`, while distributable documentation is mirrored in `dist/`.

## Build, Test, and Development Commands
Use the `just` targets to keep workflows reproducible: `just ctest` runs `cargo test` across all Rust crates, `just pyinstall` performs a development `maturin develop` build so the Python package can be imported locally, and `just pytest` executes the Python suite via `uv run pytest py-setcover/tests`. `just test` chains both test stacks for CI parity, while `just prep-bench`/`pytime`/`rtime` orchestrate reproducible benchmark data and timings. When debugging or validating installs, `just pydebug` confirms the package resolves on the active `uv` virtualenv.

## Coding Style & Naming Conventions
Rust code should remain `cargo fmt` clean with 4-space indentation, idiomatic `snake_case` symbols, and early returns for impossible states. Python follows `ruff format` defaults, also 4 spaces, with modules and functions in `snake_case` and classes in `CamelCase`. Run `just pylint` (which wraps `ruff format` and `ruff check --fix`) before submitting; do not hand-edit generated bindings in `py-setcover/setcover`.

## Testing Guidelines
Prefer narrow, deterministic tests: Rust unit tests colocated next to the implementation in `crates/setcover-core/src`, and Python tests named `test_*.py` inside `py-setcover/tests`. Add regression fixtures whenever covering new benchmark scenarios. Execute `just test` before opening a PR; when touching both languages, include evidence that `cargo test` and `uv run pytest` both pass.

## Commit & Pull Request Guidelines
Repository history uses concise, imperative commit subjects (e.g., `Add parameters to benchmark`) that optionally reference the tracking issue using `(#NN)`. Follow that style and keep each commit focused on a single concern. Pull requests should describe the algorithmic change, mention affected crates (`setcover-core`, `py-setcover`, etc.), link to any benchmarks or tickets, and attach timing tables or screenshots whenever performance is cited. Cross-language updates must explain how the Rust core and bindings stay in sync.

## Security & Configuration Tips
Benchmark scripts read and write under `scripts/benchmark`; never point them at external data without sanitizing inputs. Use `uv venv` (`just venv`) to build an isolated environment so system-wide Python packages stay untouched. Secrets or API tokens are unnecessary for normal development—if you must handle datasets, keep them outside the repo or ensure `.gitignore` covers them.
