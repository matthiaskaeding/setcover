# Resolve a column given by name or position to a column name, with errors
# that say which argument was wrong and what was available.
resolve_column <- function(X, col, arg) {
  if (length(col) != 1L || is.na(col)) {
    stop(arg, " must be a single column name or position", call. = FALSE)
  }
  if (is.character(col)) {
    if (!col %in% names(X)) {
      stop(
        arg, " = \"", col, "\" is not a column of X; available: ",
        paste(names(X), collapse = ", "),
        call. = FALSE
      )
    }
    return(col)
  }
  col <- as.integer(col)
  if (is.na(col) || col < 1L || col > ncol(X)) {
    stop(
      arg, " = ", col, " is out of range; X has ", ncol(X), " columns",
      call. = FALSE
    )
  }
  names(X)[[col]]
}

#' Set cover
#'
#' Greedy set cover on a long-form input. Results come back in greedy selection
#' order, highest-gain set first, so any prefix is itself a good partial cover:
#' take the first k rows for the k sets that cover the most.
#'
#' @param X data.frame/data.table in long format, with one column of set labels
#'   and one of elements. Extra columns are ignored.
#' @param set_col Column holding the set labels, by name or position. Defaults
#'   to the first column.
#' @param el_col Column holding the elements, by name or position. Defaults to
#'   the second column.
#' @param verbose If \code{TRUE}, print the solver's coverage progress.
#' @return A \code{data.table} with one row per chosen set, in selection order:
#'   \code{set} (the label), \code{step} (selection order, starting at 1),
#'   \code{n_new} (elements this pick was the first to cover) and \code{n_cum}
#'   (the running total, reaching the universe size in the final row).
#' @section Breaking change in 0.2.0:
#' Before 0.2.0 this function returned the chosen labels as a vector, sorted
#' alphabetically, and printed the solver's coverage progress. It now returns
#' the \code{data.table} described above and is silent by default. To restore
#' the old return value, use \code{sort(setcover(X)$set)}; for the old output,
#' pass \code{verbose = TRUE}. \code{\link{greedySetCover}} is unaffected.
#' @export
#' @examples
#' df <- data.frame(set = c("A", "A", "B", "C"), element = c(1L, 2L, 2L, 3L))
#' setcover(df)
setcover <- function(X, set_col = 1L, el_col = 2L, verbose = FALSE) {
  if (!is.data.frame(X)) {
    stop("X must be a data.frame or data.table, not ", class(X)[1L], call. = FALSE)
  }
  if (ncol(X) < 2L) {
    stop("X must have at least two columns, but has ", ncol(X), call. = FALSE)
  }

  n1 <- resolve_column(X, set_col, "set_col")
  n2 <- resolve_column(X, el_col, "el_col")
  if (identical(n1, n2)) {
    stop(
      "set_col and el_col must name different columns, both are \"", n1, "\"",
      call. = FALSE
    )
  }

  X <- data.table::setDT(data.table::copy(X))

  X[, "i0" := .GRP - 1L, by = n1]
  X[, "i1" := .GRP - 1L, by = n2]

  ex_text0 <- sprintf(".(.N,'orvar'=%s[1L])", n1)
  ex_text1 <- sprintf(".(.N,'orvar'=%s[1L])", n2)

  Group_size_i0 <- X[, eval(parse(text = ex_text0)), keyby = "i0"]
  Group_size_i1 <- X[, eval(parse(text = ex_text1)), keyby = "i1"]

  solve <- function() {
    greedy_set_cover2(
      X[["i0"]], X[["i1"]], Group_size_i0[["N"]], Group_size_i1[["N"]]
    )
  }
  if (verbose) {
    Res <- solve()
  } else {
    # greedy_set_cover2 writes coverage progress to stdout unconditionally.
    utils::capture.output(Res <- solve())
  }

  # greedy_set_cover2 emits one row per element, grouped contiguously by the
  # set that first covered it, in selection order. A set is picked at most
  # once, so run lengths are exactly the marginal gains.
  runs <- rle(Res[, 1L])
  n_new <- runs$lengths

  data.table::data.table(
    set = Group_size_i0[[3L]][runs$values + 1L],
    step = seq_along(runs$values),
    n_new = n_new,
    n_cum = cumsum(n_new)
  )
}
