library(data.table)
library(RcppGreedySetCover)

args <- commandArgs(trailingOnly = TRUE)
data_path <- if (length(args) >= 1) args[1] else "scripts/benchmark/data.csv"

cat(sprintf("Reading data from %s\n", data_path))

start_load <- Sys.time()
df <- fread(data_path)
load_time <- Sys.time() - start_load

start_algo <- Sys.time()
res <- greedySetCover(df)
algo_time <- Sys.time() - start_algo

des_len <- 100
header <- "-Results R"
cat(header, strrep("-", des_len - nchar(header)), "\n", sep = "")
cat("greedy\n")
cat(sprintf("Cover: %d sets\n", length(unique(res$set))))
cat(sprintf("Time:  %.1f seconds\n", as.numeric(algo_time)))
