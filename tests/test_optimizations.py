from ident_viewer.lib.data_structures import Spectrum, PeakMap
from ident_viewer.optimizations import (sample_image, get_ranges, find_chromatogram_rt_limits,
                                        extract_chromatogram)
from ident_viewer.lib import load_peak_map
import numpy as np


def test_00():
    spectra = []
    mzs = np.array((1.0, 2.0, 4.0), dtype=np.float64)
    iis = np.array((1.0, 2.0, 4.0), dtype=np.float32)
    spec = Spectrum(1.0, mzs, iis, None, 1)
    spectra.append(spec)
    mzs = np.array((2.0, 3.0, 4.0), dtype=np.float64)
    iis = np.array((2.0, 3.0, 5.0), dtype=np.float32)
    spec = Spectrum(2.0, mzs, iis, None, 1)
    spectra.append(spec)
    spec = Spectrum(3.0, mzs, iis, None, 2)
    spectra.append(spec)

    pm = PeakMap(spectra)

    img = sample_image(pm, 1.0, 1.0, 1.0, 1.0, 1, 1, 1)
    assert img == np.array((1.0,)), img

    img = sample_image(pm, 1.0, 1.0, 1.0, 1.0, 1, 1, 2)
    assert img == np.array((0.0,)), img

    img = sample_image(pm, 1.0, 4.0, 1.0, 5.0, 1, 1, 1)
    assert img == np.array((17.0,)), img

    img = sample_image(pm, 1.0, 2.0, 1.0, 4.0, 2, 2, 1)
    assert np.linalg.norm(np.array(((3, 5), (4, 5))) - img) <= 1e-6

    # now test if attached method works too...
    img = pm.sample_image(1.0, 2.0, 1.0, 4.0, 2, 2, 1)
    assert np.linalg.norm(np.array(((3, 5), (4, 5))) - img) <= 1e-6

    assert get_ranges(PeakMap([]), 1) == (None,) * 6
    assert get_ranges(pm, 1) == (1.0, 2.0, 1.0, 4.0, 1.0, 5.0)
    assert get_ranges(pm, 2) == (3.0, 3.0, 2.0, 4.0, 2.0, 5.0)
    assert get_ranges(pm, 3) == (None,) * 6

    pm = PeakMap(spectra[:1])
    assert get_ranges(pm, 1) == (1.0, 1.0, 1.0, 4.0, 1.0, 4.0)
    assert get_ranges(pm, 2) == (None,) * 6
    assert get_ranges(pm, 3) == (None,) * 6

    # now test if attached method works too...
    assert pm.get_ranges(1) == (1.0, 1.0, 1.0, 4.0, 1.0, 4.0)
    assert pm.get_ranges(2) == (None,) * 6
    assert pm.get_ranges(3) == (None,) * 6


def test_01(data_path):
    pm = load_peak_map(data_path("reduced.mzXML"))
    nmid = len(pm.spectra) / 2
    for s in pm.spectra[nmid:]:
        if s.ms_level == 1:
            break
    ii = np.argmax(s.intensities)
    mzmid = s.mzs[ii]
    mzmin = mzmid - 0.0001
    mzmax = mzmid + 0.0001
    if 0:
        rtmin, rtmax = find_chromatogram_rt_limits(pm, s.rt, mzmin, mzmax, 1, 2)

        assert abs(rtmin - 0.580) < 0.001
        assert abs(rtmax - 290.915) < 0.001

        rts, iis = extract_chromatogram(pm, rtmin, rtmax, mzmin, mzmax, 1)
        assert rts[0] == rtmin
        assert rts[-1] == rtmax
        assert len(rts) == 158
        assert iis[0] > 0.0      # chromo goes back to first spec (because we reduced the orig peakmap)
        assert iis[-1] == 0.0    # but in the end it finds sometghin
        assert iis[-2] == 0.0

    # no we look for a chromatogram in the void:
    mzmin += 7.0
    mzmax += 7.0
    rtmin, rtmax = find_chromatogram_rt_limits(pm, s.rt, mzmin, mzmax, 1, 2)

    assert abs(rtmin - 239.806) < 0.001
    assert abs(rtmax - 243.164) < 0.001

    rts, iis = extract_chromatogram(pm, rtmin, rtmax, mzmin, mzmax, 1)
    assert len(rts) == 3
    assert len(iis) == 3
    assert rts[0] == rtmin
    assert abs(rts[1] - s.rt) < 1e-3   # diff float precision !
    assert rts[2] == rtmax
    assert iis[0] == 0.0
    assert iis[1] == 0.0
    assert iis[2] == 0.0
