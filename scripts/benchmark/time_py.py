# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "numpy",
#     "polars",
# ]
# ///
import argparse
from pathlib import Path
import sys
import time

import numpy as np
import polars as pl

REPO_ROOT = Path(__file__).resolve().parents[2]
PY_PACKAGE_DIR = REPO_ROOT / "py-setcover"
if str(PY_PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PY_PACKAGE_DIR))

from setcover import setcover


def build_random_sets(
    n_sets: int, n_elements: int, n_rows: int, seed: int
) -> tuple[dict[int, list[int]], pl.DataFrame]:
    """Generate a random set dictionary and the raw long-form DataFrame."""
    rng = np.random.default_rng(seed)
    set_ids = rng.integers(low=0, high=n_sets, size=n_rows, dtype=np.int64)
    element_ids = rng.integers(low=0, high=n_elements, size=n_rows, dtype=np.int64)
    df = pl.DataFrame({"set": set_ids, "element": element_ids})
    aggregated = (
        df.group_by("set").agg(pl.col("element").unique().sort()).sort("set")
    )
    sets = {}
    for row in aggregated.iter_rows(named=True):
        sets[int(row["set"])] = list(row["element"])
    return sets, df


def verify_cover(sets, cover):
    """Verify that the cover actually covers all elements."""
    covered = set()
    for set_name in cover:
        covered.update(sets[set_name])

    universe = set()
    for elements in sets.values():
        universe.update(elements)

    return covered == universe


def time_algo(name: str, sets: dict[int, list[int]]):
    start = time.time()
    res = setcover(sets, name)
    end = time.time()
    assert verify_cover(sets, res)
    print(name)
    print(f"Cover: {len(res)} sets")
    print(f"Time:  {end - start:.1f} seconds")


def parse_args():
    parser = argparse.ArgumentParser(description="Benchmark python bindings across algorithms.")
    parser.add_argument("--n-sets", type=int, default=100_000, help="Total number of candidate sets")
    parser.add_argument("--n-elements", type=int, default=2_000, help="Size of the universe")
    parser.add_argument("--n-rows", type=int, default=10_000_000, help="Number of (set, element) samples")
    parser.add_argument("--seed", type=int, default=333, help="Random seed for reproducible datasets")
    parser.add_argument(
        "--export-csv",
        type=str,
        default=None,
        help="Optional path to store the sampled long-form dataset (for the R benchmark).",
    )
    parser.add_argument(
        "--skip-bench",
        action="store_true",
        help="Generate the dataset (and optional CSV) but skip running the Python benchmarks.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    print(
        f"Generating data with n_sets={args.n_sets:,}, "
        f"n_elements={args.n_elements:,}, n_rows={args.n_rows:,}, seed={args.seed}"
    )
    sets, df = build_random_sets(args.n_sets, args.n_elements, args.n_rows, args.seed)

    if args.export_csv:
        out_path = Path(args.export_csv)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df.write_csv(out_path)
        print(f"Wrote dataset to {out_path}")

    if args.skip_bench:
        return

    des_len = 100
    print("-Results python" + "-" * (des_len - len("-Results python")))

    for algo in ("greedy-standard", "greedy-bitvec", "greedy-textbook"):
        time_algo(algo, sets)


if __name__ == "__main__":
    main()
