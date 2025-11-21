#' Solve a set cover instance via the Rust backend.
#'
#' @param df Data frame with at least two columns describing set identifiers and element identifiers.
#' @param set_col Column name containing the set label (character, factor, or integer).
#' @param element_col Column name containing the element identifier.
#' @param algo Algorithm to use: `"greedy-standard"`, `"greedy-bitvec"`, or `"greedy-textbook"`.
#'
#' @return Character vector containing the names of the chosen sets.
#' @export
setcover <- function(df,
                     set_col,
                     element_col,
                     algo = c("greedy-standard", "greedy-bitvec", "greedy-textbook")) {
    algo <- match.arg(algo)
    df <- as.data.frame(df)

    if (!set_col %in% names(df)) {
        stop(sprintf("Column '%s' not found in data frame.", set_col), call. = FALSE)
    }
    if (!element_col %in% names(df)) {
        stop(sprintf("Column '%s' not found in data frame.", element_col), call. = FALSE)
    }

    df <- df[, c(set_col, element_col)]
    df <- df[stats::complete.cases(df), , drop = FALSE]
    if (nrow(df) == 0) {
        return(character())
    }

    set_ids <- as.character(df[[set_col]])
    element_ids <- as.integer(df[[element_col]])
    dense_sets <- split(element_ids, set_ids)

    .Call(wrap__greedy_setcover, dense_sets, algo)
}
