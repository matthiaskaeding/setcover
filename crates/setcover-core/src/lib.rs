use ahash::{AHashMap, AHashSet};
use bitvec::prelude::*;
use std::collections::HashMap;
use std::hash::Hash;

/// Finds an approximate solution to the set cover problem using a greedy algorithm.
///
/// This wrapper function handles the mapping of keys and elements to integers,
/// then calls the appropriate integer-based greedy algorithm. After computation,
/// it maps the integer solution back to the original key type.
///
/// # Arguments
///
/// * `sets`: A `HashMap` where keys are the identifiers of the sets and values are vectors
///   of the elements in each set.
/// * `algo`: A string specifying which implementation to use ("greedy-bitvec",
///   "greedy-standard", or "greedy-textbook").
///
/// # Type Parameters
///
/// * `K`: The type of the set identifiers. Must be cloneable, hashable, equatable, and orderable.
/// * `T`: The type of the elements within the sets. Must be cloneable, hashable, and equatable.
///
/// # Returns
///
/// A sorted vector of the keys of the sets that form the cover.
///
/// # Panics
///
/// Panics if an invalid algorithm choice is provided, or if the underlying
/// algorithms fail to find a cover.
pub fn greedy_set_cover<K, T>(sets: &HashMap<K, Vec<T>>, algo: String) -> Vec<K>
where
    K: Clone + Hash + Eq + std::fmt::Debug + Ord,
    T: Clone + Hash + Eq + std::fmt::Debug,
{
    // 1. Map keys (K) to integers and create a reverse mapping.
    let mut key_to_int = AHashMap::new();
    let mut int_to_key = Vec::new();
    for key in sets.keys() {
        if !key_to_int.contains_key(key) {
            let id = int_to_key.len();
            key_to_int.insert(key.clone(), id);
            int_to_key.push(key.clone());
        }
    }

    // 2. Map elements (T) to integers.
    let mut element_to_int = AHashMap::new();
    let mut next_element_id = 0;
    for element in sets.values().flatten() {
        element_to_int.entry(element.clone()).or_insert_with(|| {
            let id = next_element_id;
            next_element_id += 1;
            id
        });
    }

    // 3. Create a Vec of Vecs for integer-based sets.
    let mut int_sets_vec: Vec<Vec<usize>> = vec![vec![]; int_to_key.len()];
    for (key, elements) in sets {
        let int_key = *key_to_int.get(key).unwrap();
        let int_elements = elements
            .iter()
            .map(|el| *element_to_int.get(el).unwrap())
            .collect();
        int_sets_vec[int_key] = int_elements;
    }

    // Sort by descending size so the greedy-standard variant can short-circuit sooner.
    let mut indices: Vec<usize> = (0..int_sets_vec.len()).collect();
    indices.sort_by(|&a, &b| int_sets_vec[b].len().cmp(&int_sets_vec[a].len()));

    let mut sorted_sets = Vec::with_capacity(int_sets_vec.len());
    let mut sorted_keys = Vec::with_capacity(int_to_key.len());
    for idx in indices {
        sorted_sets.push(int_sets_vec[idx].clone());
        sorted_keys.push(int_to_key[idx].clone());
    }
    int_sets_vec = sorted_sets;
    int_to_key = sorted_keys;

    // 4. Call the selected algorithm. It returns a HashSet of integer keys.
    let cover_int_set: AHashSet<usize> = match algo.as_str() {
        "greedy-bitvec" => greedy_set_cover_bitvec(&int_sets_vec, next_element_id),
        "greedy-standard" => greedy_set_cover_std(&int_sets_vec),
        "greedy-textbook" => greedy_set_cover_textbook(&int_sets_vec),
        _ => panic!(
            "Wrong algo choice, must be 'greedy-bitvec', 'greedy-standard' or 'greedy-textbook'"
        ),
    };

    // 5. Convert the resulting HashSet of integer keys back to the original type K.
    let mut result: Vec<K> = cover_int_set
        .into_iter()
        .map(|i| int_to_key[i].clone())
        .collect();

    // Sort the final result for a deterministic output.
    result.sort();
    result
}

/// Finds an approximate solution to the set cover problem using a greedy algorithm
/// optimized with BitVec.
///
/// # Arguments
///
/// * `sets`: A `Vec` where the index is the integer key and the value is a vector of integer elements.
/// * `universe_size`: The total number of unique elements.
///
/// # Returns
///
/// An `AHashSet` containing the integer keys of the sets that form the cover.
fn greedy_set_cover_bitvec(sets: &Vec<Vec<usize>>, universe_size: usize) -> AHashSet<usize> {
    if universe_size == 0 {
        return AHashSet::new();
    }

    let bit_sets: Vec<BitVec> = sets
        .iter()
        .map(|elements| {
            let mut bv = bitvec![0; universe_size];
            for &id in elements {
                bv.set(id, true);
            }
            bv
        })
        .collect();

    let mut uncovered_elements = bitvec![1; universe_size];
    let mut cover: AHashSet<usize> = AHashSet::new();
    let mut iterations = 0;

    while uncovered_elements.any() && iterations < sets.len() {
        let mut best_set_key: Option<usize> = None;
        let mut best_set_covered_count = 0;

        for (key, bit_set) in bit_sets.iter().enumerate() {
            if cover.contains(&key) {
                continue;
            }

            let mut temp_buffer = bit_set.clone();
            temp_buffer &= &uncovered_elements;
            let covered_count = temp_buffer.count_ones();

            if covered_count > best_set_covered_count {
                best_set_key = Some(key);
                best_set_covered_count = covered_count;
            }
        }

        if let Some(key) = best_set_key {
            // Only compute the intersection for the best set
            let mut temp_buffer = bit_sets[key].clone();
            temp_buffer &= &uncovered_elements;
            uncovered_elements &= &!temp_buffer;
            cover.insert(key);
        } else {
            panic!("Error: Unable to find a set to cover remaining elements.");
        }
        iterations += 1;
    }

    cover
}

/// Finds an approximate solution to the set cover problem using a standard
/// HashSet-based greedy algorithm.
///
/// # Arguments
///
/// * `sets`: A `Vec` where the index is the integer key and the value is a vector of integer elements.
///
/// # Returns
///
/// An `AHashSet` containing the integer keys of the sets that form the cover.
fn greedy_set_cover_std(sets: &Vec<Vec<usize>>) -> AHashSet<usize> {
    let mut uncovered_elements: AHashSet<usize> = sets.iter().flatten().cloned().collect();
    let mut cover = AHashSet::new();
    let mut iterations = 0;

    while !uncovered_elements.is_empty() && iterations < sets.len() {
        let mut best_set_key: Option<usize> = None;
        let mut max_covered = 0;

        for (key, set_elements) in sets.iter().enumerate() {
            if cover.contains(&key) {
                continue;
            }
            if set_elements.len() < max_covered {
                break;
            }

            let intersection_count = set_elements
                .iter()
                .filter(|e| uncovered_elements.contains(e))
                .count();

            if intersection_count > max_covered {
                max_covered = intersection_count;
                best_set_key = Some(key);
            }
        }

        if let Some(key) = best_set_key {
            for element in &sets[key] {
                uncovered_elements.remove(element);
            }
            cover.insert(key);
        } else {
            panic!(
                "Error: Unable to find a set to cover the remaining elements: {:?}",
                uncovered_elements
            );
        }
        iterations += 1;
    }

    cover
}

/// Straightforward textbook greedy algorithm operating on HashSets.
/// Always picks the set that covers the largest number of uncovered
/// elements without any early exits or optimizations.
fn greedy_set_cover_textbook(sets: &Vec<Vec<usize>>) -> AHashSet<usize> {
    let mut uncovered_elements: AHashSet<usize> = sets.iter().flatten().cloned().collect();
    let mut cover = AHashSet::new();

    while !uncovered_elements.is_empty() {
        let mut best_set_key: Option<usize> = None;
        let mut best_cover_count = 0;

        for (key, set_elements) in sets.iter().enumerate() {
            if cover.contains(&key) {
                continue;
            }

            let cover_count = set_elements
                .iter()
                .filter(|e| uncovered_elements.contains(e))
                .count();

            if cover_count > best_cover_count {
                best_cover_count = cover_count;
                best_set_key = Some(key);
            }
        }

        if let Some(key) = best_set_key {
            cover.insert(key);
            for element in &sets[key] {
                uncovered_elements.remove(element);
            }
        } else {
            panic!(
                "Error: Unable to find a set to cover the remaining elements: {:?}",
                uncovered_elements
            );
        }
    }

    cover
}

/// A specialized version of greedy_set_cover for when elements are already integers.
/// This avoids the unnecessary element mapping step.
pub fn greedy_set_cover_int_elements<K>(sets: &HashMap<K, Vec<usize>>, algo: String) -> Vec<K>
where
    K: Clone + Hash + Eq + std::fmt::Debug + Ord,
{
    // 1. Map keys (K) to integers and create a reverse mapping.
    let mut key_to_int = AHashMap::new();
    let mut int_to_key = Vec::new();
    for key in sets.keys() {
        if !key_to_int.contains_key(key) {
            let id = int_to_key.len();
            key_to_int.insert(key.clone(), id);
            int_to_key.push(key.clone());
        }
    }

    // 2. Create a Vec of Vecs for integer-based sets.
    let mut int_sets_vec: Vec<Vec<usize>> = vec![vec![]; int_to_key.len()];
    for (key, elements) in sets {
        let int_key = *key_to_int.get(key).unwrap();
        int_sets_vec[int_key] = elements.clone();
    }

    // 3. Find the maximum element value to determine universe size
    let universe_size = int_sets_vec
        .iter()
        .flat_map(|v| v.iter())
        .max()
        .map_or(0, |&x| x + 1);

    // Sort by descending size to match the generic wrapper behavior.
    let mut indices: Vec<usize> = (0..int_sets_vec.len()).collect();
    indices.sort_by(|&a, &b| int_sets_vec[b].len().cmp(&int_sets_vec[a].len()));
    let mut sorted_sets = Vec::with_capacity(int_sets_vec.len());
    let mut sorted_keys = Vec::with_capacity(int_to_key.len());
    for idx in indices {
        sorted_sets.push(int_sets_vec[idx].clone());
        sorted_keys.push(int_to_key[idx].clone());
    }
    int_sets_vec = sorted_sets;
    int_to_key = sorted_keys;

    // 4. Call the selected algorithm
    let cover_int_set: AHashSet<usize> = match algo.as_str() {
        "greedy-bitvec" => greedy_set_cover_bitvec(&int_sets_vec, universe_size),
        "greedy-standard" => greedy_set_cover_std(&int_sets_vec),
        "greedy-textbook" => greedy_set_cover_textbook(&int_sets_vec),
        _ => panic!(
            "Wrong algo choice, must be 'greedy-bitvec', 'greedy-standard' or 'greedy-textbook'"
        ),
    };

    // 5. Convert back to original type K
    let mut result: Vec<K> = cover_int_set
        .into_iter()
        .map(|i| int_to_key[i].clone())
        .collect();

    result.sort();
    result
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::HashMap;

    fn make_universe<K, T>(sets: &HashMap<K, Vec<T>>) -> AHashSet<T>
    where
        T: Clone + Hash + Eq,
    {
        sets.values().flatten().cloned().collect()
    }

    #[test]
    fn test_basic_case() {
        let mut sets = HashMap::new();
        sets.insert("A".to_string(), vec![1, 2, 3]);
        sets.insert("B".to_string(), vec![1, 2]);
        sets.insert("C".to_string(), vec![2]);

        let set_cover_0 = greedy_set_cover(&sets, "greedy-standard".to_string());
        let set_cover_1 = greedy_set_cover(&sets, "greedy-bitvec".to_string());
        let set_cover_2 = greedy_set_cover(&sets, "greedy-textbook".to_string());
        let universe = make_universe(&sets);

        fn check_coverage(
            cover: &[String],
            sets: &HashMap<String, Vec<i32>>,
            universe: &AHashSet<i32>,
        ) {
            let covered_sets: HashMap<String, Vec<i32>> = cover
                .iter()
                .map(|key| (key.clone(), sets.get(key).unwrap().clone()))
                .collect();
            let covered_universe = make_universe(&covered_sets);
            assert_eq!(universe, &covered_universe);
        }

        assert_eq!(set_cover_0, vec!["A".to_string()]);
        assert_eq!(set_cover_1, vec!["A".to_string()]);
        assert_eq!(set_cover_2, vec!["A".to_string()]);

        check_coverage(&set_cover_0, &sets, &universe);
        check_coverage(&set_cover_1, &sets, &universe);
        check_coverage(&set_cover_2, &sets, &universe);
    }

    #[test]
    fn test_with_empty_set() {
        let mut sets = HashMap::new();
        sets.insert(1, vec![1, 2, 3]);
        sets.insert(2, vec![]);
        sets.insert(3, vec![3, 4, 5]);

        let set_cover_0 = greedy_set_cover(&sets, "greedy-standard".to_string());
        let set_cover_1 = greedy_set_cover(&sets, "greedy-bitvec".to_string());
        let set_cover_2 = greedy_set_cover(&sets, "greedy-textbook".to_string());
        let universe = make_universe(&sets);

        fn check_coverage(cover: &[i32], sets: &HashMap<i32, Vec<i32>>, universe: &AHashSet<i32>) {
            let covered_sets: HashMap<i32, Vec<i32>> = cover
                .iter()
                .map(|&key| (key, sets.get(&key).unwrap().clone()))
                .collect();
            let covered_universe = make_universe(&covered_sets);
            assert_eq!(universe, &covered_universe);
        }

        assert_eq!(set_cover_0, vec![1, 3]);
        assert_eq!(set_cover_1, vec![1, 3]);
        assert_eq!(set_cover_2, vec![1, 3]);

        check_coverage(&set_cover_0, &sets, &universe);
        check_coverage(&set_cover_1, &sets, &universe);
        check_coverage(&set_cover_2, &sets, &universe);
    }

    #[test]
    fn test_all_sets_needed() {
        let mut sets = HashMap::new();
        sets.insert(1, vec![1]);
        sets.insert(2, vec![2]);
        sets.insert(3, vec![3]);

        let set_cover_0 = greedy_set_cover(&sets, "greedy-standard".to_string());
        let set_cover_1 = greedy_set_cover(&sets, "greedy-bitvec".to_string());
        let set_cover_2 = greedy_set_cover(&sets, "greedy-textbook".to_string());

        assert_eq!(sets.len(), set_cover_0.len());
        assert_eq!(sets.len(), set_cover_1.len());
        assert_eq!(sets.len(), set_cover_2.len());

        let universe = make_universe(&sets);

        fn check_coverage(cover: &[i32], sets: &HashMap<i32, Vec<i32>>, universe: &AHashSet<i32>) {
            let covered_sets: HashMap<i32, Vec<i32>> = cover
                .iter()
                .map(|&key| (key, sets.get(&key).unwrap().clone()))
                .collect();
            let covered_universe = make_universe(&covered_sets);
            assert_eq!(universe, &covered_universe);
        }

        check_coverage(&set_cover_0, &sets, &universe);
        check_coverage(&set_cover_1, &sets, &universe);
        check_coverage(&set_cover_2, &sets, &universe);
    }

    #[test]
    fn test_one_set_covers_all() {
        let mut sets = HashMap::new();
        sets.insert(1, vec![1, 2, 3, 4, 5]);
        sets.insert(2, vec![1, 2]);
        sets.insert(3, vec![3, 4]);

        let set_cover_0 = greedy_set_cover(&sets, "greedy-standard".to_string());
        let set_cover_1 = greedy_set_cover(&sets, "greedy-bitvec".to_string());
        let set_cover_2 = greedy_set_cover(&sets, "greedy-textbook".to_string());

        assert_eq!(set_cover_0.len(), 1);
        assert_eq!(set_cover_1.len(), 1);
        assert_eq!(set_cover_2.len(), 1);
        assert_eq!(set_cover_0, vec![1]);
        assert_eq!(set_cover_1, vec![1]);
        assert_eq!(set_cover_2, vec![1]);

        let universe = make_universe(&sets);

        fn check_coverage(cover: &[i32], sets: &HashMap<i32, Vec<i32>>, universe: &AHashSet<i32>) {
            let covered_sets: HashMap<i32, Vec<i32>> = cover
                .iter()
                .map(|&key| (key, sets.get(&key).unwrap().clone()))
                .collect();
            let covered_universe = make_universe(&covered_sets);
            assert_eq!(universe, &covered_universe);
        }

        check_coverage(&set_cover_0, &sets, &universe);
        check_coverage(&set_cover_1, &sets, &universe);
        check_coverage(&set_cover_2, &sets, &universe);
    }

    #[test]
    fn test_overlapping_sets() {
        let mut sets = HashMap::new();
        sets.insert(1, vec![1, 2, 3]);
        sets.insert(2, vec![3, 4, 5]);
        sets.insert(3, vec![5, 6, 7]);

        let set_cover_0 = greedy_set_cover(&sets, "greedy-standard".to_string());
        let set_cover_1 = greedy_set_cover(&sets, "greedy-bitvec".to_string());
        let set_cover_2 = greedy_set_cover(&sets, "greedy-textbook".to_string());

        assert_eq!(set_cover_0.len(), 3);
        assert_eq!(set_cover_1.len(), 3);
        assert_eq!(set_cover_2.len(), 3);

        let universe = make_universe(&sets);

        fn check_coverage(cover: &[i32], sets: &HashMap<i32, Vec<i32>>, universe: &AHashSet<i32>) {
            let covered_sets: HashMap<i32, Vec<i32>> = cover
                .iter()
                .map(|&key| (key, sets.get(&key).unwrap().clone()))
                .collect();
            let covered_universe = make_universe(&covered_sets);
            assert_eq!(universe, &covered_universe);
        }

        check_coverage(&set_cover_0, &sets, &universe);
        check_coverage(&set_cover_1, &sets, &universe);
        check_coverage(&set_cover_2, &sets, &universe);
    }

    #[test]
    fn test_complex_deterministic_cases() {
        let mut sets = HashMap::new();
        sets.insert(1, vec![1, 2, 3, 4, 5, 6]); // S1 (Best initial choice)
        sets.insert(2, vec![1, 2, 7]);
        sets.insert(3, vec![3, 4, 8]);
        sets.insert(4, vec![5, 6, 9]);
        sets.insert(5, vec![7, 8, 9, 10]); // S5 (Best second choice to cover 7,8,9,10)

        let set_cover_0 = greedy_set_cover(&sets, "greedy-standard".to_string());
        let set_cover_1 = greedy_set_cover(&sets, "greedy-bitvec".to_string());
        let set_cover_2 = greedy_set_cover(&sets, "greedy-textbook".to_string());

        assert_eq!(set_cover_0, vec![1, 5]);
        assert_eq!(set_cover_1, vec![1, 5]);
        assert_eq!(set_cover_2, vec![1, 5]);

        let universe = make_universe(&sets);
        fn check_coverage(cover: &[i32], sets: &HashMap<i32, Vec<i32>>, universe: &AHashSet<i32>) {
            let covered_sets: HashMap<i32, Vec<i32>> = cover
                .iter()
                .map(|&key| (key, sets.get(&key).unwrap().clone()))
                .collect();
            let covered_universe = make_universe(&covered_sets);
            assert_eq!(universe, &covered_universe);
        }

        check_coverage(&set_cover_0, &sets, &universe);
        check_coverage(&set_cover_1, &sets, &universe);
        check_coverage(&set_cover_2, &sets, &universe);
    }

    #[test]
    fn test_output_is_sorted() {
        let mut sets = HashMap::new();
        sets.insert(3, vec![1, 2, 3]);
        sets.insert(1, vec![4, 5, 6]);
        sets.insert(2, vec![7, 8, 9]);
        sets.insert(4, vec![10, 11, 12]);

        let set_cover_0 = greedy_set_cover(&sets, "greedy-standard".to_string());
        let set_cover_1 = greedy_set_cover(&sets, "greedy-bitvec".to_string());
        let set_cover_2 = greedy_set_cover(&sets, "greedy-textbook".to_string());

        let expected = vec![1, 2, 3, 4];
        assert_eq!(set_cover_0, expected);
        assert_eq!(set_cover_1, expected);
        assert_eq!(set_cover_2, expected);

        assert!(
            set_cover_0.windows(2).all(|w| w[0] <= w[1]),
            "Output from greedy-standard is not sorted"
        );
        assert!(
            set_cover_1.windows(2).all(|w| w[0] <= w[1]),
            "Output from greedy-bitvec is not sorted"
        );
        assert!(
            set_cover_2.windows(2).all(|w| w[0] <= w[1]),
            "Output from greedy-textbook is not sorted"
        );
    }

    #[test]
    fn test_two_sets_with_same_elements() {
        let mut sets = HashMap::new();
        sets.insert(1, vec![1]);
        sets.insert(2, vec![2]);

        let set_cover_0 = greedy_set_cover(&sets, "greedy-standard".to_string());
        let set_cover_1 = greedy_set_cover(&sets, "greedy-bitvec".to_string());
        let set_cover_2 = greedy_set_cover(&sets, "greedy-textbook".to_string());

        assert_eq!(set_cover_0.len(), 2);
        assert_eq!(set_cover_1.len(), 2);
        assert_eq!(set_cover_2.len(), 2);
    }
}
