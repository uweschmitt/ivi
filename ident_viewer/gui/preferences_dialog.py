from preferences_dialog_ui import QtGui, QtCore, Ui_PreferencesDialog

class PreferencesDialog(QtGui.QDialog, Ui_PreferencesDialog):
    def __init__(self, preferences, parent=None, f=QtCore.Qt.WindowFlags()):
        QtGui.QDialog.__init__(self, parent, f)

        self.setupUi(self)
        self.connect_signals()
        self.set_preferences(preferences)

    def connect_signals(self):
        self.add_isotopes.toggled.connect(self.max_isotope.setEnabled)

    def set_preferences(self, preferences):
        self.show_a_ion.setChecked(preferences.get("show_a_ion"))
        self.show_b_ion.setChecked(preferences.get("show_b_ion"))
        self.show_c_ion.setChecked(preferences.get("show_c_ion"))
        self.show_x_ion.setChecked(preferences.get("show_x_ion"))
        self.show_y_ion.setChecked(preferences.get("show_y_ion"))
        self.show_z_ion.setChecked(preferences.get("show_z_ion"))
        self.tolerance.setText("%.5f" % preferences.get("tolerance"))

        self.add_losses.setChecked(preferences.get("add_losses"))
        self.max_isotope.setValue(preferences.get("max_isotope"))
        self.max_isotope.setEnabled(preferences.get("add_isotopes"))

        self.add_isotopes.setChecked(preferences.get("add_isotopes"))

    def get_preferences(self):
        return dict(show_a_ion=self.show_a_ion.isChecked(),
                    show_b_ion=self.show_b_ion.isChecked(),
                    show_c_ion=self.show_c_ion.isChecked(),
                    show_x_ion=self.show_x_ion.isChecked(),
                    show_y_ion=self.show_y_ion.isChecked(),
                    show_z_ion=self.show_z_ion.isChecked(),
                    add_isotopes=self.add_isotopes.isChecked(),
                    add_losses=self.add_losses.isChecked(),
                    max_isotope=self.max_isotope.value(),
                    tolerance=float(self.tolerance.text()))

    def accept(self):
        ok, message = self.check_input()
        if ok:
            super(PreferencesDialog, self).accept()
        else:
            box = QtGui.QMessageBox(self)
            box.setText(message)
            box.exec_()

    def check_input(self):
        try:
            float(self.tolerance.text())
        except ValueError:
            return False, "tolerance is not a valid float"
        return True, ""


