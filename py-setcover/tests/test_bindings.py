import pandas as pd

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
    # TODO: CHECK that column "set_int" and "element_int" have range 0 to n-1 where n-1 is
    # the number of unique vaklues
    #
