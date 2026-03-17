test_that("setcover_list returns indices when requested", {
  sets <- list(c(1L, 2L), 2L, 3L)
  idx <- setcover_list(sets, only_sets = TRUE)
  expect_identical(idx, c(1L, 3L))
})

test_that("setcover_list returns a sub-list by default", {
  sets <- list(c(1L, 2L), 2L, 3L)
  res <- setcover_list(sets)
  expect_true(is.list(res))
  expect_identical(res, list(c(1L, 2L), 3L))
})

