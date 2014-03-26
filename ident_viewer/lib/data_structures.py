from collections import namedtuple

Hit = namedtuple("Hit", "id_, aa_sequence, base_name, mz, rt, score, is_higher_score_better")
Precursor = namedtuple("Precursor", "mz")
Spectrum = namedtuple("Spectrum", "rt, mzs, intensities, precursors, ms_level")
Chromatogram = namedtuple("Chromatogram", "rts, ion_counts")
PeakMap = namedtuple("PeakMap", "spectra")
ConvexHull = namedtuple("ConvexHull", "rt_min, rt_max, mz_min, mz_max")
