from PyQt4 import QtGui, QtCore
from ivi_ui import MainWindow

from peptide_hit_model import PeptideHitModel


def connect(source, signal, slot):
    QtCore.QObject.connect(source, signal, slot)


class IdentViewer(MainWindow):

    def __init__(self, peptide_identifications, protein_identifications, *peakmaps):
        super(IdentViewer, self).__init__()

        self.peptide_identifications = peptide_identifications
        self.protein_identifications = protein_identifications
        self.peakmaps = peakmaps

        self.setup()
        self.connect_signals()

    def setup(self):
        self.peptide_hit_model = PeptideHitModel(self,
                                                 self.peakmaps,
                                                 self.peptide_identifications,
                                                 self.protein_identifications)

        self.peptide_hits.setModel(self.peptide_hit_model)

    def connect_signals(self):
        connect(self.peptide_hits.verticalHeader(), QtCore.SIGNAL("sectionClicked(int)"), self.spectrum_plotter.update)

if __name__ == '__main__':

    import sys
    app = QtGui.QApplication(sys.argv)
    window = IdentViewer()
    window.show()
    sys.exit(app.exec_())
