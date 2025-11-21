import narwhals as nw
from narwhals.typing import IntoFrame


def map_to_ints(df_native: IntoFrame, set_col: str, el_col: str) -> nw.DataFrame:
    """
    Map arbitrary set/element identifiers to contiguous integer IDs.

    The mapping is generated via dense ranking so that each unique value maps to
    a stable integer in the range [0, n).
    """
    df = nw.from_native(df_native, eager_only=True)
    sets = nw.col(set_col)
    elements = nw.col(el_col)

    def _dense_rank_expr(expr: nw.Expr):
        ranked = expr.rank(method="dense") - 1
        return ranked.cast(nw.Int64)

    return df.select(
        sets.alias("set"),
        _dense_rank_expr(sets).alias("set_int"),
        _dense_rank_expr(elements).alias("element_int"),
    )


__all__ = ["map_to_ints"]
