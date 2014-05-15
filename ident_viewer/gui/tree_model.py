
import sys
import collections
import time

from PyQt4.QtCore import QVariant, QAbstractItemModel, QModelIndex, Qt, pyqtSignal
from PyQt4.QtGui  import QApplication, QCursor

from ..lib import PeptideHitAssigner
from ..optimizations import find_chromatogram_rt_limits


class TreeItem(object):

    def __init__(self, parent, row, data, reader):
        self._parent = parent
        self._row = row
        self._data = data
        self._reader = reader

    def childCount(self):
        return 0

    def columnCount(self):
        return 4

    def data_in_column(self, col=0):
        return self._data[col]

    def row(self):
        return self._row

    def data(self):
        return self._data

    def parent(self):
        return self._parent

    def reader(self):
        return self._reader

    def get_child(self, row):
        assert False, "should be implmented"


class HitItem(TreeItem):

    def __init__(self, parent, row, hit, reader):
        super(HitItem, self).__init__(parent, row, hit, reader)
        self.children = None

    def data_in_column(self, col):
        hit = self.data()
        # return hit.base_name
        if col == 0:
            return "HIT: %s" % hit.base_name
        elif col == 1:
            return "%d" % hit.id_
        elif col == 2:
            if hit.rt is None:
                return "-"
            return "%.2fm" % (hit.rt / 60.0)
        elif col == 3:
            if hit.mz is None:
                return "-"
            return "%.5f" % hit.mz
        elif col == 4:
            if hit.score is None:
                return "-"
            return "%.4f" % hit.score

    def childCount(self):
        hit = self.data()
        return self.reader().count_spectra_for(hit) + self.reader().count_features_for(hit) + 1

    def get_child(self, row):
        r = self.reader()
        if self.children is None:
            hit = self.data()
            spectra = list(r.fetch_spectra(hit))
            spectra.sort(lambda spec: (spec.rt, spec.precursors[0].mz))
            self.children = [SpectrumItem(self, i, s, r) for (i, s) in enumerate(spectra)]
            features = list(r.fetch_features_for_hit(hit))
            n = len(self.children)
            self.children += [FeatureItem(self, i + n, f, r) for (i, f) in enumerate(features)]
            n = len(self.children)
            self.children += [MassTraceItem(self, n, r)]
        return self.children[row]


class SpectrumItem(TreeItem):

    def __init__(self, parent, row, spectrum, reader):
        super(SpectrumItem, self).__init__(parent, row, spectrum, reader)

    def data_in_column(self, col):
        spectrum = self.data()
        if col == 0:
            return "MS2:"
        if col == 2:
            return "%.2fm" % (spectrum.rt / 60.0)
        elif col == 3:
            return "%.5f" % spectrum.precursors[0].mz
        return ""


class FeatureItem(TreeItem):

    def __init__(self, parent, row, feature, reader):
        super(FeatureItem, self).__init__(parent, row, feature, reader)

    def data_in_column(self, col):
        feature = self.data()
        if col == 0:
            return "FEATURE:"
        if col == 1:
            return str(feature.fid)
        return ""


class MassTraceItem(TreeItem):

    def __init__(self, parent, row, reader):
        super(MassTraceItem, self).__init__(parent, row, None, reader)

    def data_in_column(self, col):
        hit = self.parent().data()
        if col == 0:
            return "MASSTRACE:"
        if col == 2:
            return "%.2fm" % (hit.rt / 60.0)
        elif col == 3:
            return "%.5f" % hit.mz
        return ""


class AASeqItem(TreeItem):

    def __init__(self, parent, row, seq, reader):
        super(AASeqItem, self).__init__(parent, row, seq, reader)
        self.children = None

    def childCount(self):
        count = self.reader().get_number_of_hits_for(self.data())
        return count

    def get_child(self, row):
        r = self.reader()
        if self.children is None:
            hits = r.get_hits_for_aa_sequence(self.data())
            hits.sort(key=lambda hit: (hit.base_name, hit.rt, hit.mz))
            self.children = [HitItem(self, i, hit, r) for (i, hit) in enumerate(hits)]
        return self.children[row]

    def data_in_column(self, col):
        return self.data() if col == 0 else ""


class RootItem(TreeItem):

    def __init__(self, reader):
        super(RootItem, self).__init__(None, 0, ["AASequence", "base_name", "mz", "rt"], reader)
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

    spectrumSelected = pyqtSignal(object, object)

    featureSelected = pyqtSignal(object, object, object)

    massTraceSelected = pyqtSignal(object, float, float, float, float, str)

    newHitRt = pyqtSignal(float)

    ms1HitChanged = pyqtSignal()
    ms2HitChanged = pyqtSignal()

    def __init__(self, reader, parent=None):
        super(TreeModel, self).__init__(parent)
        self.root_item = RootItem(reader)
        self.last_hit_id = None

    def set_preferences(self, preferences):
        self.preferences = preferences

    def data(self, index, role):
        if not index.isValid():
            return QVariant()
        if role != Qt.DisplayRole:
            return QVariant()

        item = index.internalPointer()
        return item.data_in_column(index.column())

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
        parent_item = child_item.parent()
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
            return ["Hit", "ID", "RT", "MZ", "Score"][section]
        return QVariant()

    def select(self, index):
        item = index.internalPointer()
        if isinstance(item, (SpectrumItem, FeatureItem, MassTraceItem)):
            hit = item.parent().data()
            hit_changed = hit.id_ != self.last_hit_id
            self.last_hit_id = hit.id_
            if isinstance(item, SpectrumItem):
                spectrum = item.data()
                assignment = PeptideHitAssigner(self.preferences).compute_assignment(hit, spectrum)
                self.spectrumSelected.emit(spectrum, assignment)
                if hit_changed:
                    self.ms1HitChanged.emit()

            elif isinstance(item, FeatureItem):
                feature = item.data()
                pm = PeakMapLRUCache.get(item.reader(), feature.base_name)
                self.featureSelected.emit(pm, feature, hit)
                if hit_changed:
                    self.ms2HitChanged.emit()

            elif isinstance(item, MassTraceItem):
                pm = PeakMapLRUCache.get(item.reader(), hit.base_name)
                mz_width = self.preferences.get("ms1_tolerance")

                if self.preferences.get("ms1_tolerance_unit") == "ppm":
                    mzmin = hit.mz * (1.0 - mz_width * 1e-6)
                    mzmax = hit.mz * (1.0 + mz_width * 1e-6)
                else:
                    mzmin = hit.mz - mz_width
                    mzmax = hit.mz + mz_width
                rtmin, rtmax = find_chromatogram_rt_limits(pm, hit.rt, mzmin, mzmax, 1, 2)
                self.massTraceSelected.emit(pm, rtmin, rtmax, mzmin, mzmax, hit.aa_sequence)

                if hit_changed:
                    self.ms2HitChanged.emit()
            self.newHitRt.emit(hit.rt)


class PeakMapLRUCache(object):

    max_size = 10

    cache = collections.OrderedDict()

    @staticmethod
    def get(reader, base_name):
        cache = PeakMapLRUCache.cache
        if base_name in cache:
            return cache[base_name]
        if len(cache) > PeakMapLRUCache.max_size:
            cache.popitem(0)
        s = time.time()
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        pm = reader.fetch_peak_map(base_name)
        QApplication.restoreOverrideCursor()
        cache[base_name] = pm
        print "loading needed %.1f s" % (time.time() - s)
        return pm


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
