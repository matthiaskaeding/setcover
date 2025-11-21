#include <R.h>
#include <Rinternals.h>
#include <R_ext/Rdynload.h>

void R_init_rsetcover_extendr(DllInfo *dll);

void R_init_rsetcover(DllInfo *dll) {
    R_init_rsetcover_extendr(dll);
}
