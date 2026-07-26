test_that("setcover returns picks in selection order with marginal gains", {
  df <- data.frame(
    set = c("A", "A", "B", "C"),
    element = c(1L, 2L, 2L, 3L),
    stringsAsFactors = FALSE
  )

  res <- setcover(df)

  expect_s3_class(res, "data.table")
  expect_identical(names(res), c("set", "step", "n_new", "n_cum"))
  expect_identical(as.character(res$set), c("A", "C"))
  expect_identical(res$step, 1:2)
  expect_identical(res$n_new, c(2L, 1L))
  expect_identical(res$n_cum, c(2L, 3L))
})

test_that("setcover orders by gain rather than by label", {
  # B is the best first pick (3 new), then C. Sorting alphabetically would put
  # A first, which is exactly the information the ordering preserves.
  df <- data.frame(
    set = c("A", "A", "B", "B", "B", "C", "C"),
    element = c(10L, 20L, 10L, 20L, 30L, 40L, 50L),
    stringsAsFactors = FALSE
  )

  res <- setcover(df)

  expect_identical(as.character(res$set), c("B", "C"))
  expect_identical(res$n_new, c(3L, 2L))
  expect_identical(res$n_cum, c(3L, 5L))
})

test_that("n_cum reaches the universe size", {
  df <- data.frame(
    set = c("S1", "S1", "S2", "S2", "S3", "S3", "S4"),
    element = c(1L, 2L, 2L, 3L, 3L, 4L, 5L),
    stringsAsFactors = FALSE
  )

  res <- setcover(df)

  expect_identical(
    res$n_cum[nrow(res)],
    length(unique(df$element))
  )
})

test_that("setcover accepts columns by name and position", {
  df <- data.frame(
    other = 1:4,
    bucket = c("A", "A", "B", "C"),
    item = c(1L, 2L, 2L, 3L),
    stringsAsFactors = FALSE
  )

  by_name <- setcover(df, set_col = "bucket", el_col = "item")
  by_pos <- setcover(df, set_col = 2L, el_col = 3L)

  expect_identical(as.character(by_name$set), c("A", "C"))
  expect_equal(as.data.frame(by_name), as.data.frame(by_pos))
})

test_that("setcover is quiet unless asked", {
  df <- data.frame(
    set = c("A", "A", "B", "C"),
    element = c(1L, 2L, 2L, 3L),
    stringsAsFactors = FALSE
  )

  expect_silent(setcover(df))
  expect_output(setcover(df, verbose = TRUE), "covered")
})

test_that("the documented migration reproduces the pre-0.2.0 return value", {
  # NEWS and ?setcover both tell upgraders to use sort(setcover(X)$set).
  df <- data.frame(
    set = c("A", "A", "B", "B", "B", "C", "C"),
    element = c(10L, 20L, 10L, 20L, 30L, 40L, 50L),
    stringsAsFactors = FALSE
  )

  old_style <- sort(as.character(setcover(df)$set))

  expect_identical(old_style, c("B", "C"))
  expect_false(is.unsorted(old_style))
})

test_that("setcover handles an empty input", {
  empty <- data.frame(
    set = character(0),
    element = integer(0),
    stringsAsFactors = FALSE
  )

  res <- setcover(empty)

  expect_s3_class(res, "data.table")
  expect_identical(names(res), c("set", "step", "n_new", "n_cum"))
  expect_identical(nrow(res), 0L)
})

test_that("setcover handles a single row", {
  res <- setcover(data.frame(set = "A", element = 1L, stringsAsFactors = FALSE))

  expect_identical(as.character(res$set), "A")
  expect_identical(res$n_new, 1L)
  expect_identical(res$n_cum, 1L)
})

test_that("setcover tolerates duplicate rows", {
  df <- data.frame(
    set = c("A", "A", "A", "A", "B", "B", "B", "C", "C"),
    element = c(1L, 1L, 1L, 2L, 1L, 2L, 3L, 4L, 5L),
    stringsAsFactors = FALSE
  )

  res <- setcover(df)

  expect_identical(as.character(res$set), c("B", "C"))
  expect_identical(res$n_new, c(3L, 2L))
})
