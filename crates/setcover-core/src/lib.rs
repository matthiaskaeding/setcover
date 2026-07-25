mod dense;
mod mapping;

pub use dense::greedy_set_cover_dense;
pub use mapping::compress_universe;

use std::collections::HashMap;
use std::hash::Hash;

/// One greedy selection, in the order the solver made it.
///
/// Greedy set cover is a sequence: each pick takes the set covering the most
/// still-uncovered elements, so any prefix of the picks is itself a good
/// partial cover. `n_new` is that pick's marginal gain — the count of elements
/// it was the first to cover — which is what tells a caller where the coverage
/// curve flattens.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Pick {
    /// Index of the chosen set in the caller's input.
    pub set: usize,
    /// Elements newly covered by this pick.
    pub n_new: usize,
}

/// Greedy set cover over a map of user-identified sets.
///
/// Returns the keys of the chosen sets, sorted for stability. Use
/// [`greedy_set_cover_dense_generic`] when the selection order and the
/// per-pick gains matter.
pub fn greedy_set_cover<K, T>(sets: &HashMap<K, Vec<T>>) -> Vec<K>
where
    K: Clone + Hash + Eq + Ord,
    T: Clone + Hash + Eq,
{
    let (keys, vec_sets) = materialize_sets(sets);
    let cover = greedy_set_cover_dense_generic(&vec_sets);

    let mut chosen: Vec<K> = cover.into_iter().map(|p| keys[p.set].clone()).collect();
    chosen.sort();
    chosen
}

fn materialize_sets<K, T>(sets: &HashMap<K, Vec<T>>) -> (Vec<K>, Vec<Vec<T>>)
where
    K: Clone + Hash + Eq + Ord,
    T: Clone,
{
    let mut entries: Vec<(K, Vec<T>)> = sets.iter().map(|(k, v)| (k.clone(), v.clone())).collect();
    // Largest first, ties broken by key order. `K: Ord` is the right comparison
    // here; the previous Debug-string tie-break sorted 10 before 9.
    entries.sort_by(|a, b| b.1.len().cmp(&a.1.len()).then_with(|| a.0.cmp(&b.0)));

    let mut keys = Vec::with_capacity(entries.len());
    let mut vec_sets = Vec::with_capacity(entries.len());
    for (k, v) in entries {
        keys.push(k);
        vec_sets.push(v);
    }
    (keys, vec_sets)
}

/// Greedy set cover for arbitrary element types.
///
/// Compresses the universe to dense integers, then runs the dense solver, and
/// returns the picks in selection order.
///
/// Infallible by construction: the universe is derived from `sets`, so their
/// union spans it and greedy always terminates with everything covered. Use
/// [`greedy_set_cover_dense`] when you supply `universe_size` yourself, since
/// that one can genuinely fail.
pub fn greedy_set_cover_dense_generic<T: Eq + Hash + Clone>(sets: &[Vec<T>]) -> Vec<Pick> {
    let (dense_sets, universe) = mapping::compress_universe(sets);

    let (picks, remaining) = dense::greedy_picks(universe.len(), &dense_sets);
    debug_assert_eq!(
        remaining, 0,
        "a universe derived from the input sets is always fully covered"
    );

    picks
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::{HashMap, HashSet};

    /// Textbook greedy, kept as a reference oracle for the dense solver.
    ///
    /// Deliberately naive: rescan every set each round and count matches
    /// against a `HashSet` of uncovered elements. Slow, but obviously correct,
    /// which is the point — the dense solver is checked against it.
    fn greedy_set_cover_textbook<T: Eq + Hash + Clone>(sets: &[Vec<T>]) -> Vec<Pick> {
        let mut uncovered: HashSet<T> = sets.iter().flatten().cloned().collect();

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
                // Unreachable: the universe is derived from these same sets.
                _ => break,
            };

            used[idx] = true;

            let mut n_new = 0usize;
            for element in &sets[idx] {
                if uncovered.remove(element) {
                    n_new += 1;
                }
            }

            chosen.push(Pick { set: idx, n_new });
        }

        chosen
    }

    fn make_universe<K, T>(sets: &HashMap<K, Vec<T>>) -> HashSet<T>
    where
        T: Clone + Hash + Eq,
    {
        sets.values().flatten().cloned().collect()
    }

    fn check_coverage<K, T>(cover: &[K], sets: &HashMap<K, Vec<T>>, universe: &HashSet<T>)
    where
        K: Clone + Hash + Eq,
        T: Clone + Hash + Eq + std::fmt::Debug,
    {
        let covered: HashSet<T> = cover
            .iter()
            .flat_map(|key| sets.get(key).unwrap().iter().cloned())
            .collect();
        assert_eq!(&covered, universe);
    }

    /// The dense solver must agree with the textbook oracle, pick for pick.
    fn assert_matches_oracle<T: Eq + Hash + Clone + std::fmt::Debug>(sets: &[Vec<T>]) {
        assert_eq!(
            greedy_set_cover_dense_generic(sets),
            greedy_set_cover_textbook(sets),
            "dense solver disagreed with the textbook oracle"
        );
    }

    #[test]
    fn test_basic_case() {
        let mut sets = HashMap::new();
        sets.insert("A".to_string(), vec![1, 2, 3]);
        sets.insert("B".to_string(), vec![1, 2]);
        sets.insert("C".to_string(), vec![2]);

        let cover = greedy_set_cover(&sets);
        assert_eq!(cover, vec!["A".to_string()]);
        check_coverage(&cover, &sets, &make_universe(&sets));
    }

    #[test]
    fn test_with_empty_set() {
        let mut sets = HashMap::new();
        sets.insert(1, vec![1, 2, 3]);
        sets.insert(2, vec![]);
        sets.insert(3, vec![3, 4, 5]);

        let cover = greedy_set_cover(&sets);
        assert_eq!(cover, vec![1, 3]);
        check_coverage(&cover, &sets, &make_universe(&sets));
    }

    #[test]
    fn test_all_sets_needed() {
        let mut sets = HashMap::new();
        sets.insert(1, vec![1]);
        sets.insert(2, vec![2]);
        sets.insert(3, vec![3]);

        let cover = greedy_set_cover(&sets);
        assert_eq!(cover.len(), sets.len());
        check_coverage(&cover, &sets, &make_universe(&sets));
    }

    #[test]
    fn test_one_set_covers_all() {
        let mut sets = HashMap::new();
        sets.insert(1, vec![1, 2, 3, 4, 5]);
        sets.insert(2, vec![1, 2]);
        sets.insert(3, vec![3, 4]);

        let cover = greedy_set_cover(&sets);
        assert_eq!(cover, vec![1]);
        check_coverage(&cover, &sets, &make_universe(&sets));
    }

    #[test]
    fn test_overlapping_sets() {
        let mut sets = HashMap::new();
        sets.insert(1, vec![1, 2, 3]);
        sets.insert(2, vec![3, 4, 5]);
        sets.insert(3, vec![5, 6, 7]);

        let cover = greedy_set_cover(&sets);
        assert_eq!(cover.len(), 3);
        check_coverage(&cover, &sets, &make_universe(&sets));
    }

    #[test]
    fn test_complex_deterministic_cases() {
        let mut sets = HashMap::new();
        sets.insert(1, vec![1, 2, 3, 4, 5, 6]); // best initial choice
        sets.insert(2, vec![1, 2, 7]);
        sets.insert(3, vec![3, 4, 8]);
        sets.insert(4, vec![5, 6, 9]);
        sets.insert(5, vec![7, 8, 9, 10]); // best second choice

        let cover = greedy_set_cover(&sets);
        assert_eq!(cover, vec![1, 5]);
        check_coverage(&cover, &sets, &make_universe(&sets));
    }

    #[test]
    fn test_output_is_sorted() {
        let mut sets = HashMap::new();
        sets.insert(3, vec![1, 2, 3]);
        sets.insert(1, vec![4, 5, 6]);
        sets.insert(2, vec![7, 8, 9]);
        sets.insert(4, vec![10, 11, 12]);

        let cover = greedy_set_cover(&sets);
        assert_eq!(cover, vec![1, 2, 3, 4]);
        assert!(cover.windows(2).all(|w| w[0] <= w[1]), "output not sorted");
    }

    #[test]
    fn test_two_sets_with_same_elements() {
        let mut sets = HashMap::new();
        sets.insert(1, vec![1]);
        sets.insert(2, vec![2]);

        assert_eq!(greedy_set_cover(&sets).len(), 2);
    }

    #[test]
    fn test_ties_break_on_key_order_not_debug_string() {
        // Every set has size 1, so every comparison is a tie. Debug-string
        // ordering would rank 10 before 9; Ord must not.
        let mut sets = HashMap::new();
        for k in [9, 10, 100] {
            sets.insert(k, vec![k]);
        }

        let cover = greedy_set_cover(&sets);
        assert_eq!(cover, vec![9, 10, 100]);
    }

    #[test]
    fn test_picks_are_in_greedy_order_with_marginal_gains() {
        // B is the best first pick (3 new), then C (2 new). Alphabetical
        // sorting would put A first and lose that.
        let sets = vec![
            vec![10, 20],     // A
            vec![10, 20, 30], // B
            vec![40, 50],     // C
        ];

        let picks = greedy_set_cover_dense_generic(&sets);
        assert_eq!(picks[0], Pick { set: 1, n_new: 3 });
        assert_eq!(picks[1], Pick { set: 2, n_new: 2 });
        assert_eq!(picks.len(), 2);
        assert_matches_oracle(&sets);
    }

    #[test]
    fn test_marginal_gains_sum_to_universe_size() {
        let sets = vec![vec![1, 2, 3], vec![3, 4, 5], vec![5, 6, 7]];
        let universe: HashSet<i32> = sets.iter().flatten().cloned().collect();

        let picks = greedy_set_cover_dense_generic(&sets);
        let total: usize = picks.iter().map(|p| p.n_new).sum();
        assert_eq!(total, universe.len());
        assert_matches_oracle(&sets);
    }

    #[test]
    fn test_marginal_gain_ignores_duplicate_elements() {
        // The selection scan counts the repeated 1 three times; n_new must not.
        let sets = vec![vec![1, 1, 1, 2], vec![3]];

        let picks = greedy_set_cover_dense_generic(&sets);
        let dup_set = picks.iter().find(|p| p.set == 0).unwrap();
        assert_eq!(dup_set.n_new, 2);
        assert_matches_oracle(&sets);
    }

    #[test]
    fn test_dense_matches_oracle_on_assorted_shapes() {
        let cases: Vec<Vec<Vec<i32>>> = vec![
            vec![vec![1, 2, 3], vec![1, 2], vec![2]],
            vec![vec![1, 2, 3], vec![], vec![3, 4, 5]],
            vec![vec![1], vec![2], vec![3]],
            vec![vec![1, 2, 3, 4, 5], vec![1, 2], vec![3, 4]],
            vec![
                vec![1, 2, 3, 4, 5, 6],
                vec![1, 2, 7],
                vec![3, 4, 8],
                vec![7, 8, 9, 10],
            ],
            vec![vec![5, 5, 5], vec![5, 6], vec![7]],
        ];

        for sets in &cases {
            assert_matches_oracle(sets);
        }
    }
}
