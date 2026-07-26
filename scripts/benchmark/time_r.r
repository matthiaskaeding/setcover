library(data.table)
library(RcppGreedySetCover)

args <- commandArgs(trailingOnly = TRUE)
data_path <- if (length(args) >= 1) args[1] else "scripts/benchmark/data.csv"
which_fn <- if (length(args) >= 2) args[2] else "pairs"

pkg_version <- as.character(packageVersion("RcppGreedySetCover"))

cat(sprintf("Reading data from %s\n", data_path))
cat(sprintf("RcppGreedySetCover %s\n", pkg_version))
df <- fread(data_path)

# The published baseline is greedySetCover(), the only function CRAN 0.1.0
# exports -- hence the default here. It returns one row per element, whereas
# the Python package returns one row per chosen set, so this is not a
# like-for-like comparison; see docs/benchmarks.md.
#
# "setcover" times this repo's newer entry point instead, which does not exist
# in the released package. One function per process either way: running both in
# sequence gives the second a warm page cache.
des_len <- 100
header <- "-Results R"
cat(header, strrep("-", des_len - nchar(header)), "\n", sep = "")

if (which_fn == "setcover") {
  if (!"setcover" %in% getNamespaceExports("RcppGreedySetCover")) {
    stop("setcover() is not exported by RcppGreedySetCover ", pkg_version)
  }
  start <- Sys.time()
  res <- RcppGreedySetCover::setcover(df)
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
