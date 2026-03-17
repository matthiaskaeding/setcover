test_that("setcover returns chosen set labels (sorted)", {
  df <- data.frame(
    set = c("A", "A", "B", "C"),
    element = c(1L, 2L, 2L, 3L),
    stringsAsFactors = FALSE
  )
  res <- setcover(df)
  expect_true(is.vector(res) || is.factor(res))
  expect_identical(as.character(res), c("A", "C"))
})

