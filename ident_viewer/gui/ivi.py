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
        self.setup_table_view_size()

    def setup_table_view_size(self):

        ph = self.peptide_hits
        # set table with so that full content fits
        vwidth = ph.verticalHeader().width()
        hwidth = ph.horizontalHeader().length()
        swidth = ph.style().pixelMetric(QtGui.QStyle.PM_ScrollBarExtent)
        fwidth = ph.frameWidth() * 2
        self.peptide_hits.setMinimumWidth(vwidth + hwidth + swidth + fwidth + 10)
        self.peptide_hits.setMaximumWidth(vwidth + hwidth + swidth + fwidth + 300)

    def connect_signals(self):
        self.peptide_hits.verticalHeader().sectionClicked.connect(self.peptide_hit_model.select)
        self.peptide_hit_model.peptideSelected.connect(self.spectrum_plotter.plot_spectrum)


if __name__ == '__main__':

    import sys
    app = QtGui.QApplication(sys.argv)
    window = IdentViewer()
    window.show()
    sys.exit(app.exec_())
