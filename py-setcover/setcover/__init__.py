import narwhals as nw
from narwhals.typing import IntoFrame

from setcover._setcover_lib import greedy_set_cover_dense_py


def map_to_ints(df_native: IntoFrame, set_col: str, el_col: str) -> nw.DataFrame:
    """
    Map arbitrary set/element identifiers to contiguous integer IDs.

    The mapping is generated via dense ranking so that each unique value maps to
    a stable integer in the range [0, n-1].
    This will drop missing values silently.
    """
    df = nw.from_native(df_native, eager_only=True)
    sets = nw.col(set_col)
    elements = nw.col(el_col)

    def _dense_rank_expr(expr: nw.Expr):
        ranked = expr.rank(method="dense") - 1
        return ranked.cast(nw.Int64)

    return (
        df.select(set_col, el_col)
        .drop_nulls()
        .select(
            sets.alias("set"),
            _dense_rank_expr(sets).alias("set_int"),
            _dense_rank_expr(elements).alias("element_int"),
        )
    )


def set_cover(df_native: IntoFrame, set_col: str, el_col: str):
    df = map_to_ints(df_native, set_col, el_col)
    dfl = df.group_by("set", "set_int").agg(nw.col("element_int").list())
    sets = dfl.get_column("element_int").to_list()
    universe_size = df.get_column("element_int").max() + 1
    sets = greedy_set_cover_dense_py(universe_size, sets)  # TODO: add import

    lu = nw.DataFrame.from_dict(
        {"set_int": sets},
        backend=df.implementation,
    )

    solution = (
        dfl.select("set", "set_int")
        .join(lu, ["set_int"], "inner")
        .get_column("set")
        .sort()
        .to_native()
    )

    return solution


__all__ = ["map_to_ints"]
