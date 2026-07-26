# Python bindings for setcover

`setcover` exposes the high-performance Rust solver from `setcover-core`
through a thin Python API that works with familiar DataFrame libraries.

## Installation

```bash
pip install setcover
```

The wheel ships with the compiled Rust extension, so no separate toolchain is
required. For local development inside this repository, `make pyinstall` runs
`maturin develop` so the package can be imported directly.

## DataFrame-first API

The public entrypoints live in `setcover/__init__.py` and use
[Narwhals](https://narwhals.dev/) to accept either pandas or Polars frames.
Install whichever backend you prefer (or both) and pass a table where one
column identifies the set name and another column contains the elements that it
covers:

```python
import pandas as pd
from setcover import setcover

df = pd.DataFrame(
    {
        "set": ["A", "A", "B", "B", "B", "C", "C"],
        "element": [10, 20, 10, 20, 30, 40, 50],
    }
)

setcover(df, "set", "element")
#   set  step  n_new  n_cum
# 0   B     0      3      3
# 1   C     1      2      5
```

Results come back **in greedy selection order**, highest-gain set first. That
ordering is the point: greedy set cover builds its answer as a sequence, so any
prefix is itself a good partial cover. The first `k` rows are the `k` sets that
cover the most.

| column  | meaning                                          |
| ------- | ------------------------------------------------ |
| `set`   | the chosen set label                             |
| `step`  | selection order, starting at 0                   |
| `n_new` | elements this pick was the first to cover        |
| `n_cum` | running total, reaching the universe size at the end |

`n_new` is the marginal gain, which is where you look to decide where to
truncate — once it flattens, further sets are buying you little.

The return type mirrors the backend you passed in (pandas `DataFrame` above,
Polars `DataFrame` if you provide a `pl.DataFrame`). Missing values and
duplicate `(set, element)` pairs are dropped before solving.

If you only want the labels, `output="labels"` returns a native Series, still in
selection order:

```python
setcover(df, "set", "element", output="labels")
# 0    B
# 1    C
```

## Expanding the cover

`output="pairs"` returns one row per element instead — the cover joined back to the
elements it covers, matching what `RcppGreedySetCover`'s `greedySetCover()`
returns:

```python
setcover(df, "set", "element", output="pairs")
#   set  element
# 0   B       10
# 1   B       20
# 2   B       30
# 3   C       40
# 4   C       50
```

Each element appears exactly once, attributed to whichever chosen set reached
it first — a partition of the universe, not a join. Rows stay in selection
order, so the first set's elements come first.

## Mapping input (labels → elements)

`setcover` can also solve directly from a mapping of set labels to their
elements. This is handy when your data isn't in tabular form, and it needs no
DataFrame backend installed at all:

```python
from setcover import setcover

sets = {"A": [1, 2], "B": [2], "C": [3]}

setcover(sets)
# [Step(set='A', step=0, n_new=2, n_cum=2),
#  Step(set='C', step=1, n_new=1, n_cum=3)]

setcover(sets, output="labels")
# ['A', 'C']
```

`Step` is a `NamedTuple`, so results stay tuple-like and sliceable —
`result[:10]` is the ten highest-gain sets.

Notes
- Duplicate elements within a set are ignored for correctness and speed.
- When using DataFrames, pass column names via `set_col` and `el_col`.
- To recover the old sorted-labels behaviour, sort the `set` column yourself.
