# Python bindings for setcover

`setcover` exposes the high-performance Rust algorithms from `setcover-core`
through a thin Python API that works with familiar DataFrame libraries.

## Installation

```bash
pip install setcover
```

The wheel ships with the compiled Rust extension, so no separate toolchain is
required. For local development inside this repository, the `just pyinstall`
target runs `maturin develop` so the package can be imported directly.

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
        "set_name": ["A", "A", "B", "C"],
        "element": [1, 2, 2, 3],
    }
)

solution = setcover(df, set_col="set_name", el_col="element")
print(solution.tolist())  # -> ["A", "C"]
```

The return type mirrors the backend you passed in (pandas `Series` in the
example above, Polars `Series` if you provide a `pl.DataFrame`). Missing values
are automatically dropped before solving.

### Working with integer IDs

If you need access to the contiguous integer representation that the Rust core
expects, call `map_to_ints(df, set_col, el_col)`. It returns a Narwhals
DataFrame with three columns:

- `set`: original set identifiers
- `set_int`: dense integer IDs for each set
- `element_int`: dense integer IDs for each element

This helper is useful when you want to persist the mappings or call the lower
level `_setcover_lib.greedy_set_cover_*` functions directly.
