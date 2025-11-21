# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "numpy",
#     "polars",
# ]
# ///
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import polars as pl


def build_random_dataframe(
    n_sets: int,
    n_elements: int,
    n_rows: int,
    seed: int,
) -> pl.DataFrame:
    rng = np.random.default_rng(seed)
    set_ids = rng.integers(low=0, high=n_sets, size=n_rows, dtype=np.int64)
    element_ids = rng.integers(low=0, high=n_elements, size=n_rows, dtype=np.int64)
    return pl.DataFrame({"set": set_ids, "element": element_ids})


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate synthetic set-cover data and write it to CSV."
    )
    parser.add_argument("--n-sets", type=int, default=100_000, help="Number of candidate sets")
    parser.add_argument("--n-elements", type=int, default=2_000, help="Size of the universe")
    parser.add_argument("--n-rows", type=int, default=10_000_000, help="Number of (set, element) rows")
    parser.add_argument("--seed", type=int, default=333, help="Random seed")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("scripts/benchmark/data.csv"),
        help="Destination CSV file",
    )
    parser.add_argument(
        "--force-new-data",
        action="store_true",
        help="Regenerate data even if parameters match the existing file.",
    )
    return parser.parse_args()


def compute_signature(args: argparse.Namespace) -> str:
    payload = {
        "n_sets": args.n_sets,
        "n_elements": args.n_elements,
        "n_rows": args.n_rows,
        "seed": args.seed,
    }
    raw = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def signature_path(output: Path) -> Path:
    return output.with_suffix(output.suffix + ".sig")


def cache_is_valid(output: Path, sig: str) -> bool:
    sig_file = signature_path(output)
    if not output.exists() or not sig_file.exists():
        return False
    try:
        existing = sig_file.read_text().strip()
    except OSError:
        return False
    return existing == sig


def main():
    args = parse_args()
    sig = compute_signature(args)
    sig_file = signature_path(args.output)

    if not args.force_new_data and cache_is_valid(args.output, sig):
        print(f"Dataset {args.output} already exists with matching parameters. Reusing.")
        return

    print(
        f"Generating data with n_sets={args.n_sets:,}, "
        f"n_elements={args.n_elements:,}, n_rows={args.n_rows:,}, seed={args.seed}"
    )
    df = build_random_dataframe(args.n_sets, args.n_elements, args.n_rows, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    df.write_csv(args.output)
    sig_file.write_text(sig)
    print(f"Wrote dataset to {args.output} (signature: {sig[:10]}...)")


if __name__ == "__main__":
    main()
