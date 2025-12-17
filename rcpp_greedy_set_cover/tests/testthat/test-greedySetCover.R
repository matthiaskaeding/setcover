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

test_that("greedySetCover validates two-column inputs", {
    df <- data.frame(set = c("A", "B"), stringsAsFactors = FALSE)
    expect_error(greedySetCover(df), "ncol")
})
