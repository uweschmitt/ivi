from PyQt4.QtGui import QFrame, QGridLayout, QSizePolicy

from plotting_widgets import MzPlotWidget

class SpectrumPlotter(MzPlotWidget):

    def plot_hit(self, spectrum, assignment):
        annotations = []
        for mz, ii, ion_name, info in assignment:
            color = dict(y="red", b="green").get(ion_name[0], "black")
            annotations.append((mz, ii, "%s<br>%s" % (ion_name, info or ""), color))
        self.set_annotations(annotations)
        self.plot_spectrum(spectrum)

