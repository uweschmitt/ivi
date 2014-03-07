from PyQt4.QtGui import QApplication
from PyQt4.QtCore import QVariant, QAbstractItemModel, QModelIndex, Qt

from treeview_ui import *

import sys

class HitItem(object):

    def __init__(self, parent, a, row):
        self.parent = parent
        self.a = a
        self._row = row

    def childCount(self):
        return 0

    def columnCount(self):
        return 1

    def data(self):
        return self.a

    def row(self):
        return self._row

    def get_child(self, row):
        assert False


def fetch_hits(aaseq, parent):
    return [HitItem(parent, h+"_"+aaseq, i) for i, h in enumerate("hit1 hit2 hit3".split())]


class AASeqItem(object):

    def __init__(self, parent, seq, row):
        self.parent = parent
        self.seq = seq
        self._row = row
        self.children = None

    def childCount(self):
        print "childCount"
        return len(fetch_hits(self.seq, self))

    def columnCount(self):
        return 1

    def data(self):
        return self.seq

    def row(self):
        return self._row

    def get_child(self, row):
        print "get_child"
        if self.children is None:
            self.children = fetch_hits(self.seq, self)
        return self.children[row]


class RootItem(object):

    def __init__(self):
        self.parent = None
        self.children = [AASeqItem(self, "abcdef"[i], i) for i in range(6)]

    def childCount(self):
        return len(self.children)

    def columnCount(self):
        return 1

    def data(self):
        return ""

    def row(self):
        return 0


class TreeModel(QAbstractItemModel):

    def __init__(self, parent=None):
        super(TreeModel, self).__init__(parent)
        self.root_item = RootItem()

    def data(self, index, role):
        if not index.isValid():
            return QVariant()
        if role != Qt.DisplayRole:
            return QVariant()

        item = index.internalPointer()
        return item.data() #  [index.column()]()

    def flags(self, index):
        if not index.isValid():
            return 0
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def index(self, row, column, parent=QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        if not parent.isValid():
            child_item = self.root_item.children[row]
        else:
            parent_item = parent.internalPointer()
            # should be aa seq !
            child_item = parent_item.get_child(row)

        return self.createIndex(row, column, child_item)

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()

        child_item = index.internalPointer()
        parent_item = child_item.parent
        if parent_item == self.root_item:
            return QModelIndex()
        return self.createIndex(parent_item.row(), 0, parent_item)

    def rowCount(self, parent=QModelIndex()):
        if parent.column() > 0:
            return 0
        if not parent.isValid():
            parent_item = self.root_item
        else:
            parent_item = parent.internalPointer()
        return parent_item.childCount()

    def columnCount(self, parent=QModelIndex()):
        if parent.isValid():
            return parent.internalPointer().columnCount()
        else:
            return self.root_item.columnCount()

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
             if section == 0:
                 return "AASequence"
             return "section %d" % section
        return QVariant()



class Window(MainWindow):

    def __init__(self):
        super(Window, self).__init__()
        self.model = TreeModel()
        self.treeView.setModel(self.model)
        self.treeView.setUniformRowHeights(True)



app = QApplication([])
win = Window()
win.show()
app.exec_()
