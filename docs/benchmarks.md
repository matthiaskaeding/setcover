# Benchmarks

How the Rust core compares against the C++ implementation in
`RcppGreedySetCover` 0.1.1.

> **This comparison has a shelf life.** It measures two *independent*
> implementations. If the R package is ported onto the Rust core (#35), both
> sides would run the same engine and these numbers stop meaning anything.
> Treat this file as describing a specific pair of implementations at a
> specific time, not a durable property of the project.

## Results

Reproduce with `make bench_alot`. Each scenario generates a random long-form
dataset with a fixed seed, then times the solve only — CSV loading is excluded.

Times are seconds, lower is better.

| n_sets  | universe | rows | seed | Python `setcover` | R `setcover` | speedup | cover size (Py / R) |
| ------- | -------- | ---- | ---- | ----------------- | ------------ | ------- | ------------------- |
| 150,000 | 2,000    | 12M  | 111  | 8.8               | 32.6         | 3.7×    | 47 / 47             |
| 40,000  | 8,000    | 9M   | 222  | 4.7               | 18.4         | 3.9×    | 100 / 99            |
| 80,000  | 4,000    | 10M  | 333  | 5.8               | 24.6         | 4.2×    | 72 / 72             |

Measured on an Intel Xeon @ 2.10GHz (4 vCPU), 15 GB RAM, Ubuntu 24.04, with
rustc 1.97.1 (release profile), Python 3.11.15 / polars 1.35.2 / narwhals
2.12.0, and R 4.3.3 / data.table 1.14.10. A 4 vCPU container is not a quiet
benchmarking machine; treat the ratio as reliable and the absolute times as
indicative.

## What is actually being compared

**Two independent implementations, not two bindings over one core.**
`setcover-core` (Rust) backs only the Python package; the R package runs its own
C++ implementation built on boost multi_index. Both solve the same problem with
the same greedy rule, but they share no code, so this ratio moves whenever
either side changes.

Both columns time the like-for-like entry point: one row per chosen set. The R
package's other function, `greedySetCover()`, returns one row per *element*;
timed separately it comes in at 31.9 / 18.8 / 24.1 seconds — within noise of R's
`setcover()`.

That the two R functions cost the same is worth understanding, because it
qualifies the headline number. `greedy_set_cover2` preallocates one output row
per element and fills every one of them, whatever wrapper called it; R's
`setcover()` just collapses that with `rle()` afterwards. So the C++ engine
always materializes the full element-to-set assignment, while the Rust dense
solver never does.

**The gap comes from design decisions, not from the choice of language.** Both
sides are compiled native code, and nothing measured here is faster in Rust
than the same approach would be in C++. Two design differences account for it:

* **Output contract.** The C++ always materializes the full element-to-set
  assignment, even when the caller only wants labels. The Rust path never
  builds it.
* **Representation.** The C++ maintains a `boost::multi_index` of set sizes
  over `unordered_set` members, so each round chases pointers and hashes
  elements individually. The dense Rust solver scans flat `Vec`s against a
  `bool` array — cache-friendly, though it rescans every candidate each round
  rather than updating incrementally.

So read the table as "the R package is ~4× slower for the same task", not "Rust
is ~4× faster than C++". A labels-only path in the C++, or a lazy priority
queue on either side, would move this number considerably more than the
language does. These runs are not profiled, so how the gap splits between the
two causes above is unquantified.

## Tie-breaking

The two implementations break ties differently — Rust takes the first set with
the maximal gain, while boost's `ordered_non_unique` index picks an arbitrary
one among equals. Both answers are valid greedy covers, but they need not be
identical, which is why scenario 2 above lands on 100 sets versus 99. Do not
assert equal output across the two.

## Running them yourself

```bash
make bench_alot                       # the three scenarios above
make bench N_SETS=... N_ELEMENTS=... N_ROWS=... SEED=...
```

See `scripts/benchmark/README.md` for the individual steps.
