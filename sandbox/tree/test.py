from PyQt4.QtGui import QApplication
from PyQt4.QtCore import QVariant, QAbstractItemModel, QModelIndex, Qt

from treeview_ui import *

import sys

class TreeItem(object):

    def __init__(self, data):
        self.parent = None
        self.children = []
        self.data = data

    def addChild(self, child):
        self.children.append(child)
        child.parent = self

    def childCount(self):
        return len(self.children)

    def columnCount(self):
        return 1

    def data(self, column):
        assert column == 0
        return self.data

    def row(self):
        if self.parent:
            return self.parent.children.index(self)
        return 0


class TreeModel(QAbstractItemModel):

    def __init__(self, parent=None):
        super(TreeModel, self).__init__(parent)
        self.root_item = TreeItem("root")
        for i in range(10):
            child = TreeItem("aas %d" % i)
            self.root_item.addChild(child)
            for j in range(20):
                sub = TreeItem("sub %d of %d" % (j, i))
                child.addChild(sub)
                for k in range(20):
                    sub2 = TreeItem("sub %d of %d and %d" % (k, j, i))
                    sub.addChild(sub2)


    def data(self, index, role):
        if not index.isValid():
            return QVariant()
        if role != Qt.DisplayRole:
            return QVariant()

        item = index.internalPointer()
        return item.data #  [index.column()]

    def flags(self, index):
        if not index.isValid():
            return 0
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def index(self, row, column, parent=QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        if not parent.isValid():
            parent_item = self.root_item
        else:
            parent_item = parent.internalPointer()

        child_item = parent_item.children[row]
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
