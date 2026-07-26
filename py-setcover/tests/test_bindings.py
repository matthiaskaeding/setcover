import pandas as pd
import polars as pl
import pytest
from setcover import Step, map_to_ints, setcover


def test_map_to_ints_dense_ids_with_pandas():
    df = pd.DataFrame(
        {
            "set_name": ["alpha", "beta", "alpha", "gamma"],
            "element": ["foo", "foo", "bar", "baz"],
        }
    )

    result = map_to_ints(df, "set_name", "element").to_native()
    assert list(result.columns) == ["set", "set_int", "element", "element_int"]

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


def test_empty_dataframe_returns_empty_result():
    # An empty frame has no max element_int: pandas gives NaN, Polars gives
    # None, and both used to reach the binding and raise TypeError.
    for empty in (pd.DataFrame({"s": [], "e": []}), pl.DataFrame({"s": [], "e": []})):
        result = setcover(empty, "s", "e")
        assert result.shape[0] == 0
        assert list(result.columns) == ["set", "step", "n_new", "n_cum"]


def test_all_null_rows_are_treated_as_empty():
    df = pd.DataFrame({"s": [None, None], "e": [None, None]})
    result = setcover(df, "s", "e")

    assert result.shape[0] == 0
    assert list(result.columns) == ["set", "step", "n_new", "n_cum"]


def test_empty_mapping_returns_no_picks():
    assert setcover({}) == []


def test_mapping_of_only_empty_sets_returns_no_picks():
    assert setcover({"A": [], "B": []}) == []


def test_mapping_skips_empty_sets():
    res = setcover({"A": [], "B": [1]})

    assert [s.set for s in res] == ["B"]
    assert res[0].n_new == 1


def test_pairs_expands_the_cover_to_one_row_per_element():
    df = pd.DataFrame(
        {
            "set_name": ["A", "A", "B", "B", "B", "C", "C"],
            "element": [10, 20, 10, 20, 30, 40, 50],
        }
    )
    result = setcover(df, "set_name", "element", output="pairs")

    assert list(result.columns) == ["set", "element"]
    assert _col(result, "set") == ["B", "B", "B", "C", "C"]
    assert _col(result, "element") == [10, 20, 30, 40, 50]


def test_pairs_partitions_the_universe():
    # Every element exactly once, attributed to whichever chosen set reached it
    # first -- a partition, not a join. 20 is in both A and B but appears once.
    df = pd.DataFrame(
        {
            "set_name": ["A", "A", "B", "B", "B", "C", "C"],
            "element": [10, 20, 10, 20, 30, 40, 50],
        }
    )
    result = setcover(df, "set_name", "element", output="pairs")
    elements = _col(result, "element")

    assert sorted(elements) == sorted(df["element"].unique())
    assert len(elements) == len(set(elements))

    # Every emitted pair must actually exist in the input.
    real = set(map(tuple, df.drop_duplicates().to_numpy()))
    assert all((s, e) in real for s, e in zip(_col(result, "set"), elements))


def test_pairs_agrees_with_the_picks_table():
    df = pd.DataFrame(
        {
            "set_name": ["A", "A", "A", "B", "B", "B", "C", "C", "C"],
            "element": [1, 2, 3, 3, 4, 5, 5, 6, 7],
        }
    )
    picks = setcover(df, "set_name", "element")
    prs = setcover(df, "set_name", "element", output="pairs")

    # Same sets, same order, and each set owns exactly n_new elements.
    assert _col(prs, "set")[:1] == _col(picks, "set")[:1]
    counts = pd.Series(_col(prs, "set")).value_counts()
    for label, n_new in zip(_col(picks, "set"), _col(picks, "n_new")):
        assert counts[label] == n_new


def test_pairs_on_polars_and_empty_input():
    result = setcover(
        pl.DataFrame({"s": ["A", "A", "B"], "e": [1, 2, 2]}), "s", "e", output="pairs"
    )
    assert isinstance(result, pl.DataFrame)
    assert _col(result, "set") == ["A", "A"]

    empty = setcover(pd.DataFrame({"s": [], "e": []}), "s", "e", output="pairs")
    assert empty.shape[0] == 0
    assert list(empty.columns) == ["set", "element"]


def test_pairs_from_a_mapping():
    res = setcover({"A": [10, 20], "B": [10, 20, 30], "C": [40, 50]}, output="pairs")
    assert res == [("B", 10), ("B", 20), ("B", 30), ("C", 40), ("C", 50)]


def test_unknown_output_mode_is_rejected():
    with pytest.raises(ValueError, match="output must be"):
        setcover({"A": [1]}, output="labels")


def test_mapping_and_dataframe_paths_agree():
    sets = {"A": [10, 20], "B": [10, 20, 30], "C": [40, 50]}
    rows = [(label, el) for label, els in sets.items() for el in els]
    df = pd.DataFrame(rows, columns=["set_name", "element"])

    from_mapping = setcover(sets)
    from_frame = setcover(df, "set_name", "element")

    assert [s.set for s in from_mapping] == _col(from_frame, "set")
    assert [s.n_new for s in from_mapping] == _col(from_frame, "n_new")
    assert [s.n_cum for s in from_mapping] == _col(from_frame, "n_cum")


def test_one_column_name_without_the_other_is_rejected():
    df = pd.DataFrame({"s": ["A"], "e": [1]})

    with pytest.raises(ValueError, match="set_col was given without el_col"):
        setcover(df, "s")
    with pytest.raises(ValueError, match="el_col was given without set_col"):
        setcover(df, el_col="e")


def test_missing_columns_are_named_alongside_what_is_available():
    df = pd.DataFrame({"s": ["A"], "e": [1]})

    with pytest.raises(ValueError, match=r"\['nope'\] not found"):
        setcover(df, "nope", "e")
    with pytest.raises(ValueError, match=r"available columns are \['s', 'e'\]"):
        setcover(df, "s", "nope")


def test_the_same_column_for_sets_and_elements_is_rejected():
    df = pd.DataFrame({"s": ["A"], "e": [1]})

    with pytest.raises(ValueError, match="must name different columns"):
        setcover(df, "s", "s")


def test_column_names_with_a_mapping_are_rejected():
    with pytest.raises(TypeError, match="but data is a mapping"):
        setcover({"A": [1, 2]}, "s", "e")


def test_a_dataframe_without_column_names_says_so():
    df = pd.DataFrame({"s": ["A"], "e": [1]})

    with pytest.raises(TypeError, match="pass set_col and el_col"):
        setcover(df)


def test_a_wholly_wrong_type_is_rejected():
    with pytest.raises(TypeError, match="got list"):
        setcover([("A", 1), ("A", 2)])


def test_mapping_values_must_be_iterables_of_elements():
    with pytest.raises(TypeError, match="iterable of elements"):
        setcover({"A": 1})
    # A string is iterable but almost never what the caller meant.
    with pytest.raises(TypeError, match="iterable of elements"):
        setcover({"A": "abc"})
