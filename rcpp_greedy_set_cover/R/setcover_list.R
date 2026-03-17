#' Set cover for list-of-vectors
#'
#' Solve greedy set cover when input is a list of vectors (each vector is a set).
#'
#' @param sets A list of atomic vectors representing sets. Elements can be
#'   integer, character, or other atomic types coercible to a vector.
#' @param only_sets If TRUE, return 1-based indices of chosen sets. Otherwise,
#'   return the chosen subsets themselves as a sub-list (default).
#' @return A sub-list of `sets` (default) or integer indices if `only_sets=TRUE`.
#' @examples
#' sets <- list(A = c(1L, 2L), B = 2L, C = 3L)
#' setcover_list(sets, only_sets = TRUE)
#' setcover_list(sets)
setcover_list <- function(sets, only_sets = FALSE) {
  stopifnot(is.list(sets))

  # Flatten and build dense ids for elements
  els <- unlist(sets, recursive = TRUE, use.names = FALSE)
  # Ensure atomic vector
  if (!is.atomic(els)) {
    els <- as.character(els)
  }
  u <- unique(els)
  # Map each element to id in 0..|U|-1
  i1 <- match(els, u) - 1L
  # Set indices 0..n_sets-1 repeated by lengths
  lens <- lengths(sets)
  i0 <- rep.int(seq_along(sets) - 1L, lens)
  # Group sizes for preallocation (as in data.table path)
  group_sizes_i0 <- as.integer(lens)
  group_sizes_i1 <- as.integer(tabulate(i1 + 1L, nbins = length(u)))

  Res <- greedy_set_cover2(i0, i1, group_sizes_i0, group_sizes_i1)
  chosen_ids0 <- sort(unique(Res[, 1L]))
  if (only_sets) {
    return(chosen_ids0 + 1L)
  }
  sets[chosen_ids0 + 1L]
}

