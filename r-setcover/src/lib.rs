use extendr_api::prelude::*;
use setcover_core::greedy_set_cover;
use std::collections::HashMap;
use std::convert::TryFrom;
use std::panic;

/// Convert an R list (`list(name = c(1L, 2L), ...)`) into
/// the HashMap format expected by the Rust solver.
fn list_to_hashmap(sets: List) -> extendr_api::Result<HashMap<String, Vec<i64>>> {
    if sets.len() == 0 {
        return Ok(HashMap::new());
    }

    let mut map = HashMap::with_capacity(sets.len());
    for (idx, (name, value)) in sets.iter().enumerate() {
        let set_name = if name.is_empty() {
            format!("set_{}", idx + 1)
        } else {
            name.to_string()
        };

        let integers = Integers::try_from(value).map_err(|_| {
            extendr_api::Error::Other("Each set must be an integer vector.".to_string())
        })?;

        let mut elements = Vec::with_capacity(integers.len());
        for entry in integers.iter() {
            if let Some(val) = Option::<i32>::from(entry) {
                elements.push(val as i64);
            }
        }

        map.insert(set_name, elements);
    }

    Ok(map)
}

#[extendr]
fn greedy_setcover(sets: List, algo: &str) -> extendr_api::Result<Vec<String>> {
    let algo = if algo.is_empty() {
        "greedy-standard"
    } else {
        algo
    };

    let map = list_to_hashmap(sets)?;
    if map.is_empty() {
        return Ok(Vec::new());
    }

    let owned_algo = algo.to_string();
    let cover = panic::catch_unwind(|| greedy_set_cover(&map, owned_algo.clone()))
        .map_err(|_| extendr_api::Error::Other("Unable to run greedy solver.".to_string()))?;

    Ok(cover)
}

extendr_module! {
    mod rsetcover;
    fn greedy_setcover;
}
