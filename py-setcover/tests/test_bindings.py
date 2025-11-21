from numbers import Integral

import narwhals as nw
import pandas as pd
import pytest

from setcover import map_to_ints


def test_map_to_ints_dense_ids_with_pandas():
    df = pd.DataFrame(
        {
            "set_name": ["alpha", "beta", "alpha", "gamma"],
            "element": ["foo", "foo", "bar", "baz"],
        }
    )

    result = map_to_ints(df, "set_name", "element").to_native()

    assert result.shape[1] == 3
    assert list(result.columns) == ["set", "set_int", "element_int"]
