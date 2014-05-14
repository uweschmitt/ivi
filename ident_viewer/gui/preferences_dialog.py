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

        if preferences.get("ms2_tolerance_unit") == "Da":
            self.ms2_tolerance.setText("%.5f" % preferences.get("ms2_tolerance"))
            self.ms2_tolerance_unit_is_da.setChecked(1)
            self.ms2_tolerance_unit_is_ppm.setChecked(0)
        else:
            self.ms2_tolerance.setText("%.0f" % preferences.get("ms2_tolerance"))
            self.ms2_tolerance_unit_is_da.setChecked(0)
            self.ms2_tolerance_unit_is_ppm.setChecked(1)

        if preferences.get("ms1_tolerance_unit") == "Da":
            self.ms1_tolerance.setText("%.5f" % preferences.get("ms1_tolerance"))
            self.ms1_tolerance_unit_is_da.setChecked(1)
            self.ms1_tolerance_unit_is_ppm.setChecked(0)
        else:
            self.ms1_tolerance.setText("%.0f" % preferences.get("ms1_tolerance"))
            self.ms1_tolerance_unit_is_da.setChecked(0)
            self.ms1_tolerance_unit_is_ppm.setChecked(1)

        self.add_losses.setChecked(preferences.get("add_losses"))
        self.max_isotope.setValue(preferences.get("max_isotope"))
        self.max_isotope.setEnabled(preferences.get("add_isotopes"))

        self.add_isotopes.setChecked(preferences.get("add_isotopes"))

    def get_preferences(self):
        checked_to_str = lambda w: "Da" if w.isChecked() else "ppm"

        return dict(show_a_ion=self.show_a_ion.isChecked(),
                    show_b_ion=self.show_b_ion.isChecked(),
                    show_c_ion=self.show_c_ion.isChecked(),
                    show_x_ion=self.show_x_ion.isChecked(),
                    show_y_ion=self.show_y_ion.isChecked(),
                    show_z_ion=self.show_z_ion.isChecked(),
                    add_isotopes=self.add_isotopes.isChecked(),
                    add_losses=self.add_losses.isChecked(),
                    max_isotope=self.max_isotope.value(),
                    ms1_tolerance=float(self.ms1_tolerance.text()),
                    ms2_tolerance=float(self.ms2_tolerance.text()),
                    ms1_tolerance_unit=checked_to_str(self.ms1_tolerance_unit_is_da),
                    ms2_tolerance_unit=checked_to_str(self.ms2_tolerance_unit_is_da),
                    )

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
            float(self.ms1_tolerance.text())
        except ValueError:
            return False, "ms1 tolerance is not a valid float"
        try:
            float(self.ms2_tolerance.text())
        except ValueError:
            return False, "ms2 tolerance is not a valid float"
        return True, ""


