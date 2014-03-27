from collections import namedtuple

from ..optimizations import get_ranges as optimized_get_ranges

Hit = namedtuple("Hit", "id_, aa_sequence, base_name, mz, rt, score, is_higher_score_better")
Precursor = namedtuple("Precursor", "mz")
Chromatogram = namedtuple("Chromatogram", "rts, ion_counts")
ConvexHull = namedtuple("ConvexHull", "rt_min, rt_max, mz_min, mz_max")


class PeakMap(namedtuple("PeakMap", "spectra")):

    def get_ranges(self):
        return optimized_get_ranges(self)


class Spectrum(namedtuple("Spectrum", "rt, mzs, intensities, precursors, ms_level")):

    def cleaned(self):
        mask = (self.intensities > 0.0)
        mzs = self.mzs[mask]
        intensities = self.intensities[mask]
        return self.__class__(self.rt, mzs, intensities, self.precursors, self.ms_level)
