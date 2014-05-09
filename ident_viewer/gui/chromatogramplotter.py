from PyQt4.QtGui import QFrame, QGridLayout, QSizePolicy
from guiqwt.builder import make
from guiqwt.shapes import Marker

from plotting_widgets import RtPlotWidget

import numpy as np

from ..optimizations import extract_chromatogram


def create_rt_ms2_marker():
    marker = make.marker(position=(0, 0),
                         markerstyle="|",
                         label_cb=lambda x, y: "<div style='color:blue'>rt_ms2</div>",
                         constraint_cb=lambda x, y: (x, y),
                         movable=False,
                         readonly=False,
                         color="#ddddff",
                         linewidth=2)

    # else the get_unique_item methods in modified_guiqwt fail:
    class DummyMarkerAsOnlyOneTrueMarkerIsAllowed(Marker):
        pass
    marker.__class__ = DummyMarkerAsOnlyOneTrueMarkerIsAllowed
    return marker


class ChromatogramPlotter(RtPlotWidget):

    def __init__(self, parent):
        super(ChromatogramPlotter, self).__init__(parent)
        self.fix_rt_marker = create_rt_ms2_marker()
        self.add_background_item(self.fix_rt_marker)

    def plot_feature(self, peakmap, feature, hit):
        self.fix_rt_marker.setXValue(hit.rt)
        chromos = []
        for mt in feature.mass_traces:
            rts, iis = extract_chromatogram(peakmap, mt.rt_min, mt.rt_max, mt.mz_min, mt.mz_max, 1)
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
