from collections import namedtuple
import pyopenms as oms

from .. import optimizations

Hit = namedtuple("Hit", "id_, aa_sequence, base_name, mz, rt, charge, score, is_higher_score_better")
Precursor = namedtuple("Precursor", "mz")
Chromatogram = namedtuple("Chromatogram", "rts, ion_counts")
ConvexHull = namedtuple("ConvexHull", "rt_min, rt_max, mz_min, mz_max")


class PeakMap(namedtuple("PeakMap", "spectra")):

    def get_ranges(self, ms_level=1):
        return optimizations.get_ranges(self, ms_level)

    def sample_image(self, rt_min, rt_max, mz_min, mz_max, w, h, ms_level):
        return optimizations.sample_image(self, rt_min, rt_max, mz_min, mz_max, w, h, ms_level)


class Spectrum(namedtuple("Spectrum", "rt, mzs, intensities, precursors, ms_level")):

    def cleaned(self):
        mask = (self.intensities > 0.0)
        mzs = self.mzs[mask]
        intensities = self.intensities[mask]
        return self.__class__(self.rt, mzs, intensities, self.precursors, self.ms_level)

    def as_oms_spectrum(self):
        spec = oms.MSSpectrum()
        spec.setRT(self.rt)
        spec.set_peaks((self.mzs, self.intensities))
        spec.setMSLevel(self.ms_level)
        oms_pcs = []
        for precursor in self.precursors:
            oms_pc = oms.Precursor()
            oms_pc.setMZ(precursor.mz)
            oms_pcs.append(oms_pc)
        spec.setPrecursors(oms_pcs)
        return spec

    @classmethod
    def from_oms_spectrum(clz, spec):
        mzs, intensities = spec.get_peaks()
        precursors = [Precursor(pc.getMZ()) for pc in spec.getPrecursors()]
        return clz(spec.getRT(), mzs, intensities, precursors, spec.getMSLevel())

