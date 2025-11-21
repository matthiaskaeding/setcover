/// Greedy set cover on a dense universe {0, 1, ..., universe_size - 1}.
///
/// `sets[i]` is list of elements in set i (each in 0..universe_size).
/// Returns indices of chosen sets, or None if coverage impossible.
pub fn greedy_set_cover_dense(universe_size: usize, sets: &[Vec<usize>]) -> Option<Vec<usize>> {
    if universe_size == 0 {
        return Some(Vec::new());
    }

    let mut uncovered = vec![true; universe_size];
    let mut remaining = universe_size;
    let mut chosen_sets = Vec::new();
    let mut used = vec![false; sets.len()];

    while remaining > 0 {
        let mut best_idx: Option<usize> = None;
        let mut best_cover = 0usize;

        for (i, s) in sets.iter().enumerate() {
            if used[i] {
                continue;
            }
            let mut cover = 0usize;
            for &e in s {
                if e < universe_size && uncovered[e] {
                    cover += 1;
                }
            }
            if cover > best_cover {
                best_cover = cover;
                best_idx = Some(i);
            }
        }

        let idx = match best_idx {
            Some(i) if best_cover > 0 => i,
            _ => return None,
        };

        used[idx] = true;
        chosen_sets.push(idx);

        for &e in &sets[idx] {
            if e < universe_size && uncovered[e] {
                uncovered[e] = false;
                remaining -= 1;
                if remaining == 0 {
                    break;
                }
            }
        }
    }

    Some(chosen_sets)
}
