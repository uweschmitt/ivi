# encoding: latin-1

import pyopenms as oms
import data_structures


def load_idxml_file(path):
    protein_identifations = []
    peptide_identifations = []
    oms.IdXMLFile().load(path, protein_identifations, peptide_identifations)
    return peptide_identifations, protein_identifations


def load_peak_map(path):
    mse = oms.MSExperiment()
    oms.FileHandler().loadExperiment(path, mse)
    spectra = [data_structures.Spectrum.from_oms_spectrum(spec) for spec in mse]
    return data_structures.PeakMap(spectra)
