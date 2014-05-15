from PyQt4.QtGui import QFrame, QGridLayout, QSizePolicy
from guiqwt.builder import make
from guiqwt.shapes import Marker

from plotting_widgets import RtPlotWidget

import numpy as np

from ..optimizations import extract_chromatogram


def create_rt_ms2_marker():
    marker = make.marker(position=(0, 0),
                         markerstyle="|",
                         label_cb=lambda x, y: "<div style='color:red'>rt_ms2</div>",
                         constraint_cb=lambda x, y: (x, y),
                         movable=False,
                         readonly=False,
                         color="#ff7777",
                         linewidth=1)

    # else the get_unique_item methods in modified_guiqwt fail:
    class DummyMarkerAsOnlyOneTrueMarkerIsAllowed(Marker):
        pass
    marker.__class__ = DummyMarkerAsOnlyOneTrueMarkerIsAllowed
    return marker


class ChromatogramPlotter(RtPlotWidget):

    def __init__(self, parent):
        super(ChromatogramPlotter, self).__init__(parent)
        self.fixed_rt_marker = create_rt_ms2_marker()
        self.add_background_item(self.fixed_rt_marker)
        self.clear()

    def clear(self):
        self.plot_chromatograms([])
        self.set_rt_marker(-1)

    def plot_chromatogram_from_masstrace(self, peakmap, rtmin, rtmax, mzmin, mzmax, aa_sequence):
        rts, iis = extract_chromatogram(peakmap, rtmin, rtmax, mzmin, mzmax, 1)
        self.plot_chromatograms([(rts, iis, "0")])

    def set_rt_marker(self, rt):
        self.fixed_rt_marker.setXValue(rt)

    def plot_chromatograms_from_feature(self, peakmap, feature, hit):
        # self.fixed_rt_marker.setXValue(hit.rt)
        chromos = []
        for mt in feature.mass_traces:
            rts, iis = extract_chromatogram(peakmap, mt.rtmin, mt.rtmax, mt.mzmin, mt.mzmax, 1)
            chromos.append((rts, iis))
        max_i = 0.0
        max_idx = 0
        for i, (rts, iis) in enumerate(chromos):
            if len(iis):
                m = max(iis)
                if m > max_i:
                    max_i = m
                    max_idx = i
        labeled_chromos = []
        for i, (rts, iis) in enumerate(chromos):
            labeled_chromos.append((rts, iis, str(i - max_idx)))

        # reverse list in order to have nicer legend in plot:
        self.plot_chromatograms(labeled_chromos[::-1])
