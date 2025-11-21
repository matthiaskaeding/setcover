# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "narwhals",
#     "polars",
# ]
# ///
import argparse
import sys
import time
from pathlib import Path

import polars as pl

REPO_ROOT = Path(__file__).resolve().parents[2]
PY_PACKAGE_DIR = REPO_ROOT / "py-setcover"
if str(PY_PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PY_PACKAGE_DIR))

from setcover import set_cover


def _series_to_list(series):
    if hasattr(series, "to_list"):
        return series.to_list()
    if hasattr(series, "tolist"):
        return series.tolist()
    return list(series)


def verify_cover(df: pl.DataFrame, cover_sets: list[str | int]) -> bool:
    """
    Ensure the chosen sets cover the entire universe of elements.
    """
    if not cover_sets:
        return df.height == 0
    chosen = df.filter(pl.col("set").is_in(cover_sets))
    covered = set(chosen["element"].to_list())
    universe = set(df["element"].to_list())
    return covered == universe


def parse_args():
    parser = argparse.ArgumentParser(
        description="Benchmark python bindings across algorithms."
    )
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
    df = pl.read_csv(args.data_csv)

    des_len = 100
    print("-Results python" + "-" * (des_len - len("-Results python")))

    start = time.time()
    cover_series = set_cover(df, "set", "element")
    end = time.time()
    cover = _series_to_list(cover_series)
    assert verify_cover(df, cover)
    print("set_cover (dense)")
    print(f"Cover: {len(cover)} sets")
    print(f"Time:  {end - start:.1f} seconds")


if __name__ == "__main__":
    main()
