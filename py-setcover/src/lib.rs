use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use std::collections::HashMap;

use setcover_core::{greedy_set_cover, greedy_set_cover_dense};

#[pyfunction]
fn greedy_set_cover_string_i64(
    sets: HashMap<String, Vec<i64>>,
    algo: String,
) -> PyResult<Vec<String>> {
    Ok(greedy_set_cover(&sets, algo))
}

#[pyfunction]
fn greedy_set_cover_string_string(
    sets: HashMap<String, Vec<String>>,
    algo: String,
) -> PyResult<Vec<String>> {
    Ok(greedy_set_cover(&sets, algo))
}

#[pyfunction]
fn greedy_set_cover_i64_i64(sets: HashMap<i64, Vec<i64>>, algo: String) -> PyResult<Vec<i64>> {
    Ok(greedy_set_cover(&sets, algo))
}

#[pyfunction]
fn greedy_set_cover_i64_string(
    sets: HashMap<i64, Vec<String>>,
    algo: String,
) -> PyResult<Vec<i64>> {
    Ok(greedy_set_cover(&sets, algo))
}

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

/// A Python module implemented in Rust.
#[pymodule]
fn _setcover_lib(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(greedy_set_cover_string_i64, m)?)?;
    m.add_function(wrap_pyfunction!(greedy_set_cover_string_string, m)?)?;
    m.add_function(wrap_pyfunction!(greedy_set_cover_i64_i64, m)?)?;
    m.add_function(wrap_pyfunction!(greedy_set_cover_i64_string, m)?)?;
    m.add_function(wrap_pyfunction!(greedy_set_cover_dense_py, m)?)?;
    Ok(())
}
