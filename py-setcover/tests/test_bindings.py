import pandas as pd
import polars as pl
from setcover import Step, map_to_ints, setcover


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


def _col(frame, name):
    return _series_to_list(frame[name])


def test_set_cover_basic_dataframe():
    df = pd.DataFrame(
        {
            "set_name": ["A", "A", "B", "C"],
            "element": [1, 2, 2, 3],
        }
    )
    result = setcover(df, "set_name", "element")

    assert isinstance(result, pd.DataFrame)
    assert list(result.columns) == ["set", "step", "n_new", "n_cum"]
    assert _col(result, "set") == ["A", "C"]
    assert _col(result, "step") == [0, 1]
    assert _col(result, "n_new") == [2, 1]
    assert _col(result, "n_cum") == [2, 3]


def test_set_cover_polars_dataframe():
    df = pl.DataFrame(
        {
            "bucket": ["X", "Y", "Z", "X"],
            "item": ["hat", "hat", "scarf", "glove"],
        }
    )
    result = setcover(df, "bucket", "item")

    assert isinstance(result, pl.DataFrame)
    assert _col(result, "set") == ["X", "Z"]
    assert _col(result, "n_new") == [2, 1]


def test_set_cover_only_sets_returns_native_series():
    df = pd.DataFrame({"set_name": ["A", "A", "B", "C"], "element": [1, 2, 2, 3]})
    result = setcover(df, "set_name", "element", only_sets=True)

    assert isinstance(result, pd.Series)
    assert _series_to_list(result) == ["A", "C"]


def test_set_cover_returns_greedy_order_not_sorted():
    # B is the best first pick (3 new elements), then C. Sorting alphabetically
    # would put A first, which is exactly the information we want preserved.
    df = pd.DataFrame(
        {
            "set_name": ["A", "A", "B", "B", "B", "C", "C"],
            "element": [10, 20, 10, 20, 30, 40, 50],
        }
    )
    result = setcover(df, "set_name", "element")

    assert _col(result, "set") == ["B", "C"]
    assert _col(result, "n_new") == [3, 2]
    assert _col(result, "n_cum") == [3, 5]


def test_n_cum_reaches_universe_size():
    df = pd.DataFrame(
        {
            "set_name": ["A", "A", "A", "B", "B", "B", "C", "C", "C"],
            "element": [1, 2, 3, 3, 4, 5, 5, 6, 7],
        }
    )
    result = setcover(df, "set_name", "element")

    assert _col(result, "n_cum")[-1] == df["element"].nunique()


def test_set_cover_ignores_missing_rows():
    df = pd.DataFrame(
        {
            "bucket": ["north", "south", None, "west"],
            "element": [1, None, 2, 3],
        }
    )
    result = setcover(df, "bucket", "element")
    assert sorted(_col(result, "set")) == ["north", "west"]


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

    assert _col(with_dups, "set") == ["B", "C"]
    assert _col(with_dups, "n_new") == [3, 2]
    assert _col(with_dups, "set") == _col(deduped, "set")


def test_set_cover_with_mapping_returns_steps():
    sets = {"A": [1, 2], "B": [2], "C": [3]}
    res = setcover(sets)

    assert res == [
        Step(set="A", step=0, n_new=2, n_cum=2),
        Step(set="C", step=1, n_new=1, n_cum=3),
    ]
    # Named tuples stay tuple-like, so a prefix is a partial cover.
    assert res[0].set == "A"
    assert [s.set for s in res[:1]] == ["A"]


def test_set_cover_with_mapping_only_sets_returns_labels():
    sets = {"A": [1, 2], "B": [2], "C": [3]}
    res = setcover(sets, only_sets=True)
    assert res == ["A", "C"]


def test_mapping_and_dataframe_paths_agree():
    sets = {"A": [10, 20], "B": [10, 20, 30], "C": [40, 50]}
    rows = [(label, el) for label, els in sets.items() for el in els]
    df = pd.DataFrame(rows, columns=["set_name", "element"])

    from_mapping = setcover(sets)
    from_frame = setcover(df, "set_name", "element")

    assert [s.set for s in from_mapping] == _col(from_frame, "set")
    assert [s.n_new for s in from_mapping] == _col(from_frame, "n_new")
    assert [s.n_cum for s in from_mapping] == _col(from_frame, "n_cum")
