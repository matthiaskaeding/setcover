use crate::Pick;

/// Outcome of a greedy run.
pub(crate) struct Run {
    pub picks: Vec<Pick>,
    /// Elements still uncovered when greedy ran out of useful sets.
    pub remaining: usize,
    /// `owner[e]` is the index into `sets` of the pick that first covered `e`,
    /// or `usize::MAX` if `e` was never covered. Only present when requested,
    /// since it costs a `usize` per element rather than the scan's `bool`.
    pub owner: Option<Vec<usize>>,
}

/// Run greedy until no unused set covers anything new.
///
/// A non-zero `remaining` means the sets do not span the universe; whether
/// that is an error depends on where `universe_size` came from, which is the
/// caller's business.
pub(crate) fn greedy_picks(universe_size: usize, sets: &[Vec<usize>], track_owner: bool) -> Run {
    let mut uncovered = vec![true; universe_size];
    let mut owner = track_owner.then(|| vec![usize::MAX; universe_size]);
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
            // Nothing left to gain: the remaining elements are unreachable.
            _ => break,
        };

        used[idx] = true;

        // Count while marking rather than trusting `best_cover`: the scan above
        // counts a duplicated element once per occurrence, this cannot.
        let mut n_new = 0usize;
        for &e in &sets[idx] {
            if e < universe_size && uncovered[e] {
                uncovered[e] = false;
                if let Some(owner) = owner.as_mut() {
                    owner[e] = idx;
                }
                remaining -= 1;
                n_new += 1;
                if remaining == 0 {
                    break;
                }
            }
        }

        chosen_sets.push(Pick { set: idx, n_new });
    }

    Run {
        picks: chosen_sets,
        remaining,
        owner,
    }
}

/// Greedy set cover on a dense universe {0, 1, ..., universe_size - 1}.
///
/// `sets[i]` is a list of elements in set i (each in 0..universe_size).
/// Returns the picks in selection order, or None when `sets` does not span the
/// universe. That is reachable here precisely because the caller supplies
/// `universe_size` independently of the sets — see
/// [`crate::greedy_set_cover_dense_generic`] for the variant that derives it
/// and therefore cannot fail.
pub fn greedy_set_cover_dense(universe_size: usize, sets: &[Vec<usize>]) -> Option<Vec<Pick>> {
    let run = greedy_picks(universe_size, sets, false);
    if run.remaining == 0 {
        Some(run.picks)
    } else {
        None
    }
}

/// As [`greedy_set_cover_dense`], plus the element-to-set assignment.
///
/// The second element of the pair is indexed by element: `owner[e]` is the
/// index into `sets` of the chosen set that first covered `e`. Every element
/// appears exactly once, which is what makes it a partition of the universe
/// rather than a join — an element covered by several chosen sets is
/// attributed only to the one that reached it first.
pub fn greedy_set_cover_dense_with_owner(
    universe_size: usize,
    sets: &[Vec<usize>],
) -> Option<(Vec<Pick>, Vec<usize>)> {
    let run = greedy_picks(universe_size, sets, true);
    if run.remaining == 0 {
        Some((run.picks, run.owner.expect("requested above")))
    } else {
        None
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn returns_none_when_sets_do_not_span_the_universe() {
        // Element 2 appears in no set, so a universe of size 3 is not coverable.
        assert_eq!(greedy_set_cover_dense(3, &[vec![0], vec![1]]), None);
    }

    #[test]
    fn empty_universe_is_trivially_covered() {
        assert_eq!(greedy_set_cover_dense(0, &[]), Some(Vec::new()));
        assert_eq!(greedy_set_cover_dense(0, &[vec![]]), Some(Vec::new()));
    }

    #[test]
    fn owner_attributes_each_element_to_the_pick_that_reached_it_first() {
        // Set 0 is picked first (3 new), so it owns 0,1,2 even though set 1
        // also contains 2. Set 1 then owns only 3.
        let (picks, owner) =
            greedy_set_cover_dense_with_owner(4, &[vec![0, 1, 2], vec![2, 3]]).unwrap();

        assert_eq!(picks[0].set, 0);
        assert_eq!(owner, vec![0, 0, 0, 1]);
        // Every element attributed exactly once, so the counts match the gains.
        for pick in &picks {
            assert_eq!(owner.iter().filter(|&&o| o == pick.set).count(), pick.n_new);
        }
    }

    #[test]
    fn owner_is_absent_when_no_cover_exists() {
        assert_eq!(
            greedy_set_cover_dense_with_owner(3, &[vec![0], vec![1]]),
            None
        );
    }

    #[test]
    fn out_of_range_elements_are_ignored() {
        // 9 is outside the universe and must not be counted as a gain.
        let picks = greedy_set_cover_dense(2, &[vec![0, 9], vec![1]]).unwrap();
        assert_eq!(picks.iter().map(|p| p.n_new).sum::<usize>(), 2);
    }
}
