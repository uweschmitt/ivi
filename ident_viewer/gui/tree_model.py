from PyQt4.QtCore import QVariant, QAbstractItemModel, QModelIndex, Qt

import sys


class TreeItem(object):

    def __init__(self, parent, row, data, reader):
        self.parent = parent
        self.row_ = row
        self.data_ = data
        self.reader = reader

    def childCount(self):
        return 0

    def columnCount(self):
        return 4

    def data(self, col=0):
        return self.data_[col]

    def row(self):
        return self.row_

    def get_child(self, row):
        assert False, "should be implmented"



class HitItem(TreeItem):

    def __init__(self, parent, row, hit, reader):
        super(HitItem, self).__init__(parent, row, [hit], reader)
        self.children = None

    def data(self, col):
        hit = self.data_[0]
        #return hit.base_name
        if col==0:
            return "HIT: %s" % hit.base_name
        elif col == 1:
            if hit.rt is None:
                return "-"
            return "%.1fs" % hit.rt
        elif col == 2:
            if hit.mz is None:
                return "-"
            return "%.5f" % hit.mz
        elif col == 3:
            if hit.score is None:
                return "-"
            return "%.4f" % hit.score

    def childCount(self):
        return self.reader.count_spectra_for(self.data_[0])

    def get_child(self, row):
        if self.children is None:
            spectra = list(self.reader.fetch_spectra(self.data_[0]))
            spectra.sort(lambda spec: (spec.getRT(), spec.getPrecursors()[0].getMZ()))
            self.children = [SpectrumItem(self, i, s, self.reader) for (i, s) in enumerate(spectra)]
        return self.children[row]


class SpectrumItem(TreeItem):

    def __init__(self, parent, row, spectrum, reader):
        super(SpectrumItem, self).__init__(parent, row, [spectrum], reader)

    def data(self, col):
        spectrum = self.data_[0]
        if col == 0:
            return "MS2:"
        if col == 1:
            return "%.1fs" % spectrum.getRT()
        elif col == 2:
            return "%.5f" % spectrum.getPrecursors()[0].getMZ()
        return ""




class AASeqItem(TreeItem):

    def __init__(self, parent, row, seq, reader):
        super(AASeqItem, self).__init__(parent, row, [seq], reader)
        self.children = None

    def childCount(self):
        count = self.reader.get_number_of_hits_for(self.data_[0])
        return count

    def get_child(self, row):
        if self.children is None:
            hits = self.reader.get_hits_for_aa_sequence(self.data_[0])
            hits.sort(key=lambda hit: (hit.base_name, hit.rt, hit.mz))
            self.children = [HitItem(self, i, hit, self.reader) for (i, hit) in enumerate(hits)]
        return self.children[row]

    def data(self, col):
        return self.data_[0] if col == 0 else ""


class RootItem(TreeItem):

    def __init__(self, reader):
        super(RootItem, self).__init__(None, 0, ["AASequence" ,"base_name", "mz", "rt"], reader)
        aa_sequences = reader.get_aa_sequences()
        aa_sequences.sort(reverse=True)
        self.children = [AASeqItem(self, i, seq, reader) for (i, seq) in enumerate(aa_sequences)]

    def childCount(self):
        return len(self.children)

    def row(self):
        return 0

    def get_child(self, row):
        return self.children[row]


class TreeModel(QAbstractItemModel):

    def __init__(self, reader, parent=None):
        super(TreeModel, self).__init__(parent)
        self.root_item = RootItem(reader)

    def set_preferences(self, *a):
        print "preferences=", a


    def data(self, index, role):
        if not index.isValid():
            return QVariant()
        if role != Qt.DisplayRole:
            return QVariant()

        item = index.internalPointer()
        return item.data(index.column())

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
            return ["Hit", "RT", "MZ", "Score"][section]
        return QVariant()


if __name__ == "__main__":

    from PyQt4.QtGui import QApplication

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
