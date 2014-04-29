from PyQt4 import QtGui, QtCore
from ivi_ui import MainWindow
from preferences_dialog import PreferencesDialog

from peptide_hit_model import PeptideHitModel

from tree_model import TreeModel

from ..lib import default_preferences


class IdentViewer(MainWindow):

    def __init__(self, reader):
        super(IdentViewer, self).__init__()
        self.reader = reader
        self.setup()
        self.connect_signals()

    def setup(self):
        self.preferences = default_preferences()
        self.setup_tree_view_size()

        self.tree_model = TreeModel(self.reader)
        self.tree_model.set_preferences(self.preferences)
        self.peptide_hits.setModel(self.tree_model)

    def setup_tree_view_size(self):
        self.peptide_hits.setMinimumWidth(400)

    def connect_signals(self):
        # self.peptide_hits.verticalHeader().sectionClicked.connect(self.row_chosen)
        # self.peptide_hits.verticalHeader().sectionClicked.connect(self.tree_model.select)
        # self.tree_model.peptideSelected.connect(self.spectrum_plotter.plot_hit)
        self.action_preferences.triggered.connect(self.edit_preferences)
        self.action_open_file.triggered.connect(self.open_file)

    def row_chosen(self, i):
        self.peptide_hits.selectRow(i)

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
