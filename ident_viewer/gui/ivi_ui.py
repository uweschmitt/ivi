# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ivi.ui'
#
# Created: Thu Feb 27 10:30:29 2014
#      by: PyQt4 UI code generator 4.9.1
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName(_fromUtf8("MainWindow"))
        MainWindow.resize(1200, 800)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.gridLayout = QtGui.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.splitter = QtGui.QSplitter(self.centralwidget)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName(_fromUtf8("splitter"))
        self.peptide_hits = QtGui.QTableView(self.splitter)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.peptide_hits.sizePolicy().hasHeightForWidth())
        self.peptide_hits.setSizePolicy(sizePolicy)
        self.peptide_hits.setAlternatingRowColors(False)
        self.peptide_hits.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.peptide_hits.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.peptide_hits.setSortingEnabled(True)
        self.peptide_hits.setObjectName(_fromUtf8("peptide_hits"))
        self.peptide_hits.horizontalHeader().setStretchLastSection(True)
        self.spectrum_plotter = SpectrumPlotter(self.splitter)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(2)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.spectrum_plotter.sizePolicy().hasHeightForWidth())
        self.spectrum_plotter.setSizePolicy(sizePolicy)
        self.spectrum_plotter.setObjectName(_fromUtf8("spectrum_plotter"))
        self.gridLayout.addWidget(self.splitter, 0, 0, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1200, 25))
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
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QtGui.QApplication.translate("MainWindow", "MainWindow", None, QtGui.QApplication.UnicodeUTF8))
        self.menuIdent_Viewer.setTitle(QtGui.QApplication.translate("MainWindow", "Ident Viewer", None, QtGui.QApplication.UnicodeUTF8))
        self.action_preferences.setText(QtGui.QApplication.translate("MainWindow", "Preferences", None, QtGui.QApplication.UnicodeUTF8))
        self.action_preferences.setShortcut(QtGui.QApplication.translate("MainWindow", "Ctrl+P", None, QtGui.QApplication.UnicodeUTF8))
        self.action_quit.setText(QtGui.QApplication.translate("MainWindow", "Quit", None, QtGui.QApplication.UnicodeUTF8))
        self.action_quit.setShortcut(QtGui.QApplication.translate("MainWindow", "Ctrl+Q", None, QtGui.QApplication.UnicodeUTF8))
        self.action_open_file.setText(QtGui.QApplication.translate("MainWindow", "Open File", None, QtGui.QApplication.UnicodeUTF8))
        self.action_open_file.setShortcut(QtGui.QApplication.translate("MainWindow", "Ctrl+O", None, QtGui.QApplication.UnicodeUTF8))

from spectrumplotter import SpectrumPlotter

class MainWindow(QtGui.QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None, f=QtCore.Qt.WindowFlags()):
        QtGui.QMainWindow.__init__(self, parent, f)

        self.setupUi(self)

