# -*- coding: utf-8 -*-
"""
Created on Wed Jul 17 10:50:56 2013

@author: uwe schmitt
"""

import sip
sip.setapi('QString', 1)
sip.setapi('QVariant', 1)

from PyQt4 import QtCore

from ..lib import extract_hits, PeptideHitAssigner



class PeptideHitModel(QtCore.QAbstractTableModel):

    peptideSelected = QtCore.pyqtSignal(object, object)

    def __init__(self, parent, peakmaps, peptide_identifications, protein_identifications):
        super(PeptideHitModel, self).__init__()
        self.hits = list(extract_hits(peakmaps[0], peptide_identifications, []))

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.hits)

    def columnCount(self, parent=QtCore.QModelIndex()):
        return 4

    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Vertical:
                return "%s" % section
            return ["score", "sequence", "rt", "mz"][section]
        return QtCore.QVariant()

    def sort(self, column, order):
        reverse = (order == QtCore.Qt.DescendingOrder)
        self.hits.sort(key=lambda row: row[column], reverse=reverse)
        self.dataChanged.emit(
            self.index(0, 0), self.index(self.rowCount() - 1, self.columnCount() - 1))

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            i = index.row()
            j = index.column()
            score, sequence, rt, mz, __, __ = self.hits[i]
            return ["%7.4f" % score, "%s" % sequence, "%.0fs" % rt, "%.5f" % mz][j]
        else:
            return QtCore.QVariant()

    def select(self, index):
        spec = self.hits[index][-1]
        hit = self.hits[index][-2]
        assignment =  PeptideHitAssigner(self.preferences).compute_assignment(hit, spec)
        self.peptideSelected.emit(spec, assignment)

    def set_preferences(self, preferences):
        self.preferences = preferences
