from PyQt4.QtGui import QFrame, QGridLayout, QSizePolicy

from plotting_widgets import RtPlotWidget

import numpy as np

from ..optimizations import extract_chromatogram


class ChromatogramPlotter(RtPlotWidget):

    def plot_feature(self, peakmap, feature):
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
