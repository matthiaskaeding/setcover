import narwhals as nw
from narwhals.typing import IntoFrame
from typing import Any, Iterable, Sequence, Union, Optional, Mapping

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


def setcover(
    data: Union[IntoFrame, Mapping[Any, Iterable[Any]], Sequence[Sequence[Any]]],
    set_col: Optional[str] = None,
    el_col: Optional[str] = None,
    only_sets: bool = False,
):
    """
    Greedy set cover solver.

    - If `data` is a DataFrame-like (pandas/polars via Narwhals), provide
      `set_col` and `el_col`; returns a native Series of chosen set labels.
    - If `data` is a mapping from set labels to iterables of elements,
      returns the chosen cover as a sub-dict by default. If `only_sets=True`,
      returns only the selected set labels in input order.
    - If `data` is a collection of collections (e.g., list of iterables),
      returns the chosen subsets themselves by default. If `only_sets=True`,
      returns the selected set indices (0-based).
    """
    # DataFrame path
    if set_col is not None and el_col is not None:
        df = map_to_ints(data, set_col, el_col).sort("set_int", "element_int")
        dfl = (
            df.group_by("set", "set_int")
            .agg(nw.col("element_int").len().alias("n"))
            .sort("set_int")
        )

        # Build sets as list of lists. We know element_int are dense integers without nulls
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

    # Mapping path (set_label -> iterable of elements)
    if isinstance(data, Mapping):
        elem_to_id: dict[Any, int] = {}
        labels: list[Any] = []
        sets_int: list[list[int]] = []
        for label, subset in data.items():
            if not isinstance(subset, Iterable) or isinstance(subset, (str, bytes)):
                raise TypeError("each mapping value must be an iterable of elements")
            labels.append(label)
            ids = []
            for el in subset:
                if el not in elem_to_id:
                    elem_to_id[el] = len(elem_to_id)
                ids.append(elem_to_id[el])
            # De-duplicate within a set while preserving insertion order
            deduped = list(dict.fromkeys(ids))
            sets_int.append(deduped)

        universe_size = len(elem_to_id)
        chosen = sorted(greedy_set_cover_dense_py(universe_size, sets_int))
        if only_sets:
            return [labels[i] for i in chosen]
        # Return sub-dict preserving input order of chosen labels
        return {labels[i]: data[labels[i]] for i in chosen}

    # Sequence-of-sequences path (no labels)
    if not isinstance(data, Iterable) or isinstance(data, (str, bytes)):
        raise TypeError(
            "Unsupported input: provide a DataFrame (set_col/el_col), a mapping of set->elements, or a collection of collections"
        )

    elem_to_id: dict[Any, int] = {}
    sets_int: list[list[int]] = []
    for subset in data:
        if not isinstance(subset, Iterable) or isinstance(subset, (str, bytes)):
            raise TypeError("each subset must be an iterable of elements")
        ids = []
        for el in subset:
            if el not in elem_to_id:
                elem_to_id[el] = len(elem_to_id)
            ids.append(elem_to_id[el])
        deduped = list(dict.fromkeys(ids))
        sets_int.append(deduped)

    universe_size = len(elem_to_id)
    chosen = sorted(greedy_set_cover_dense_py(universe_size, sets_int))
    if only_sets:
        return chosen
    return [data[i] for i in chosen]


__all__ = ["setcover"]
