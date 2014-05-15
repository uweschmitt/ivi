cimport cython
from libc.float cimport DBL_MAX
cimport libc.math
cimport numpy as np
import numpy as np

from libc.stdlib cimport malloc, free, calloc


@cython.boundscheck(False)
@cython.wraparound(False)
@cython.cdivision(True)
def find_chromatogram_rt_limits(peak_map, float rt_start, double mzmin, double mzmax,
                                int ms_level, int n_conscutive_zeros):

    cdef list spectra = peak_map.spectra

    # find start i0 where rt_start matches best
    cdef size_t i0 = find_next(spectra, rt_start, ms_level)
    # extend rt upwards
    cdef float rtmax = march(spectra, i0, +1, n_conscutive_zeros, mzmin, mzmax, ms_level)
    # extend rt downwards
    cdef float rtmin = march(spectra, i0, -1, n_conscutive_zeros, mzmin, mzmax, ms_level)
    return rtmin, rtmax


@cython.boundscheck(False)
@cython.wraparound(False)
@cython.cdivision(True)
cdef size_t find_next(list spectra, float rt0, int ms_level):
    cdef size_t i
    cdef int  msl
    cdef float dist
    cdef float best_dist = 9999999.0
    cdef float rt
    cdef size_t best_i = 0
    cdef size_t ns = len(spectra)

    for i in range(ns):
        spec = spectra[i]
        msl = spec.ms_level   # prohibits python rich comp in next line
        if msl != ms_level:
            continue
        rt = spec.rt          # prohibits python substration in next line
        dist = libc.math.fabs(rt - rt0)
        if dist < best_dist:
            best_i = i
            best_dist = dist
    return best_i


@cython.boundscheck(False)
@cython.wraparound(False)
@cython.cdivision(True)
cdef float march(list spectra, size_t i0, int direction, int n_conscutive_zeros, float mzmin,
                 float mzmax, int ms_level):

    cdef float rt
    cdef float sumi
    cdef int msl
    cdef size_t ns = len(spectra)
    cdef size_t count_zeros = 0
    while 0 <= i0 < ns:
        spec = spectra[i0]
        i0 += direction
        msl = spec.ms_level   # prohibits python rich comp in next line
        if msl != ms_level:
            continue
        rt = spec.rt

        sumi = intensity(spec.mzs, spec.intensities, mzmin, mzmax)
        if sumi == 0.0:
            count_zeros += 1
        else:
            count_zeros = 0
        if count_zeros >= n_conscutive_zeros:
            break

    return rt


@cython.boundscheck(False)
@cython.wraparound(False)
@cython.cdivision(True)
cdef float intensity(np.float64_t[:] mzs,  np.float32_t[:] intensities, float mzmin, float mzmax):
    cdef float sumi = 0.0
    cdef int   ns = mzs.shape[0]
    cdef int   i
    for i in range(0, ns):
        if mzmin <= mzs[i] <= mzmax:
            sumi += intensities[i]
    return sumi


@cython.boundscheck(False)
@cython.wraparound(False)
@cython.cdivision(True)
def extract_chromatogram(peak_map, float rtmin, float rtmax, double mzmin, double mzmax,
                         int ms_level):

    assert mzmax >= mzmin, "mzmax < mzmin"
    assert rtmax >= rtmin, "rtmax < rtmin"

    cdef np.float64_t[:] mzs
    cdef np.float32_t[:] intensities

    cdef list spectra = peak_map.spectra
    cdef size_t ns = len(spectra)

    cdef size_t nt, i, j, k, n
    cdef float ii, rt
    cdef double mz

    cdef int smsl

    nt = 0
    for i in range(ns):
        spec = spectra[i]
        rt = spec.rt
        if rtmin <= rt <= rtmax:
            smsl = spec.ms_level   # prohibits python rich comp in next line
            if smsl == ms_level:
                nt += 1

    cdef np.ndarray rts = np.zeros((nt,), dtype=np.float32)
    cdef np.ndarray iis = np.zeros((nt,), dtype=np.float32)

    cdef np.float32_t[:] rts_view = rts
    cdef np.float32_t[:] iis_view = iis

    j = 0
    for i in range(ns):
        spec = spectra[i]
        rt = spec.rt
        if rtmin <= rt <= rtmax:
            smsl = spec.ms_level   # prohibits python rich comp in next line
            # print i, j, rt, smsl
            if smsl == ms_level:
                mzs = spec.mzs
                intensities = spec.intensities
                ii = 0.0
                n = mzs.shape[0]
                for k in range(n):
                    mz = mzs[k]
                    if mzmin <= mz and mz <= mzmax:
                        ii += intensities[k]
                rts_view[j] = rt
                iis_view[j] = ii
                j += 1

    return rts, iis


@cython.boundscheck(False)
@cython.wraparound(False)
@cython.cdivision(True)
def sample_image(peak_map, float rtmin, float rtmax, double mzmin, double mzmax, size_t w,
                 size_t h, int ms_level):

    # avoid zero division later
    assert mzmax >= mzmin, "mzmax < mzmin"
    assert rtmax >= rtmin, "rtmax < rtmin"

    cdef np.ndarray img = np.zeros((h, w), dtype=np.float32)
    cdef np.float32_t[:, :] img_view = img
    cdef size_t rt_bin
    cdef float rt
    cdef double mz
    cdef size_t n, i, j, mz_bin
    cdef np.float64_t[:] mzs
    cdef np.float32_t[:] intensities

    cdef list spectra = peak_map.spectra
    cdef size_t ns = len(spectra)
    cdef int smsl

    for i in range(ns):
        spec = spectra[i]
        rt = spec.rt
        if rt < rtmin:
            continue
        if rt > rtmax:
            break
        smsl = spec.ms_level   # prohibits python rich comp in next line
        if smsl != ms_level:
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


@cython.boundscheck(False)
@cython.wraparound(False)
@cython.cdivision(True)
def get_ranges(peak_map, int ms_level):
    cdef list spectra = peak_map.spectra
    cdef int n = len(spectra)

    cdef object spectrum
    cdef double rtmin, rtmax, mzmin, mzmax, rt, iimin, iimax
    cdef np_min = np.min
    cdef np_max = np.max
    cdef np.float64_t[:] mzs
    cdef np.float32_t[:] iis
    cdef int found_spec = 0
    cdef int smsl

    rtmax = -DBL_MAX
    rtmin = +DBL_MAX
    mzmax = -DBL_MAX
    mzmin = +DBL_MAX
    iimax = -DBL_MAX
    iimin = +DBL_MAX

    for i in range(n):
        spectrum = spectra[i]
        smsl = spectrum.ms_level
        if smsl == ms_level:
            found_spec = 1
            mzs = spectrum.mzs
            iis = spectrum.intensities
            rt = spectrum.rt
            rtmin = min(rt, rtmin)
            rtmax = max(rt, rtmin)
            mzmin = min(mzmin, np_min(mzs))
            mzmax = max(mzmax, np_max(mzs))
            iimin = min(iimin, np_min(iis))
            iimax = max(iimax, np_max(iis))
    if found_spec:
        return rtmin, rtmax, mzmin, mzmax, iimin, iimax
    return None, None, None, None, None, None
