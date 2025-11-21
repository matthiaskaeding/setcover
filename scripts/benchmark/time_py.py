# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "polars",
# ]
# ///
import argparse
from pathlib import Path
import sys
import time

import polars as pl

REPO_ROOT = Path(__file__).resolve().parents[2]
PY_PACKAGE_DIR = REPO_ROOT / "py-setcover"
if str(PY_PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PY_PACKAGE_DIR))

from setcover import setcover


def load_sets_from_csv(path: Path) -> dict[int, list[int]]:
    df = pl.read_csv(path)
    grouped = (
        df.group_by("set")
        .agg(pl.col("element").unique().sort())
        .sort("set")
    )
    sets = {}
    for row in grouped.iter_rows(named=True):
        sets[int(row["set"])] = list(row["element"])
    return sets


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
    parser.add_argument(
        "--data-csv",
        type=Path,
        default=Path("scripts/benchmark/data.csv"),
        help="CSV file containing the long-form dataset.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    print(f"Reading data from {args.data_csv}")
    sets = load_sets_from_csv(args.data_csv)

    des_len = 100
    print("-Results python" + "-" * (des_len - len("-Results python")))

    for algo in ("greedy-standard", "greedy-bitvec", "greedy-textbook"):
        time_algo(algo, sets)


if __name__ == "__main__":
    main()
