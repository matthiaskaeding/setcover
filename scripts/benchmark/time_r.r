library(data.table)
library(RcppGreedySetCover)

args <- commandArgs(trailingOnly = TRUE)
data_path <- if (length(args) >= 1) args[1] else "scripts/benchmark/data.csv"
which_fn <- if (length(args) >= 2) args[2] else "setcover"

cat(sprintf("Reading data from %s\n", data_path))
df <- fread(data_path)

# One function per process: running both in sequence gives the second one a
# warm page cache and understates it by ~15%.
#
# setcover() is the like-for-like comparison against the Python package -- both
# return one row per chosen set. greedySetCover() returns one row per element,
# so it does strictly more work and is reported separately, not compared.
des_len <- 100
header <- "-Results R"
cat(header, strrep("-", des_len - nchar(header)), "\n", sep = "")

if (which_fn == "setcover") {
  start <- Sys.time()
  res <- setcover(df)
  elapsed <- Sys.time() - start
  cat("setcover (labels + gains)\n")
  cat(sprintf("Cover: %d sets\n", nrow(res)))
} else {
  start <- Sys.time()
  res <- greedySetCover(df)
  elapsed <- Sys.time() - start
  cat("greedySetCover (set/element pairs)\n")
  cat(sprintf("Cover: %d sets\n", length(unique(res$set))))
}

cat(sprintf("Time:  %.1f seconds\n", as.numeric(elapsed, units = "secs")))
