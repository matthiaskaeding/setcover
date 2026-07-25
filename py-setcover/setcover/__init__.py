from collections.abc import Iterable, Mapping
from itertools import accumulate
from typing import Any, NamedTuple

import narwhals as nw
from narwhals.typing import IntoFrame

from setcover._setcover_lib import greedy_set_cover_dense_py


class Step(NamedTuple):
    """One greedy selection, in the order the solver made it."""

    set: Any
    step: int
    n_new: int
    n_cum: int


def map_to_ints(df_native: IntoFrame, set_col: str, el_col: str) -> nw.DataFrame:
    """
    Map arbitrary set/element identifiers to contiguous integer IDs.

    The mapping is generated via dense ranking so that each unique value maps to
    a stable integer in the range [0, n-1].
    This will drop missing values and duplicate (set, element) pairs silently.
    Duplicates must go: the solver scores a candidate set by counting its
    elements, so a repeated pair would inflate that set's apparent gain.
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
        .unique([set_col, el_col])
        .select(
            sets.alias("set"),
            _dense_rank_expr(sets).alias("set_int"),
            _dense_rank_expr(elements).alias("element_int"),
        )
    )


def setcover(
    data: IntoFrame | Mapping[Any, Iterable[Any]],
    set_col: str | None = None,
    el_col: str | None = None,
    only_sets: bool = False,
):
    """
    Greedy set cover solver.

    Results come back in greedy selection order, highest-gain set first, so any
    prefix is itself a good partial cover: take the first k rows for the k sets
    that cover the most. `n_new` is each pick's marginal gain and `n_cum` the
    running total, which is where you look to decide where to truncate.

    - If `data` is a DataFrame-like (pandas/polars via Narwhals), provide
      `set_col` and `el_col`; returns a native DataFrame with columns
      `set`, `step`, `n_new`, `n_cum` in the same backend as the input.
    - If `data` is a mapping from set labels to iterables of elements,
      returns a list of `Step` named tuples (no DataFrame backend assumed).

    With `only_sets=True` you get just the chosen labels, still in selection
    order: a native Series for the DataFrame path, a list for the mapping path.
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
        picks = greedy_set_cover_dense_py(universe_size, sets)

        # dfl is sorted by set_int, and set_int is a dense rank, so row i of dfl
        # is the set the solver saw at index i.
        labels = dfl.get_column("set").to_list()
        n_new = [gain for _, gain in picks]
        solution = nw.DataFrame.from_dict(
            {
                "set": [labels[idx] for idx, _ in picks],
                "step": list(range(len(picks))),
                "n_new": n_new,
                "n_cum": list(accumulate(n_new)),
            },
            backend=df.implementation,
        )
        if only_sets:
            return solution.get_column("set").to_native()
        return solution.to_native()

    # Mapping path (set_label -> iterable of elements)
    if not isinstance(data, Mapping):
        raise TypeError(
            "Unsupported input: provide a DataFrame with set_col/el_col or a mapping of set->elements"
        )

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
    picks = greedy_set_cover_dense_py(universe_size, sets_int)
    if only_sets:
        return [labels[idx] for idx, _ in picks]

    cumulative = accumulate(gain for _, gain in picks)
    return [
        Step(set=labels[idx], step=step, n_new=gain, n_cum=n_cum)
        for step, ((idx, gain), n_cum) in enumerate(zip(picks, cumulative))
    ]


__all__ = ["Step", "map_to_ints", "setcover"]
