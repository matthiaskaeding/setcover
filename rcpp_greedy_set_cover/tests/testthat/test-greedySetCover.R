test_that("greedySetCover returns expected coverage", {
    df <- data.frame(
        set = c("A", "A", "B", "B", "C"),
        element = c(1L, 2L, 2L, 3L, 3L),
        stringsAsFactors = FALSE
    )

    result <- greedySetCover(df, data.table = FALSE)

    expect_s3_class(result, "data.frame")
    expect_identical(names(result), c("set", "element"))
    expect_true(all(result$set %in% c("A", "B")))
    expect_identical(sort(unique(result$element)), sort(unique(df$element)))
})

test_that("greedySetCover prints by default and can be silenced", {
    df <- data.frame(
        set = c("A", "A", "B", "B", "C"),
        element = c(1L, 2L, 2L, 3L, 3L),
        stringsAsFactors = FALSE
    )

    expect_output(greedySetCover(df), "covered")
    expect_silent(greedySetCover(df, verbose = FALSE))

    # Silencing must not change the answer.
    loud <- capture.output(res_loud <- greedySetCover(df))
    res_quiet <- greedySetCover(df, verbose = FALSE)
    expect_equal(as.data.frame(res_loud), as.data.frame(res_quiet))
})

test_that("greedySetCover validates two-column inputs", {
    df <- data.frame(set = c("A", "B"), stringsAsFactors = FALSE)
    expect_error(greedySetCover(df), "ncol")
})

test_that("greedySetCover computes a valid cover when several sets are required", {
    df <- data.frame(
        set = c("S1", "S1", "S2", "S2", "S3", "S3", "S4"),
        element = c(1L, 2L, 2L, 3L, 3L, 4L, 5L),
        stringsAsFactors = FALSE
    )

    cover <- greedySetCover(df) # returns data.table by default
    expect_s3_class(cover, "data.table")

    covered_elements <- sort(unique(cover$element))
    universe <- sort(unique(df$element))

    expect_identical(covered_elements, universe)
    expect_true(length(unique(cover$set)) >= 2)
})
