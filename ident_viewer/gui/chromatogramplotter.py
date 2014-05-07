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
        self.plot_chromatograms(chromos)




