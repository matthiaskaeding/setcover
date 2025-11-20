from typing import Dict, List, TypeVar, overload
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
    sets: Dict[KeyT, List[ValueT]], algo: str = "greedy-standard"
) -> List[KeyT]:
    """
    Finds an approximate solution to the set cover problem.

    This is a user-friendly Python wrapper around the core Rust implementation.

    Args:
        sets: A dictionary of lists. Keys can be strings or integers.
              Values can be strings or integers.
        algo: The algorithm to use.
              greedy-bitvec for BitVec-based implementation (faster for most cases)
              greedy-standard for HashSet-based implementation.
              greedy-textbook for a straightforward greedy loop with no optimizations.
              Defaults to greedy-standard.

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
    # Validate input
    if not isinstance(sets, dict):
        raise TypeError("sets must be a dictionary")

    # Get the first non-empty list to determine value type
    sample_values = next((v for v in sets.values() if v), None)
    if sample_values is None:
        raise ValueError("at least one non-empty list is required")

    # Get a sample key to determine key type
    sample_key = next(iter(sets.keys()))
    if not isinstance(sample_key, (str, int)):
        raise TypeError("dictionary keys must be either strings or integers")

    # Determine value type
    sample_value = sample_values[0]
    if not isinstance(sample_value, (int, str)):
        raise TypeError(
            f"unsupported value type: {type(sample_value)}. Only integers and strings are supported."
        )

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

    return func(sets, algo)


__all__ = [
    "setcover",
]
