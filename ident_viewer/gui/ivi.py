import sys

from PyQt4 import QtGui, QtCore

from ivi_ui import MainWindow
from preferences_dialog import PreferencesDialog

from peptide_hit_model import PeptideHitModel

from tree_model import TreeModel

from ..lib import default_preferences


class IdentViewer(MainWindow):

    def __init__(self, reader):
        super(IdentViewer, self).__init__()
        # fix mac
        if sys.platform == "darwin":
            self.menubar.setNativeMenuBar(False)
        self.reader = reader
        self.setup()
        self.connect_signals()

    def setup(self):
        self.preferences = default_preferences()

        self.tree_model = TreeModel(self.reader)
        self.tree_model.set_preferences(self.preferences)
        self.tree_view.setModel(self.tree_model)
        self.setup_tree_view_size()

    def setup_tree_view_size(self):
        self.tree_view.setMinimumWidth(400)
        self.tree_view.setColumnWidth(0, 200)
        self.tree_view.resizeColumnToContents(1)
        self.tree_view.resizeColumnToContents(2)
        self.tree_view.resizeColumnToContents(3)

    def connect_signals(self):
        self.tree_view.clicked.connect(self.tree_model.select)

        self.tree_model.spectrumSelected.connect(self.spectrum_plotter.plot_spectrum)

        self.tree_model.featureSelected.connect(self.peakmap_plotter.plot_feature)
        self.tree_model.featureSelected.connect(self.chromatogram_plotter.plot_chromatograms_from_feature)

        self.tree_model.massTraceSelected.connect(self.peakmap_plotter.plot_mass_trace)
        self.tree_model.massTraceSelected.connect(self.chromatogram_plotter.plot_chromatogram_from_masstrace)

        self.tree_model.ms1HitChanged.connect(self.peakmap_plotter.clear)
        self.tree_model.ms1HitChanged.connect(self.chromatogram_plotter.clear)

        self.tree_model.ms2HitChanged.connect(self.spectrum_plotter.clear)

        self.tree_model.newHitRt.connect(self.chromatogram_plotter.set_rt_marker)

        self.chromatogram_plotter.rtCursorMoved.connect(self.peakmap_plotter.move_marker_to_rt)
        self.peakmap_plotter.cursorMoved.connect(self.chromatogram_plotter.move_marker)

    def row_chosen(self, i):
        self.tree_view.selectRow(i)

    def edit_preferences(self):
        dlg = PreferencesDialog(self.preferences, parent=self)
        closed_as = dlg.exec_()
        if closed_as == QtGui.QDialog.Accepted:
            self.preferences = dlg.get_preferences()
            self.tree_model.set_preferences(self.preferences)

    def open_file(self):
        pass


if __name__ == '__main__':
    from PyQt4.QtCore import Qt

    import sys
    app = QtGui.QApplication(sys.argv)
    window = IdentViewer()
    window.show()
    window.raise_()
    window.setWindowState(Qt.WindowActive)
    sys.exit(app.exec_())
