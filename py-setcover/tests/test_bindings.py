import pandas as pd
import polars as pl

from setcover import map_to_ints, setcover


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
    # TODO: CHECK that column "set_int" and "element_int" have range 0 to n-1 where n-1 is
    # the number of unique vaklues
    #


def _series_to_list(series):
    if hasattr(series, "tolist"):
        return series.tolist()
    if hasattr(series, "to_list"):
        return series.to_list()
    return list(series)


def test_set_cover_basic_dataframe():
    df = pd.DataFrame(
        {
            "set_name": ["A", "A", "B", "C"],
            "element": [1, 2, 2, 3],
        }
    )
    result = setcover(df, "set_name", "element")
    assert _series_to_list(result) == ["A", "C"]
    assert isinstance(result, pd.Series)


def test_set_cover_polars_dataframe():
    df = pl.DataFrame(
        {
            "bucket": ["X", "Y", "Z", "X"],
            "item": ["hat", "hat", "scarf", "glove"],
        }
    )
    result = setcover(df, "bucket", "item")
    assert _series_to_list(result) == ["X", "Z"]
    assert isinstance(result, pl.Series)


def test_set_cover_ignores_missing_rows():
    df = pd.DataFrame(
        {
            "bucket": ["north", "south", None, "west"],
            "element": [1, None, 2, 3],
        }
    )
    result = setcover(df, "bucket", "element")
    assert _series_to_list(result) == ["north", "west"]
