mod bitset;
mod dense;
mod mapping;

pub use bitset::{greedy_set_cover_bitset, BitSet};
pub use dense::greedy_set_cover_dense;
pub use mapping::compress_universe;

use std::collections::HashMap;
use std::hash::Hash;

/// Public router that mirrors the historical API.
///
/// Accepts a `HashMap` of sets keyed by user identifiers and returns the
/// keys of the chosen sets (sorted for stability).
pub fn greedy_set_cover<K, T>(sets: &HashMap<K, Vec<T>>, algo: String) -> Vec<K>
where
    K: Clone + Hash + Eq + std::fmt::Debug + Ord,
    T: Clone + Hash + Eq + std::fmt::Debug,
{
    let (keys, vec_sets) = materialize_sets(sets);
    let cover = run_greedy(&vec_sets, &algo).unwrap_or_else(|| {
        panic!("Error: Unable to find a set cover using algorithm {algo}");
    });

    let mut chosen: Vec<K> = cover.into_iter().map(|idx| keys[idx].clone()).collect();
    chosen.sort();
    chosen
}

/// Variant where the set elements are already dense integers.
pub fn greedy_set_cover_int_elements<K>(sets: &HashMap<K, Vec<usize>>, algo: String) -> Vec<K>
where
    K: Clone + Hash + Eq + std::fmt::Debug + Ord,
{
    let (keys, vec_sets) = materialize_sets(sets);
    let cover = run_greedy(&vec_sets, &algo).unwrap_or_else(|| {
        panic!("Error: Unable to find a set cover using algorithm {algo}");
    });

    let mut chosen: Vec<K> = cover.into_iter().map(|idx| keys[idx].clone()).collect();
    chosen.sort();
    chosen
}

/// Route across the available greedy strategies for a generic Vec-of-Vecs input.
pub fn greedy_set_cover_generic<T: Eq + Hash + Clone>(
    sets: &[Vec<T>],
    algo: &str,
) -> Option<Vec<usize>> {
    match algo {
        "dense" => greedy_set_cover_dense_generic(sets),
        "bitset" => greedy_set_cover_bitset_generic(sets),
        "textbook" => greedy_set_cover_textbook_generic(sets),
        _ => None,
    }
}

fn run_greedy<T: Eq + Hash + Clone>(sets: &[Vec<T>], algo: &str) -> Option<Vec<usize>> {
    let route = match algo {
        "greedy-standard" => "dense",
        "greedy-bitvec" => "bitset",
        "greedy-textbook" => "textbook",
        other => {
            panic!(
                "Wrong algo choice '{other}', must be 'greedy-bitvec', 'greedy-standard' or 'greedy-textbook'"
            );
        }
    };
    greedy_set_cover_generic(sets, route)
}

fn materialize_sets<K, T>(sets: &HashMap<K, Vec<T>>) -> (Vec<K>, Vec<Vec<T>>)
where
    K: Clone + Hash + Eq + std::fmt::Debug,
    T: Clone,
{
    let mut entries: Vec<(K, Vec<T>)> = sets.iter().map(|(k, v)| (k.clone(), v.clone())).collect();
    entries.sort_by(|a, b| {
        b.1.len()
            .cmp(&a.1.len())
            .then_with(|| format!("{:?}", &a.0).cmp(&format!("{:?}", &b.0)))
    });

    let mut keys = Vec::with_capacity(entries.len());
    let mut vec_sets = Vec::with_capacity(entries.len());
    for (k, v) in entries {
        keys.push(k);
        vec_sets.push(v);
    }
    (keys, vec_sets)
}

/// Generic wrapper: greedy dense algorithm for arbitrary `T`.
///
/// Returns indices of chosen sets (into `sets`), or None if not coverable.
pub fn greedy_set_cover_dense_generic<T: Eq + Hash + Clone>(sets: &[Vec<T>]) -> Option<Vec<usize>> {
    let (dense_sets, universe) = mapping::compress_universe(sets);
    let universe_size = universe.len();

    dense::greedy_set_cover_dense(universe_size, &dense_sets)
}

/// Generic wrapper: greedy bitset algorithm for arbitrary `T`.
///
/// Returns indices of chosen sets (into `sets`), or None if not coverable.
pub fn greedy_set_cover_bitset_generic<T: Eq + Hash + Clone>(
    sets: &[Vec<T>],
) -> Option<Vec<usize>> {
    let (dense_sets, universe) = mapping::compress_universe(sets);
    let universe_size = universe.len();

    let sets_bits: Vec<BitSet> = dense_sets
        .iter()
        .map(|s| bitset::make_bitset(universe_size, s))
        .collect();

    bitset::greedy_set_cover_bitset(universe_size, &sets_bits)
}

/// Textbook greedy: pick the set covering the most uncovered elements each round.
pub fn greedy_set_cover_textbook_generic<T: Eq + Hash + Clone>(
    sets: &[Vec<T>],
) -> Option<Vec<usize>> {
    use std::collections::HashSet;

    let mut uncovered: HashSet<T> = sets.iter().flatten().cloned().collect();
    if uncovered.is_empty() {
        return Some(Vec::new());
    }

    let mut chosen = Vec::new();
    let mut used = vec![false; sets.len()];

    while !uncovered.is_empty() {
        let mut best_idx: Option<usize> = None;
        let mut best_gain = 0usize;

        for (idx, set) in sets.iter().enumerate() {
            if used[idx] {
                continue;
            }

            let gain = set.iter().filter(|e| uncovered.contains(*e)).count();
            if gain > best_gain {
                best_gain = gain;
                best_idx = Some(idx);
            }
        }

        let idx = match best_idx {
            Some(i) if best_gain > 0 => i,
            _ => return None,
        };

        used[idx] = true;
        chosen.push(idx);

        for element in &sets[idx] {
            uncovered.remove(element);
        }
    }

    Some(chosen)
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::{HashMap, HashSet};

    fn make_universe<K, T>(sets: &HashMap<K, Vec<T>>) -> HashSet<T>
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
            universe: &HashSet<i32>,
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

        fn check_coverage(cover: &[i32], sets: &HashMap<i32, Vec<i32>>, universe: &HashSet<i32>) {
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

        fn check_coverage(cover: &[i32], sets: &HashMap<i32, Vec<i32>>, universe: &HashSet<i32>) {
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

        fn check_coverage(cover: &[i32], sets: &HashMap<i32, Vec<i32>>, universe: &HashSet<i32>) {
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

        fn check_coverage(cover: &[i32], sets: &HashMap<i32, Vec<i32>>, universe: &HashSet<i32>) {
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
        fn check_coverage(cover: &[i32], sets: &HashMap<i32, Vec<i32>>, universe: &HashSet<i32>) {
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
