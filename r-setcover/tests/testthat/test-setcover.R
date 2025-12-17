test_that("setcover solves a simple instance", {
    df <- data.frame(
        set = c("A", "A", "A", "B", "B", "C"),
        element = c(1L, 2L, 3L, 1L, 2L, 2L),
        stringsAsFactors = FALSE
    )

    expect_identical(setcover(df, "set", "element"), "A")
})

test_that("setcover supports each algorithm choice", {
    df <- data.frame(
        set = c("S1", "S1", "S2"),
        element = c(1L, 2L, 3L),
        stringsAsFactors = FALSE
    )
    expected <- c("S1", "S2")

    for (algo in c("greedy-standard", "greedy-bitvec", "greedy-textbook")) {
        expect_identical(setcover(df, "set", "element", algo), expected)
    }
})

test_that("setcover validates that requested columns exist", {
    df <- data.frame(
        good_sets = letters[1:3],
        good_elements = 1:3,
        stringsAsFactors = FALSE
    )

    expect_error(setcover(df, "missing", "good_elements"), "Column 'missing'")
    expect_error(setcover(df, "good_sets", "missing"), "Column 'missing'")
})

test_that("setcover returns empty result for empty data", {
    df <- data.frame(set = character(), element = integer(), stringsAsFactors = FALSE)
    expect_identical(setcover(df, "set", "element"), character())
})
