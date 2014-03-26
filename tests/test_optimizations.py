from ident_viewer.lib.data_structures import Spectrum, PeakMap
from ident_viewer.optimizations import sample_image
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
