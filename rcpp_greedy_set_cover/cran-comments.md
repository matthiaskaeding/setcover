## Test environments
* local macOS 14.6 (Apple M1), R 4.3.3

## R CMD check results
0 errors | 1 warning | 1 note

* Warning: On macOS (Apple clang), a compiler warning
  `warning: 'sprintf' is deprecated`
  is emitted from `Rcpp/internal/r_coerce.h`. This originates in upstream
  Rcpp headers, not from code in this package.
* Note: `checking for future file timestamps ... unable to verify current time`
  (local clock issue).
