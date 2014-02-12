import pyopenms as oms
import re


class PeptideHitAssigner(object):


    def __init__(self, assign_b_ion=True, assign_y_ion=True, **config):
        self.config = dict(assign_b_ion=assign_b_ion,
                           assign_y_ion=assign_y_ion)
        self.config.update(config)

    def compute_assignment(self, peptide_hit, spectrum):

        aa_sequence = peptide_hit.getSequence()
        if not aa_sequence.isValid():
            return []

        theoretical_spectrum = self._compute_theoretical_spectrum(peptide_hit, aa_sequence)
        alignment = self._compute_alignment(spectrum, theoretical_spectrum)

        assignment = []

        for (i, j) in alignment:
            ion_name = theoretical_spectrum[j].getMetaValue("IonName")
            residue_info = self._residue_info(ion_name, aa_sequence)
            assignment.append((spectrum[i].getMZ(), spectrum[i].getIntensity(), ion_name,
                residue_info))

        return assignment

    def _compute_theoretical_spectrum(self, peptide_hit, aa_sequence):

        generator = self._setup_spectrum_generator()

        theoretical_spectrum = oms.RichPeakSpectrum()
        max_charge = max(1, peptide_hit.getCharge())

        for charge in range(1, max_charge + 1):
            if self.config.get("assign_a_ion"):
                generator.addPeaks(theoretical_spectrum, aa_sequence, oms.ResidueType.AIon, charge)
            if self.config.get("assign_b_ion"):
                generator.addPeaks(theoretical_spectrum, aa_sequence, oms.ResidueType.BIon, charge)
            if self.config.get("assign_c_ion"):
                generator.addPeaks(theoretical_spectrum, aa_sequence, oms.ResidueType.CIon, charge)
            if self.config.get("assign_x_ion"):
                generator.addPeaks(theoretical_spectrum, aa_sequence, oms.ResidueType.XIon, charge)
            if self.config.get("assign_y_ion"):
                generator.addPeaks(theoretical_spectrum, aa_sequence, oms.ResidueType.YIon, charge)
            if self.config.get("assign_z_ion"):
                generator.addPeaks(theoretical_spectrum, aa_sequence, oms.ResidueType.ZIon, charge)
            generator.addPrecursorPeaks(theoretical_spectrum, aa_sequence, charge)

        return theoretical_spectrum

    def _compute_alignment(self, spec1, spec2):
        aligner = self._setup_aligner()
        indices = []
        aligner.getSpectrumAlignment(indices, spec1, spec2)
        return indices

    def _residue_info(self, ion_name, aa_sequence):

        if ion_name.startswith("y"):
            ion_nr_str = ion_name.replace("y", "").replace("+", "")
            ion_number = int(ion_nr_str)
            info = []
            # ion residue for y is reverted:
            for j in range(aa_sequence.size()-1, aa_sequence.size() - ion_number - 1, -1):
                r = aa_sequence.getResidue(j)
                info.append(r.getOneLetterCode())
                if r.getModification() != "":
                    info.append("*")
            return "".join(info)
        elif ion_name.startswith("b"):
            ion_nr_str = ion_name.replace("b", "").replace("+", "")
            ion_number = int(ion_nr_str)
            sub_seq = aa_sequence.getSubsequence(0, ion_number).toString()
            return re.sub("[(].*[)]", "*", sub_seq)  # replaces "(Modification)" to "*"
        else:
            return None

    def _setup_spectrum_generator(self):
        generator = oms.TheoreticalSpectrumGenerator()

        params = generator.getDefaults()
        params["add_metainfo"] = "true"

        # overwrite defaults if given:
        for name in ("max_isotope", "add_losses", "add_isotopes", "relative_loss_intensity"):
            params[name] = self.config.get(name, params[name])

        generator.setParameters(params)
        return generator

    def _setup_aligner(self):
        aligner = oms.SpectrumAlignment()

        params = aligner.getDefaults()
        tolerance = 3e-1
        params["tolerance"] = tolerance
        aligner.setParameters(params)
        return aligner


def main():
    protein_ids = []
    peptide_ids = []

    oms.IdXMLFile().load("BSA1_OMSSA.idXML", protein_ids, peptide_ids)

    mse = oms.MSExperiment()
    oms.FileHandler().loadExperiment("BSA1.mzML", mse)

    mapper = oms.IDMapper()
    mapper.annotate(mse, peptide_ids, protein_ids)

    for s in mse.getSpectra():
        if s.getMSLevel() == 2 and s.getPeptideIdentifications():
            pi = s.getPeptideIdentifications()[0]
            print pi.getMetaValue("MZ")
            peptide_hit = pi.getHits()[0]
            break
    else:
        raise Exception("no hit found")

    print peptide_hit.getSequence().toString()
    for mz, ii, ion, info in  PeptideHitAssigner().compute_assignment(peptide_hit, s):
        print "%10.5f" % mz, "%e" % ii, "%-10s" % ion, info

if __name__ == "__main__":
    main()



