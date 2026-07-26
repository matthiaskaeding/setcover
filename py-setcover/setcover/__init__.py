from collections.abc import Iterable, Mapping
from itertools import accumulate
from typing import Any, Literal, NamedTuple

import narwhals as nw
from narwhals.typing import IntoFrame

from setcover._setcover_lib import (
    greedy_set_cover_dense_py,
    greedy_set_cover_dense_with_owner_py,
)


class Step(NamedTuple):
    """One greedy selection, in the order the solver made it."""

    set: Any
    step: int
    n_new: int
    n_cum: int


def map_to_ints(df_native: IntoFrame, set_col: str, el_col: str) -> nw.DataFrame:
    """
    Map arbitrary set/element identifiers to contiguous integer IDs.

    Returns the original labels alongside their ids — `set`, `set_int`,
    `element`, `element_int` — so callers can map results back.

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
            elements.alias("element"),
            _dense_rank_expr(elements).alias("element_int"),
        )
    )


def setcover(
    data: IntoFrame | Mapping[Any, Iterable[Any]],
    set_col: str | None = None,
    el_col: str | None = None,
    output: Literal["sets", "pairs"] = "sets",
):
    """
    Greedy set cover solver.

    Accepts either a DataFrame-like (pandas/polars via Narwhals) with `set_col`
    and `el_col`, or a mapping from set labels to iterables of elements. The
    mapping path assumes no DataFrame backend is installed.

    Results come back in greedy selection order, highest-gain set first, so any
    prefix is itself a good partial cover: take the first k rows for the k sets
    that cover the most.

    `output` selects the return shape:

    - `"sets"` (default) — one row per chosen set, with `step`, `n_new` (that
      pick's marginal gain) and `n_cum` (the running total, which is where you
      look to decide where to truncate). A native DataFrame in the input's
      backend, or a list of `Step` named tuples from a mapping. Take the `set`
      column if you only want the labels.
    - `"pairs"` — the cover expanded to one row per element, columns `set` and
      `element`, matching what `RcppGreedySetCover`'s `greedySetCover()`
      returns. Each element appears exactly once, attributed to whichever
      chosen set reached it first, so it is a partition of the universe rather
      than a join. A native DataFrame, or a list of tuples.
    """
    if output not in ("sets", "pairs"):
        raise ValueError(f"output must be 'sets' or 'pairs', got {output!r}")

    # Both column names or neither: one alone is always a mistake, and without
    # this check it falls through to the mapping path and reports the wrong
    # problem.
    if (set_col is None) != (el_col is None):
        given, missing = (
            ("set_col", "el_col") if el_col is None else ("el_col", "set_col")
        )
        raise ValueError(
            f"{given} was given without {missing}; pass both for a DataFrame, "
            "or neither for a mapping"
        )

    # DataFrame path
    if set_col is not None and el_col is not None:
        if isinstance(data, Mapping):
            raise TypeError(
                "set_col and el_col are for DataFrame input, but data is a "
                "mapping; drop them to solve the mapping directly"
            )
        if set_col == el_col:
            raise ValueError(
                f"set_col and el_col must name different columns, both are {set_col!r}"
            )

        available = list(nw.from_native(data, eager_only=True).columns)
        absent = [c for c in (set_col, el_col) if c not in available]
        if absent:
            raise ValueError(
                f"column(s) {absent} not found in data; available columns are {available}"
            )

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

        # An empty frame — no rows, or every row dropped as null — has no max.
        # pandas returns NaN and Polars returns None, and both blow up in the
        # binding rather than yielding an empty cover. The universe is empty, so
        # the solver has nothing to pick.
        if df.shape[0]:
            universe_size = int(df.get_column("element_int").max()) + 1
        else:
            universe_size = 0
        if output == "pairs":
            picks, owner = greedy_set_cover_dense_with_owner_py(universe_size, sets)
        else:
            picks = greedy_set_cover_dense_py(universe_size, sets)

        # dfl is sorted by set_int, and set_int is a dense rank, so row i of dfl
        # is the set the solver saw at index i.
        labels = dfl.get_column("set").to_list()

        if output == "pairs":
            # element_int is a dense rank, so sorting by it lines the labels up
            # with owner, which the solver indexed by element.
            el_labels = (
                df.unique(["element_int"])
                .sort("element_int")
                .get_column("element")
                .to_list()
            )
            step_of_set = {set_idx: step for step, (set_idx, _) in enumerate(picks)}
            order = sorted(
                range(universe_size), key=lambda e: (step_of_set[owner[e]], e)
            )
            return nw.DataFrame.from_dict(
                {
                    "set": [labels[owner[e]] for e in order],
                    "element": [el_labels[e] for e in order],
                },
                backend=df.implementation,
            ).to_native()

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
        return solution.to_native()

    # Mapping path (set_label -> iterable of elements)
    if not isinstance(data, Mapping):
        # A DataFrame reaching here means the caller forgot the column names.
        if hasattr(data, "columns"):
            raise TypeError(
                "data looks like a DataFrame; pass set_col and el_col to name "
                "the set and element columns"
            )
        raise TypeError(
            "data must be a DataFrame with set_col/el_col, or a mapping of "
            f"set -> elements; got {type(data).__name__}"
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

    if output == "pairs":
        picks, owner = greedy_set_cover_dense_with_owner_py(universe_size, sets_int)
        el_labels = list(elem_to_id)  # insertion order matches the assigned ids
        step_of_set = {set_idx: step for step, (set_idx, _) in enumerate(picks)}
        order = sorted(range(universe_size), key=lambda e: (step_of_set[owner[e]], e))
        return [(labels[owner[e]], el_labels[e]) for e in order]

    picks = greedy_set_cover_dense_py(universe_size, sets_int)

    cumulative = accumulate(gain for _, gain in picks)
    return [
        Step(set=labels[idx], step=step, n_new=gain, n_cum=n_cum)
        for step, ((idx, gain), n_cum) in enumerate(zip(picks, cumulative))
    ]


__all__ = ["Step", "setcover"]
