#' Set cover (labels only)
#'
#' Returns the chosen set labels of a greedy set cover on a two-column
#' long-form input.
#'
#' @param X Two-column data.frame/data.table in long format: column 1 are set
#'   labels, column 2 are elements.
#' @return A character (or factor) vector of chosen set labels, sorted.
#' @examples
#' df <- data.frame(set = c("A","A","B","C"), element = c(1L,2L,2L,3L))
#' setcover(df)
setcover <- function(X) {
  stopifnot(ncol(X) == 2L)
  X <- data.table::setDT(data.table::copy(X))

  n1 <- names(X)[1L]
  n2 <- names(X)[2L]

  X[, "i0" := .GRP - 1L, by = n1]
  X[, "i1" := .GRP - 1L, by = n2]

  ex_text0 <- sprintf(".(.N,'orvar'=%s[1L])", n1)
  ex_text1 <- sprintf(".(.N,'orvar'=%s[1L])", n2)

  Group_size_i0 <- X[, eval(parse(text = ex_text0)), keyby = "i0"]
  Group_size_i1 <- X[, eval(parse(text = ex_text1)), keyby = "i1"]

  Res <- greedy_set_cover2(
    X[["i0"]], X[["i1"]], Group_size_i0[["N"]], Group_size_i1[["N"]]
  )

  # Map chosen set ids back to labels, sort for deterministic output
  chosen_ids <- unique(Res[, 1L])
  labels <- Group_size_i0[[3L]][chosen_ids + 1L]
  sort(labels)
}

