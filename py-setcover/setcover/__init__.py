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


def setcover(df_native: IntoFrame, set_col: str, el_col: str) -> nw.Series:
    """
    Find set cover
    """
    df = map_to_ints(df_native, set_col, el_col).sort("set_int", "element_int")
    dfl = (
        df.group_by("set", "set_int")
        .agg(nw.col("element_int").len().alias("n"))
        .sort("set_int")
    )

    # Built sets as list of lists. We know element_int are dense integers without nulls
    sets = []
    start = 0
    elements_int = df.get_column("element_int").to_list()
    for n in dfl.get_column("n"):
        sets.append(elements_int[start : start + n])
        start += n

    universe_size = df.get_column("element_int").max() + 1
    chosen_sets = greedy_set_cover_dense_py(universe_size, sets)

    # Map back
    lu = nw.DataFrame.from_dict(
        {"set_int": chosen_sets},
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


__all__ = ["setcover"]
