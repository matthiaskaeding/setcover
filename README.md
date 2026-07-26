# Set cover algorithms

High performance implementation of set-cover algorithms.

## The problem

**Input:** a universe $U = \{e_1, \dots, e_n\}$ and a family $\mathcal{S} = \{S_1, \dots, S_m\}$ of subsets of $U$ whose union is $U$.

**Output:** a smallest subfamily $\mathcal{C} \subseteq \mathcal{S}$ with $\bigcup_{S \in \mathcal{C}} S = U$.

**Complexity:** NP-hard. Greedily taking the set that covers the most still-uncovered elements gives a $\ln n + 1$ approximation, essentially the best possible.

### Example: cell towers over neighborhoods

Cover all seven neighborhoods $U = \{A,\dots,G\}$ using as few rooftop sites as possible:

| Site | Covers |
|------|--------|
| $T_1$ | A, B, C |
| $T_2$ | C, D |
| $T_3$ | D, E, F |
| $T_4$ | A, E |
| $T_5$ | F, G |
| $T_6$ | B, G |

Greedy picks $T_1$ (3 new), then $T_3$ (3 new), then $T_5$ for the leftover G — three towers. That's optimal, since no set exceeds 3 elements and two sites could reach at most 6 of the 7.

## Implementations

* `crates/setcover-core`: Rust implementation of the greedy algorithm, roughly
  **5× faster** than `RcppGreedySetCover` 0.1.1 on CRAN. Not a perfect
  comparison — see [docs/benchmarks.md](docs/benchmarks.md) for details.
* `py-setcover`: Python bindings for the Rust crates, using Narwhals to stay
  dataframe-agnostic.
* `RcppGreedySetCover`: R package using C++.
