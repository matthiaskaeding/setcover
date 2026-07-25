# Repository Guidelines

## Project Structure & Module Organization
Rust sources live under `crates/setcover-core/src`, providing the shared greedy set-cover logic used by every consumer. The Python bindings reside in `py-setcover/src` with the wheel metadata in `py-setcover/pyproject.toml`; tests for that package are under `py-setcover/tests`. The Rcpp wrapper sits in `rcpp_greedy_set_cover`, and benchmarking scripts plus supporting data generators live in `scripts/benchmark`. Build artifacts are staged in `target/` (Rust) and `py-setcover/dist/`, while distributable documentation is mirrored in `dist/`.

## Build, Test, and Development Commands
Use the `make` targets to keep workflows reproducible: `make ctest` runs `cargo test` across all Rust crates, `make pyinstall` performs a development `maturin develop` build so the Python package can be imported locally, and `make pytest` executes the Python suite. `make test` chains both test stacks for CI parity, while `make prep-bench`/`pytime`/`rtime` orchestrate reproducible benchmark data and timings. When debugging or validating installs, `make pydebug` confirms the package resolves on the active `uv` virtualenv.

### Rebuild the extension after touching Rust
**`uv run pytest` does not rebuild the Rust extension when Rust sources change.** uv keys its cached wheel on the package version, so as long as `py-setcover/pyproject.toml` still says `0.1.0`, edits under `crates/setcover-core/src` or `py-setcover/src` go undetected and the suite silently runs against a stale binary. The failure mode is nasty in both directions: tests blow up against an old ABI, or worse, they pass while testing code you did not write.

Always run the Python suite as `uv run --reinstall-package setcover pytest` (what `make pytest` and the CI workflow both do). A cold `uv run pytest` in a fresh checkout is fine — the hazard is only on a warm cache, which is exactly what CI restores between runs and what you have locally after the first run.

# Writing style

When updating any README.md are any other documentation write concisely.

## Coding Style & Naming Conventions
Rust code should remain `cargo fmt` clean with 4-space indentation, idiomatic `snake_case` symbols, and early returns for impossible states. Python follows `ruff format` defaults, also 4 spaces, with modules and functions in `snake_case` and classes in `CamelCase`. Run `make pylint` (which wraps `ruff format` and `ruff check --fix`) before submitting; do not hand-edit generated bindings in `py-setcover/setcover`. ruff is pinned to an exact version in both the Makefile and `.github/workflows/ci.yml` — it changes its default rule set between minor releases, so an unpinned `uv tool run ruff` lints differently locally than in CI. Bump the two in step.

## Testing Guidelines
Prefer narrow, deterministic tests: Rust unit tests colocated next to the implementation in `crates/setcover-core/src`, and Python tests named `test_*.py` inside `py-setcover/tests`. Add regression fixtures whenever covering new benchmark scenarios. Execute `make test` before opening a PR; when touching both languages, include evidence that `cargo test` and `uv run pytest` both pass.

## Git: Commit & Pull Request Guidelines
- Always create a feature branch.
- When merging feature branch to main, ALWAYS use `git merge --squash`. Afterwards delete the branch but ask first.
- Repository history uses concise, imperative commit subjects (e.g., `Add parameters to benchmark`) that optionally reference the tracking issue using `(#NN)`. Follow that style and keep each commit focused on a single concern. 
-Pull requests should describe the algorithmic change, mention affected crates (`setcover-core`, `py-setcover`, etc.), link to any benchmarks or tickets, and attach timing tables or screenshots whenever performance is cited. Cross-language updates must explain how the Rust core and bindings stay in sync.

## Security & Configuration Tips
Benchmark scripts read and write under `scripts/benchmark`; never point them at external data without sanitizing inputs. Use `uv venv` (`make venv`) to build an isolated environment so system-wide Python packages stay untouched. Secrets or API tokens are unnecessary for normal development—if you must handle datasets, keep them outside the repo or ensure `.gitignore` covers them.
