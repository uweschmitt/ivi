from PyQt4.QtGui import QFrame, QGridLayout, QSizePolicy

from plotting_widgets import MzPlotter


class SpectrumPlotter(QFrame):

    def __init__(self, parent):
        super(SpectrumPlotter, self).__init__(parent)
        self.plotter = MzPlotter(None)
        self.plotter.setMinimumSize(800, 700)
        self.widget = self.plotter.widget
        self.widget.setVisible(True)
        self.layout = QGridLayout(self)
        policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.widget.setSizePolicy(policy)
        self.layout.addWidget(self.widget, 0, 0, 1, 1)

        self.plotter.reset()

    def plot_spectrum(self, spectrum):
        self.plotter.plot_spectrum(spectrum)
        self.plotter.replot()
