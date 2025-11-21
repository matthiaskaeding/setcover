from numbers import Integral

import pandas as pd
import polars as pl

from setcover import map_to_ints


def _series_values(frame, column):
    series = frame[column]
    if hasattr(series, "to_list"):
        return series.to_list()
    if hasattr(series, "tolist"):
        return series.tolist()
    return list(series)


def _assert_dense(values):
    assert values, "expected at least one value"
    assert min(values) == 0
    unique = sorted(set(values))
    assert unique == list(range(len(unique)))
    assert all(isinstance(value, Integral) for value in values)


def _assert_consistent_mapping(labels, ids):
    mapping = {}
    for label, idx in zip(labels, ids):
        previous = mapping.setdefault(label, idx)
        assert previous == idx


def test_map_to_ints_dense_ids_with_pandas():
    df = pd.DataFrame(
        {
            "set_name": ["alpha", "beta", "alpha", "gamma"],
            "element": ["foo", "foo", "bar", "baz"],
        }
    )

    expected_set_count = df["set_name"].nunique()
    expected_element_count = df["element"].nunique()

    result = map_to_ints(df, "set_name", "element").to_native()
    assert result.shape[1] == 3
    assert list(result.columns) == ["set", "set_int", "element_int"]

    set_labels = _series_values(result, "set")
    set_ids = _series_values(result, "set_int")
    element_ids = _series_values(result, "element_int")

    _assert_dense(set_ids)
    _assert_dense(element_ids)
    assert len(set(set_ids)) == expected_set_count
    assert len(set(element_ids)) == expected_element_count
    _assert_consistent_mapping(set_labels, set_ids)


def test_map_to_ints_dense_ids_with_polars():
    df = pl.DataFrame(
        {
            "set_name": [10, 10, 42, -7, -7],
            "element": ["apple", "banana", "apple", "banana", "banana"],
        }
    )

    expected_set_count = df["set_name"].n_unique()
    expected_element_count = df["element"].n_unique()

    result = map_to_ints(df, "set_name", "element").to_native()
    assert set(result.columns) == {"set", "set_int", "element_int"}

    set_labels = _series_values(result, "set")
    set_ids = _series_values(result, "set_int")
    element_ids = _series_values(result, "element_int")

    _assert_dense(set_ids)
    _assert_dense(element_ids)
    assert len(set(set_ids)) == expected_set_count
    assert len(set(element_ids)) == expected_element_count
    _assert_consistent_mapping(set_labels, set_ids)


def test_map_to_ints_handles_numeric_sets_with_pandas():
    df = pd.DataFrame(
        {
            "set_name": [1.5, 1.5, 2.75, -3.0],
            "element": [10, 20, 10, 40],
        }
    )

    expected_set_count = df["set_name"].nunique()
    expected_element_count = df["element"].nunique()

    result = map_to_ints(df, "set_name", "element").to_native()
    assert list(result.columns) == ["set", "set_int", "element_int"]

    set_labels = _series_values(result, "set")
    set_ids = _series_values(result, "set_int")
    element_ids = _series_values(result, "element_int")

    _assert_dense(set_ids)
    _assert_dense(element_ids)
    assert len(set(set_ids)) == expected_set_count
    assert len(set(element_ids)) == expected_element_count
    _assert_consistent_mapping(set_labels, set_ids)


def test_map_to_ints_handles_string_sets_float_elements_polars():
    df = pl.DataFrame(
        {
            "set_name": ["north", "south", "north", "east"],
            "element": [0.1, 0.2, 0.3, 0.1],
        }
    )

    expected_set_count = df["set_name"].n_unique()
    expected_element_count = df["element"].n_unique()

    result = map_to_ints(df, "set_name", "element").to_native()
    assert set(result.columns) == {"set", "set_int", "element_int"}

    set_labels = _series_values(result, "set")
    set_ids = _series_values(result, "set_int")
    element_ids = _series_values(result, "element_int")

    _assert_dense(set_ids)
    _assert_dense(element_ids)
    assert len(set(set_ids)) == expected_set_count
    assert len(set(element_ids)) == expected_element_count
    _assert_consistent_mapping(set_labels, set_ids)


def test_map_to_ints_drops_missing_rows():
    df = pd.DataFrame(
        {
            "set_name": ["north", None, "south", "east"],
            "element": [1.0, 2.0, None, 3.0],
        }
    )

    result = map_to_ints(df, "set_name", "element").to_native()
    assert len(result) == 2
    assert set(result["set"]) == {"north", "east"}
