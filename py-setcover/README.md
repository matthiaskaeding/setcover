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
        "set": ["A", "A", "B", "C"],
        "element": [1, 2, 2, 3],
    }
)

solution = setcover(df, "set", "element")
print(solution)  # -> ["A", "C"]
```

The return type mirrors the backend you passed in (pandas `Series` in the
example above, Polars `Series` if you provide a `pl.DataFrame`). Missing values
are automatically dropped before solving.
