# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ivi.ui'
#
# Created: Thu May 15 15:15:26 2014
#      by: PyQt4 UI code generator 4.10.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName(_fromUtf8("MainWindow"))
        MainWindow.resize(1200, 800)
        self.centralwidget = QtGui.QWidget(MainWindow)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.centralwidget.sizePolicy().hasHeightForWidth())
        self.centralwidget.setSizePolicy(sizePolicy)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.gridLayout = QtGui.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.splitter_3 = QtGui.QSplitter(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.splitter_3.sizePolicy().hasHeightForWidth())
        self.splitter_3.setSizePolicy(sizePolicy)
        self.splitter_3.setOrientation(QtCore.Qt.Horizontal)
        self.splitter_3.setObjectName(_fromUtf8("splitter_3"))
        self.tree_view = QtGui.QTreeView(self.splitter_3)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.tree_view.sizePolicy().hasHeightForWidth())
        self.tree_view.setSizePolicy(sizePolicy)
        self.tree_view.setAutoFillBackground(False)
        self.tree_view.setAlternatingRowColors(False)
        self.tree_view.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.tree_view.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.tree_view.setObjectName(_fromUtf8("tree_view"))
        self.splitter_2 = QtGui.QSplitter(self.splitter_3)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.splitter_2.sizePolicy().hasHeightForWidth())
        self.splitter_2.setSizePolicy(sizePolicy)
        self.splitter_2.setOrientation(QtCore.Qt.Vertical)
        self.splitter_2.setObjectName(_fromUtf8("splitter_2"))
        self.spectrum_plotter = SpectrumPlotter(self.splitter_2)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.spectrum_plotter.sizePolicy().hasHeightForWidth())
        self.spectrum_plotter.setSizePolicy(sizePolicy)
        self.spectrum_plotter.setMinimumSize(QtCore.QSize(0, 300))
        self.spectrum_plotter.setObjectName(_fromUtf8("spectrum_plotter"))
        self.splitter = QtGui.QSplitter(self.splitter_2)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.splitter.sizePolicy().hasHeightForWidth())
        self.splitter.setSizePolicy(sizePolicy)
        self.splitter.setMinimumSize(QtCore.QSize(0, 400))
        self.splitter.setBaseSize(QtCore.QSize(0, 0))
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName(_fromUtf8("splitter"))
        self.peakmap_plotter = PeakmapPlotter(self.splitter)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.peakmap_plotter.sizePolicy().hasHeightForWidth())
        self.peakmap_plotter.setSizePolicy(sizePolicy)
        self.peakmap_plotter.setObjectName(_fromUtf8("peakmap_plotter"))
        self.chromatogram_plotter = ChromatogramPlotter(self.splitter)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.chromatogram_plotter.sizePolicy().hasHeightForWidth())
        self.chromatogram_plotter.setSizePolicy(sizePolicy)
        self.chromatogram_plotter.setObjectName(_fromUtf8("chromatogram_plotter"))
        self.gridLayout.addWidget(self.splitter_3, 0, 0, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1200, 22))
        self.menubar.setNativeMenuBar(False)
        self.menubar.setObjectName(_fromUtf8("menubar"))
        self.menuIdent_Viewer = QtGui.QMenu(self.menubar)
        self.menuIdent_Viewer.setObjectName(_fromUtf8("menuIdent_Viewer"))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(MainWindow)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        MainWindow.setStatusBar(self.statusbar)
        self.action_preferences = QtGui.QAction(MainWindow)
        self.action_preferences.setObjectName(_fromUtf8("action_preferences"))
        self.action_quit = QtGui.QAction(MainWindow)
        self.action_quit.setObjectName(_fromUtf8("action_quit"))
        self.action_open_file = QtGui.QAction(MainWindow)
        self.action_open_file.setObjectName(_fromUtf8("action_open_file"))
        self.menuIdent_Viewer.addSeparator()
        self.menuIdent_Viewer.addAction(self.action_open_file)
        self.menuIdent_Viewer.addSeparator()
        self.menuIdent_Viewer.addAction(self.action_preferences)
        self.menuIdent_Viewer.addSeparator()
        self.menuIdent_Viewer.addAction(self.action_quit)
        self.menubar.addAction(self.menuIdent_Viewer.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QObject.connect(self.action_quit, QtCore.SIGNAL(_fromUtf8("triggered()")), MainWindow.close)
        QtCore.QObject.connect(self.action_preferences, QtCore.SIGNAL(_fromUtf8("triggered()")), MainWindow.edit_preferences)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow", None))
        self.menuIdent_Viewer.setTitle(_translate("MainWindow", "Ident Viewer", None))
        self.action_preferences.setText(_translate("MainWindow", "Preferences", None))
        self.action_preferences.setShortcut(_translate("MainWindow", "Ctrl+P", None))
        self.action_quit.setText(_translate("MainWindow", "Quit", None))
        self.action_quit.setShortcut(_translate("MainWindow", "Ctrl+Q", None))
        self.action_open_file.setText(_translate("MainWindow", "Open File", None))
        self.action_open_file.setShortcut(_translate("MainWindow", "Ctrl+O", None))

from chromatogramplotter import ChromatogramPlotter
from peakmapplotter import PeakmapPlotter
from spectrumplotter import SpectrumPlotter

class MainWindow(QtGui.QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None, f=QtCore.Qt.WindowFlags()):
        QtGui.QMainWindow.__init__(self, parent, f)

        self.setupUi(self)


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    MainWindow = QtGui.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())

