use std::collections::HashMap;
use std::hash::Hash;

/// Compress arbitrary elements into dense ids 0..n-1.
///
/// `sets[i]` is the i-th set.
/// Returns:
///   - dense_sets: same shape as `sets` but elements are `usize` in 0..n-1
///   - reverse: where reverse[id] gives back the original element T
pub fn compress_universe<T: Eq + Hash + Clone>(sets: &[Vec<T>]) -> (Vec<Vec<usize>>, Vec<T>) {
    let mut map: HashMap<T, usize> = HashMap::new();
    let mut reverse: Vec<T> = Vec::new();

    for s in sets {
        for item in s {
            if !map.contains_key(item) {
                let id = reverse.len();
                map.insert(item.clone(), id);
                reverse.push(item.clone());
            }
        }
    }

    let mut dense_sets = Vec::with_capacity(sets.len());
    for s in sets {
        dense_sets.push(s.iter().map(|x| map[x]).collect());
    }

    (dense_sets, reverse)
}
