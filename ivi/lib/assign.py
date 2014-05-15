import pyopenms as oms
import re

from data_structures import Hit, Spectrum, Precursor


class PeptideHitAssigner(object):

    def __init__(self, preferences):
        self.preferences = preferences

    def compute_assignment(self, hit, spectrum):
        assert isinstance(hit, Hit)
        assert isinstance(spectrum, Spectrum)

        theoretical_rich_spectrum = self._compute_theoretical_spectrum(hit)
        alignment = self._compute_alignment(spectrum.to_oms_spectrum(), theoretical_rich_spectrum)

        assignment = []

        for (i, j) in alignment:
            ion_name = theoretical_rich_spectrum[j].getMetaValue("IonName")
            residue_info = self._residue_info(ion_name, hit)
            assignment.append((spectrum.mzs[i], spectrum.intensities[i], ion_name, residue_info))

        return assignment

    def _compute_theoretical_spectrum(self, hit):

        aa_sequence = oms.AASequence(hit.aa_sequence)

        generator = self._setup_spectrum_generator()

        result_spec = oms.RichPeakSpectrum()
        max_charge = max(1, hit.charge)

        ResType = oms.Residue.ResidueType

        for charge in range(1, max_charge + 1):
            if self.preferences.get("show_a_ion"):
                generator.addPeaks(result_spec, aa_sequence, ResType.AIon, charge)
            if self.preferences.get("show_b_ion"):
                generator.addPeaks(result_spec, aa_sequence, ResType.BIon, charge)
            if self.preferences.get("show_c_ion"):
                generator.addPeaks(result_spec, aa_sequence, ResType.CIon, charge)
            if self.preferences.get("show_x_ion"):
                generator.addPeaks(result_spec, aa_sequence, ResType.XIon, charge)
            if self.preferences.get("show_y_ion"):
                generator.addPeaks(result_spec, aa_sequence, ResType.YIon, charge)
            if self.preferences.get("show_z_ion"):
                generator.addPeaks(result_spec, aa_sequence, ResType.ZIon, charge)
            generator.addPrecursorPeaks(result_spec, aa_sequence, charge)

        return result_spec

    def _compute_alignment(self, oms_spec1, oms_spec2):
        aligner = self._setup_aligner()
        indices = []
        aligner.getSpectrumAlignment(indices, oms_spec1, oms_spec2)
        return indices

    def _residue_info(self, ion_name, hit):
        aa_sequence = oms.AASequence(hit.aa_sequence)
        if ion_name.startswith("y"):
            ion_nr_str = ion_name.replace("y", "").replace("+", "")
            ion_nr_str, __, __ = ion_nr_str.partition("-")
            ion_number = int(ion_nr_str)
            info = []
            # ion residue for y is reverted:
            for j in range(aa_sequence.size() - 1, aa_sequence.size() - ion_number - 1, -1):
                r = aa_sequence.getResidue(j)
                info.append(r.getOneLetterCode())
                if r.getModification() != "":
                    info.append("*")
            return "".join(info)
        elif ion_name.startswith("b"):
            ion_nr_str = ion_name.replace("b", "").replace("+", "")
            ion_nr_str, __, __ = ion_nr_str.partition("-")
            ion_number = int(ion_nr_str)
            sub_seq = aa_sequence.getSubsequence(0, ion_number).toString()
            return re.sub("[(].*[)]", "*", sub_seq)  # replaces "(Modification)" to "*"
        else:
            return None

    def _setup_spectrum_generator(self):
        generator = oms.TheoreticalSpectrumGenerator()

        params = generator.getDefaults()
        params["add_metainfo"] = "true"

        # bool param values -> str, overwrite defaults if given
        for name in ("add_losses", "add_isotopes"):
            default = 1 if params[name] == "true" else 0
            value = "true" if self.preferences.get(name, default) else "false"
            params[name] = value

        # other param values  overwrite defaults if given:
        for name in ("max_isotope", "relative_loss_intensity"):
            params[name] = self.preferences.get(name, params[name])

        generator.setParameters(params)
        return generator

    def _setup_aligner(self):
        aligner = oms.SpectrumAlignment()

        params = aligner.getDefaults()
        tolerance = self.preferences.get("ms2_tolerance")
        unit = self.preferences.get("ms2_unit")
        params["tolerance"] = tolerance
        params["is_relative_tolerance"] = "true" if unit == "ppm" else "false"
        aligner.setParameters(params)
        return aligner
