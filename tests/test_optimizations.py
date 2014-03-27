from ident_viewer.lib.data_structures import Spectrum, PeakMap
from ident_viewer.optimizations import sample_image, get_ranges
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

    assert get_ranges(PeakMap([]), 1) == (None, ) * 6
    assert get_ranges(pm, 1) == (1.0, 2.0, 1.0, 2.0, 1.0, 2.0)
    assert get_ranges(pm, 2) == (3.0, 3.0, 2.0, 2.0, 2.0, 2.0)
    assert get_ranges(pm, 3) == (None, ) * 6

    pm = PeakMap(spectra[:1])
    assert get_ranges(pm, 1) == (1.0, 1.0, 1.0, 1.0, 1.0, 1.0)
    assert get_ranges(pm, 2) == (None, ) * 6
    assert get_ranges(pm, 3) == (None, ) * 6

    # now test if attached method works too...
    assert pm.get_ranges(1) == (1.0, 1.0, 1.0, 1.0, 1.0, 1.0)
    assert pm.get_ranges(2) == (None, ) * 6
    assert pm.get_ranges(3) == (None, ) * 6
