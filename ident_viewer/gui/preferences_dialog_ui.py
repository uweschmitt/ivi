# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'preferences_dialog.ui'
#
# Created: Wed Feb 26 14:09:31 2014
#      by: PyQt4 UI code generator 4.9.1
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_PreferencesDialog(object):
    def setupUi(self, PreferencesDialog):
        PreferencesDialog.setObjectName(_fromUtf8("PreferencesDialog"))
        PreferencesDialog.resize(310, 208)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(PreferencesDialog.sizePolicy().hasHeightForWidth())
        PreferencesDialog.setSizePolicy(sizePolicy)
        PreferencesDialog.setMaximumSize(QtCore.QSize(310, 208))
        PreferencesDialog.setSizeGripEnabled(False)
        self.gridLayout = QtGui.QGridLayout(PreferencesDialog)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.buttonBox = QtGui.QDialogButtonBox(PreferencesDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.buttonBox.sizePolicy().hasHeightForWidth())
        self.buttonBox.setSizePolicy(sizePolicy)
        self.buttonBox.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setCenterButtons(False)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 1, 0, 1, 1)
        self.frame = QtGui.QFrame(PreferencesDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frame.sizePolicy().hasHeightForWidth())
        self.frame.setSizePolicy(sizePolicy)
        self.frame.setFrameShape(QtGui.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtGui.QFrame.Raised)
        self.frame.setObjectName(_fromUtf8("frame"))
        self.gridLayout_2 = QtGui.QGridLayout(self.frame)
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        self.label_4 = QtGui.QLabel(self.frame)
        self.label_4.setObjectName(_fromUtf8("label_4"))
        self.gridLayout_2.addWidget(self.label_4, 3, 0, 1, 1)
        self.tolerance = QtGui.QLineEdit(self.frame)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tolerance.sizePolicy().hasHeightForWidth())
        self.tolerance.setSizePolicy(sizePolicy)
        self.tolerance.setObjectName(_fromUtf8("tolerance"))
        self.gridLayout_2.addWidget(self.tolerance, 0, 1, 1, 1)
        self.frame_2 = QtGui.QFrame(self.frame)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.frame_2.sizePolicy().hasHeightForWidth())
        self.frame_2.setSizePolicy(sizePolicy)
        self.frame_2.setFrameShape(QtGui.QFrame.StyledPanel)
        self.frame_2.setFrameShadow(QtGui.QFrame.Raised)
        self.frame_2.setObjectName(_fromUtf8("frame_2"))
        self.formLayout = QtGui.QFormLayout(self.frame_2)
        self.formLayout.setFieldGrowthPolicy(QtGui.QFormLayout.AllNonFixedFieldsGrow)
        self.formLayout.setObjectName(_fromUtf8("formLayout"))
        self.show_a_ion = QtGui.QCheckBox(self.frame_2)
        self.show_a_ion.setObjectName(_fromUtf8("show_a_ion"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.LabelRole, self.show_a_ion)
        self.show_x_ion = QtGui.QCheckBox(self.frame_2)
        self.show_x_ion.setObjectName(_fromUtf8("show_x_ion"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.FieldRole, self.show_x_ion)
        self.show_b_ion = QtGui.QCheckBox(self.frame_2)
        self.show_b_ion.setObjectName(_fromUtf8("show_b_ion"))
        self.formLayout.setWidget(2, QtGui.QFormLayout.LabelRole, self.show_b_ion)
        self.show_y_ion = QtGui.QCheckBox(self.frame_2)
        self.show_y_ion.setObjectName(_fromUtf8("show_y_ion"))
        self.formLayout.setWidget(2, QtGui.QFormLayout.FieldRole, self.show_y_ion)
        self.show_c_ion = QtGui.QCheckBox(self.frame_2)
        self.show_c_ion.setObjectName(_fromUtf8("show_c_ion"))
        self.formLayout.setWidget(3, QtGui.QFormLayout.LabelRole, self.show_c_ion)
        self.show_z_ion = QtGui.QCheckBox(self.frame_2)
        self.show_z_ion.setObjectName(_fromUtf8("show_z_ion"))
        self.formLayout.setWidget(3, QtGui.QFormLayout.FieldRole, self.show_z_ion)
        self.gridLayout_2.addWidget(self.frame_2, 1, 1, 1, 1)
        self.label = QtGui.QLabel(self.frame)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout_2.addWidget(self.label, 0, 0, 1, 1)
        self.label_2 = QtGui.QLabel(self.frame)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.gridLayout_2.addWidget(self.label_2, 1, 0, 1, 1)
        self.label_3 = QtGui.QLabel(self.frame)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.gridLayout_2.addWidget(self.label_3, 0, 2, 1, 1)
        self.label_5 = QtGui.QLabel(self.frame)
        self.label_5.setObjectName(_fromUtf8("label_5"))
        self.gridLayout_2.addWidget(self.label_5, 2, 0, 1, 1)
        self.label_6 = QtGui.QLabel(self.frame)
        self.label_6.setObjectName(_fromUtf8("label_6"))
        self.gridLayout_2.addWidget(self.label_6, 4, 0, 1, 1)
        self.max_isotope = QtGui.QSpinBox(self.frame)
        self.max_isotope.setMinimum(1)
        self.max_isotope.setMaximum(20)
        self.max_isotope.setObjectName(_fromUtf8("max_isotope"))
        self.gridLayout_2.addWidget(self.max_isotope, 3, 1, 1, 1)
        self.add_isotopes = QtGui.QCheckBox(self.frame)
        self.add_isotopes.setText(_fromUtf8(""))
        self.add_isotopes.setObjectName(_fromUtf8("add_isotopes"))
        self.gridLayout_2.addWidget(self.add_isotopes, 2, 1, 1, 1)
        self.add_losses = QtGui.QCheckBox(self.frame)
        self.add_losses.setText(_fromUtf8(""))
        self.add_losses.setObjectName(_fromUtf8("add_losses"))
        self.gridLayout_2.addWidget(self.add_losses, 4, 1, 1, 1)
        self.gridLayout.addWidget(self.frame, 0, 0, 1, 1)

        self.retranslateUi(PreferencesDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), PreferencesDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), PreferencesDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(PreferencesDialog)

    def retranslateUi(self, PreferencesDialog):
        PreferencesDialog.setWindowTitle(QtGui.QApplication.translate("PreferencesDialog", "Preferences", None, QtGui.QApplication.UnicodeUTF8))
        self.label_4.setText(QtGui.QApplication.translate("PreferencesDialog", "max isotope:", None, QtGui.QApplication.UnicodeUTF8))
        self.show_a_ion.setText(QtGui.QApplication.translate("PreferencesDialog", "A", None, QtGui.QApplication.UnicodeUTF8))
        self.show_x_ion.setText(QtGui.QApplication.translate("PreferencesDialog", "X", None, QtGui.QApplication.UnicodeUTF8))
        self.show_b_ion.setText(QtGui.QApplication.translate("PreferencesDialog", "B", None, QtGui.QApplication.UnicodeUTF8))
        self.show_y_ion.setText(QtGui.QApplication.translate("PreferencesDialog", "Y", None, QtGui.QApplication.UnicodeUTF8))
        self.show_c_ion.setText(QtGui.QApplication.translate("PreferencesDialog", "C", None, QtGui.QApplication.UnicodeUTF8))
        self.show_z_ion.setText(QtGui.QApplication.translate("PreferencesDialog", "Z", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("PreferencesDialog", "tolerance:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("PreferencesDialog", "Show Ions:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("PreferencesDialog", "Dalton", None, QtGui.QApplication.UnicodeUTF8))
        self.label_5.setText(QtGui.QApplication.translate("PreferencesDialog", "add isotopes:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_6.setText(QtGui.QApplication.translate("PreferencesDialog", "add losses:", None, QtGui.QApplication.UnicodeUTF8))


class PreferencesDialog(QtGui.QDialog, Ui_PreferencesDialog):
    def __init__(self, parent=None, f=QtCore.Qt.WindowFlags()):
        QtGui.QDialog.__init__(self, parent, f)

        self.setupUi(self)

