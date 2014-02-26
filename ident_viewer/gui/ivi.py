from PyQt4 import QtGui, QtCore
from ivi_ui import MainWindow
from preferences_dialog import PreferencesDialog

from peptide_hit_model import PeptideHitModel

from ..lib import default_preferences


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

        self.preferences = default_preferences()
        self.peptide_hits.setModel(self.peptide_hit_model)
        self.peptide_hit_model.set_preferences(self.preferences)
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
        self.peptide_hits.verticalHeader().sectionClicked.connect(self.row_chosen)
        self.peptide_hits.verticalHeader().sectionClicked.connect(self.peptide_hit_model.select)
        self.peptide_hit_model.peptideSelected.connect(self.spectrum_plotter.plot_hit)

        self.action_preferences.triggered.connect(self.edit_preferences)
        self.action_open_file.triggered.connect(self.open_file)

    def row_chosen(self, i):
        self.peptide_hits.selectRow(i)

    def edit_preferences(self):
        dlg = PreferencesDialog(self.preferences, parent=self)
        closed_as = dlg.exec_()
        if closed_as == QtGui.QDialog.Accepted:
            self.preferences = dlg.get_preferences()
            self.peptide_hit_model.set_preferences(self.preferences)

    def open_file(self):
        pass




if __name__ == '__main__':

    import sys
    app = QtGui.QApplication(sys.argv)
    window = IdentViewer()
    window.show()
    sys.exit(app.exec_())
