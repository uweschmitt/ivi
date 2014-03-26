cimport cython
cimport numpy as np
import numpy as np

from libc.stdlib cimport malloc, free, calloc


@cython.boundscheck(False)
@cython.wraparound(False)
@cython.cdivision(True)
def sample_image(peak_map, double rtmin, double rtmax, double mzmin, double mzmax, size_t w,
                 size_t h, int ms_level):

    # avoid zero division later
    assert mzmax >= mzmin, "mzmax < mzmin"
    assert rtmax >= rtmin, "rtmax < rtmin"

    cdef np.ndarray img = np.zeros((h, w), dtype=np.float64)
    cdef np.float64_t[:, :] img_view = img
    cdef size_t rt_bin
    cdef float rt, mz
    cdef size_t n, i, j, mz_bin
    cdef np.float64_t[:] mzs
    cdef np.float32_t[:] intensities

    cdef list spectra = peak_map.spectra
    cdef size_t ns = len(spectra)

    for i in range(ns):
        spec = spectra[i]
        rt = spec.rt
        if rt < rtmin:
            continue
        if rt > rtmax:
            break
        if spec.ms_level != ms_level:
            continue
        rt_bin = int((rt - rtmin) / (rtmax - rtmin) * (w - 1))
        mzs = spec.mzs
        intensities = spec.intensities
        n = mzs.shape[0]
        for j in range(n):
            mz = mzs[j]
            if mzmin <= mz and mz <= mzmax:
                mz_bin = int((mz - mzmin) / (mzmax - mzmin) * (h - 1))
                img_view[mz_bin, rt_bin] += intensities[j]
    return img
