from typing import Any, Dict, List, Tuple, TypeVar, overload
from ._setcover_lib import (
    greedy_set_cover_string_i64,
    greedy_set_cover_string_string,
    greedy_set_cover_i64_i64,
    greedy_set_cover_i64_string,
)

KeyT = TypeVar("KeyT", str, int)
ValueT = TypeVar("ValueT", str, int)


@overload
def setcover(sets: Dict[str, List[int]], algo: str = "greedy-bitvec") -> List[str]: ...


@overload
def setcover(sets: Dict[str, List[str]], algo: str = "greedy-bitvec") -> List[str]: ...


@overload
def setcover(sets: Dict[int, List[int]], algo: str = "greedy-bitvec") -> List[int]: ...


@overload
def setcover(sets: Dict[int, List[str]], algo: str = "greedy-bitvec") -> List[int]: ...


def setcover(
    sets: Dict[KeyT, List[ValueT]] | Any,
    algo: str = "greedy-standard",
    *,
    set_column: str | None = None,
    element_column: str | None = None,
) -> List[KeyT]:
    """
    Finds an approximate solution to the set cover problem.

    This is a user-friendly Python wrapper around the core Rust implementation.

    Args:
        sets: Either a dictionary mapping keys to lists of elements, or a two-column
              dataframe (pandas, Polars, etc.) that will be adapted via narwhals.
              When a dataframe is provided, `set_column` and `element_column` identify
              the relevant columns (defaulting to the first two).
        algo: The algorithm to use.
              greedy-bitvec for BitVec-based implementation (faster for most cases)
              greedy-standard for HashSet-based implementation.
              greedy-textbook for a straightforward greedy loop with no optimizations.
              Defaults to greedy-standard.
        set_column: Optional name of the column containing set identifiers when a
              dataframe input is supplied. Defaults to the dataframe's first column.
        element_column: Optional name of the column containing elements when a
              dataframe input is supplied. Defaults to the dataframe's second column.

    Returns:
        A sorted list containing the keys of the chosen sets that form the cover.
        The type of the returned set matches the type of the input dictionary keys.

    Raises:
        TypeError: If the input is not a dictionary, or if keys/values are not of supported types.
        ValueError: If no non-empty lists are provided, or if an invalid algorithm is specified.
    """
    if algo not in ("greedy-bitvec", "greedy-standard", "greedy-textbook"):
        msg = f"""<algo> must be in ("greedy-bitvec", "greedy-standard", "greedy-textbook") but is {algo}"""
        raise ValueError(msg)
    normalized_sets = _ensure_mapping(
        sets, set_column=set_column, element_column=element_column
    )
    sample_key, sample_value = _validate_mapping(normalized_sets)

    # Choose the appropriate function based on key and value types
    match (isinstance(sample_key, str), isinstance(sample_value, str)):
        case (True, True):
            func = greedy_set_cover_string_string
        case (True, False):
            func = greedy_set_cover_string_i64
        case (False, True):
            func = greedy_set_cover_i64_string
        case (False, False):
            func = greedy_set_cover_i64_i64

    return func(normalized_sets, algo)


def sets_from_dataframe(
    dataframe: Any, *, set_column: str | None = None, element_column: str | None = None
) -> Dict[Any, List[Any]]:
    """
    Convert a pandas/Polars dataframe into the dictionary input expected by `setcover`.

    Args:
        dataframe: Two-column dataframe (in-memory) supported by narwhals.
        set_column: Optional column containing the set identifiers.
        element_column: Optional column containing the elements.

    Returns:
        A dictionary mapping each set identifier to a list of elements.
    """
    return _dataframe_to_sets(
        dataframe, set_column=set_column, element_column=element_column
    )


def _ensure_mapping(
    sets: Dict[KeyT, List[ValueT]] | Any,
    *,
    set_column: str | None,
    element_column: str | None,
) -> Dict[KeyT, List[ValueT]]:
    if isinstance(sets, dict):
        return sets
    if not _is_dataframe_like(sets):
        raise TypeError("sets must be a dictionary or dataframe.")
    return _dataframe_to_sets(
        sets,
        set_column=set_column,
        element_column=element_column,
    )


def _dataframe_to_sets(
    dataframe: Any, *, set_column: str | None, element_column: str | None
) -> Dict[Any, List[Any]]:
    try:
        import narwhals as nw
    except ImportError as exc:
        raise ImportError(
            "DataFrame input requires optional dependency 'narwhals'. "
            "Install via `pip install narwhals` or `pip install setcover[dataframe]`."
        ) from exc

    table = nw.from_native(dataframe)
    columns = list(table.columns)
    if len(columns) < 2:
        raise ValueError("DataFrame input must contain at least two columns.")
    set_col = set_column or columns[0]
    elem_col = element_column or columns[1]
    if set_col == elem_col:
        raise ValueError(
            "set_column and element_column must reference different columns."
        )
    if set_col not in columns:
        raise ValueError(f"{set_col!r} is not a column in the provided dataframe.")
    if elem_col not in columns:
        raise ValueError(f"{elem_col!r} is not a column in the provided dataframe.")

    normalized: Dict[Any, List[Any]] = {}
    for row in table.iter_rows(named=True):
        key = _python_scalar(row[set_col])
        value = _python_scalar(row[elem_col])
        normalized.setdefault(key, []).append(value)

    if not normalized:
        raise ValueError("DataFrame input must contain at least one element.")
    return normalized


def _python_scalar(value: Any) -> Any:
    if hasattr(value, "to_python"):
        try:
            return value.to_python()
        except Exception:
            pass
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    return value


def _validate_mapping(sets: Dict[Any, List[Any]]) -> Tuple[Any, Any]:
    if not isinstance(sets, dict):
        raise TypeError("sets must be a dictionary or dataframe.")

    sample_values = next((v for v in sets.values() if v), None)
    if sample_values is None:
        raise ValueError("at least one non-empty list is required")

    sample_key = next(iter(sets.keys()))
    if not isinstance(sample_key, (str, int)):
        raise TypeError("dictionary keys must be either strings or integers")

    sample_value = sample_values[0]
    if not isinstance(sample_value, (int, str)):
        raise TypeError(
            f"unsupported value type: {type(sample_value)}. Only integers and strings are supported."
        )
    return sample_key, sample_value


def _is_dataframe_like(candidate: Any) -> bool:
    if candidate is None:
        return False
    if hasattr(candidate, "__dataframe__"):
        return True
    if hasattr(candidate, "schema"):
        return True
    columns = getattr(candidate, "columns", None)
    return columns is not None


__all__ = [
    "setcover",
    "sets_from_dataframe",
]
