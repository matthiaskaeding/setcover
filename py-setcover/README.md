# Python bindings for setcover algorithms.

## DataFrame input via Narwhals

Install the optional dependency to enable dataframe support:

```bash
pip install "setcover[dataframe]"
```

Then pass a pandas/Polars dataframe (two columns: sets and elements) directly to
`setcover`, or call `sets_from_dataframe` to build the dictionary manually:

```python
import pandas as pd
from setcover import setcover

df = pd.DataFrame({"set": ["A", "A", "B"], "element": [1, 2, 3]})
cover = setcover(df, algo="greedy-standard", set_column="set", element_column="element")
```
