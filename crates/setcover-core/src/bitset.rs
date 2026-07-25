use crate::Pick;

pub type BitSet = Vec<u64>;

pub fn make_bitset(universe_size: usize, elements: &[usize]) -> BitSet {
    let num_words = universe_size.div_ceil(64);
    let mut bits = vec![0u64; num_words];

    for &e in elements {
        if e >= universe_size {
            continue;
        }
        let word = e / 64;
        let bit = e % 64;
        bits[word] |= 1u64 << bit;
    }

    bits
}

fn make_uncovered(universe_size: usize) -> BitSet {
    let num_words = universe_size.div_ceil(64);
    let mut bits = vec![!0u64; num_words];

    let excess = num_words * 64 - universe_size;
    if excess > 0 {
        let mask = !0u64 >> excess;
        let last = num_words - 1;
        bits[last] &= mask;
    }

    bits
}

fn coverage_gain(set_bits: &BitSet, uncovered: &BitSet) -> usize {
    set_bits
        .iter()
        .zip(uncovered.iter())
        .map(|(s, u)| (s & u).count_ones() as usize)
        .sum()
}

/// Greedy set cover using bitsets.
/// `sets_bits[i]` is the bitset representation of set i.
pub fn greedy_set_cover_bitset(universe_size: usize, sets_bits: &[BitSet]) -> Option<Vec<Pick>> {
    if universe_size == 0 {
        return Some(Vec::new());
    }

    let mut uncovered = make_uncovered(universe_size);
    let mut remaining = universe_size;
    let mut chosen = Vec::new();
    let mut used = vec![false; sets_bits.len()];

    while remaining > 0 {
        let mut best_idx: Option<usize> = None;
        let mut best_gain = 0usize;

        for (i, bits) in sets_bits.iter().enumerate() {
            if used[i] {
                continue;
            }
            let gain = coverage_gain(bits, &uncovered);
            if gain > best_gain {
                best_gain = gain;
                best_idx = Some(i);
            }
        }

        let idx = match best_idx {
            Some(i) if best_gain > 0 => i,
            _ => return None,
        };

        used[idx] = true;

        let bits = &sets_bits[idx];
        let mut n_new = 0usize;
        for (u, s) in uncovered.iter_mut().zip(bits.iter()) {
            let newly_covered = *u & *s;
            let count = newly_covered.count_ones() as usize;
            if count > 0 {
                remaining -= count;
                n_new += count;
            }
            *u &= !s;
        }

        chosen.push(Pick { set: idx, n_new });
    }

    Some(chosen)
}
