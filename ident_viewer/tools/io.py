#encoding: latin-1
import pyopenms as oms


def load_idxml_file(path):
    protein_identifations = []
    peptide_identifations = []
    oms.IdXMLFile().load(path, protein_identifations, peptide_identifations)
    return peptide_identifations, protein_identifations


def load_experiment(path):
    mse = oms.MSExperiment()
    oms.FileHandler().loadExperiment(path, mse)
    return mse
