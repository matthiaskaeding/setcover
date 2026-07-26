use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

use setcover_core::{greedy_set_cover_dense, greedy_set_cover_dense_with_owner};

/// Returns `(set_index, n_new)` pairs in greedy selection order.
#[pyfunction]
fn greedy_set_cover_dense_py(
    universe_size: usize,
    sets: Vec<Vec<usize>>,
) -> PyResult<Vec<(usize, usize)>> {
    let picks = greedy_set_cover_dense(universe_size, &sets).ok_or_else(|| {
        PyValueError::new_err("Unable to find a set cover for the provided dataset.")
    })?;
    Ok(picks.into_iter().map(|p| (p.set, p.n_new)).collect())
}

/// `(set_index, n_new)` pairs in selection order.
type Picks = Vec<(usize, usize)>;
/// Indexed by element: the index of the chosen set that first covered it.
type Owner = Vec<usize>;

/// As `greedy_set_cover_dense_py`, plus the element-to-set assignment.
#[pyfunction]
fn greedy_set_cover_dense_with_owner_py(
    universe_size: usize,
    sets: Vec<Vec<usize>>,
) -> PyResult<(Picks, Owner)> {
    let (picks, owner) =
        greedy_set_cover_dense_with_owner(universe_size, &sets).ok_or_else(|| {
            PyValueError::new_err("Unable to find a set cover for the provided dataset.")
        })?;
    Ok((picks.into_iter().map(|p| (p.set, p.n_new)).collect(), owner))
}

/// A Python module implemented in Rust.
#[pymodule]
fn _setcover_lib(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(greedy_set_cover_dense_py, m)?)?;
    m.add_function(wrap_pyfunction!(greedy_set_cover_dense_with_owner_py, m)?)?;
    Ok(())
}
