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

    # Both id columns must be dense: exactly 0..n-1 for n unique input values.
    assert set(result["set_int"]) == set(range(df["set_name"].nunique()))
    assert set(result["element_int"]) == set(range(df["element"].nunique()))


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


def test_map_to_ints_drops_duplicate_pairs():
    df = pd.DataFrame(
        {
            "set_name": ["A", "A", "A", "B"],
            "element": ["x", "x", "y", "x"],
        }
    )
    result = map_to_ints(df, "set_name", "element").to_native()
    assert result.shape[0] == 3


def test_set_cover_unaffected_by_duplicate_rows():
    # A covers {1,2}, B covers {1,2,3}, C covers {4,5}. Greedy should take B
    # then C. Repeating the (A,1) row must not inflate A's apparent gain to 4
    # and pull it into the cover.
    rows = {
        "set_name": ["A", "A", "A", "A", "B", "B", "B", "C", "C"],
        "element": [1, 1, 1, 2, 1, 2, 3, 4, 5],
    }
    with_dups = setcover(pd.DataFrame(rows), "set_name", "element")
    deduped = setcover(pd.DataFrame(rows).drop_duplicates(), "set_name", "element")

    assert _series_to_list(with_dups) == ["B", "C"]
    assert _series_to_list(with_dups) == _series_to_list(deduped)


def test_set_cover_with_mapping_returns_cover_subdict():
    # Cover {1,2,3} with labeled sets
    sets = {"A": [1, 2], "B": [2], "C": [3]}
    res = setcover(sets)
    assert isinstance(res, dict)
    assert list(res.keys()) == ["A", "C"]
    assert res == {"A": [1, 2], "C": [3]}


def test_set_cover_with_mapping_only_sets_returns_labels():
    sets = {"A": [1, 2], "B": [2], "C": [3]}
    res = setcover(sets, only_sets=True)
    assert res == ["A", "C"]


# setcover_pairs was intentionally removed; API remains label-only.
