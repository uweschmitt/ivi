from guiqwt.plot import CurveWidget, PlotManager
from guiqwt.builder import make
from guiqwt.label import ObjectInfo
from guiqwt.annotations import AnnotatedPoint

from modified_guiqwt import *
from config import setupStyleRangeMarker, setupCommonStyle, setupStyleRtMarker

from PyQt4.Qwt5 import QwtScaleDraw, QwtText
from PyQt4.QtGui import QWidget
from PyQt4 import QtGui


import numpy as np
import new

from helpers import protect_signal_handler

from emzed_optimizations.sample import sample_peaks


def getColor(i):
    colors = "bgrkm"
    return colors[i % len(colors)]



class PlotWidget(QWidget):

    def __init__(self, parent, xlabel, ylabel, modified_parent_class=None):
        super(PlotWidget, self).__init__(parent)

        self.layout = QtGui.QGridLayout(self)

        self.widget = CurveWidget(parent, xlabel=xlabel, ylabel=ylabel)
        # inject modified behaviour of widgets plot:
        if modified_parent_class is not None:
            self.widget.plot.__class__ = modified_parent_class

        self.plot = self.widget.plot

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        self.widget.setSizePolicy(sizePolicy)

        left, top, right, bottom = 0, 0, 0, 0
        self.widget.setContentsMargins(left, top, right, bottom)
        self.layout.setContentsMargins(left, top, right, bottom)
        self.layout.addWidget(self.widget, 0, 0, 1, 1)

    def reset_x_limits(self, xmin=None, xmax=None, fac=1.2):
        self.plot.reset_x_limits(xmin, xmax, fac)

    def reset_y_limits(self, ymin=None, ymax=None, fac=1.2):
        self.plot.reset_y_limits(ymin, ymax, fac)

    def replot(self):
        self.plot.replot()


class MzCursorInfo(ObjectInfo):

    def __init__(self, marker, line):
        ObjectInfo.__init__(self)
        self.marker = marker
        self.line = line

    def get_text(self):
        mz, I = self.marker.xValue(), self.marker.yValue()
        txt = "mz=%.6f<br/>I=%.1e" % (mz, I)
        if self.line.isVisible():
            _, _, mz2, I2 = self.line.get_rect()
            mean = (mz + mz2) / 2.0
            txt += "<br/><br/>dmz=%.6f<br/>rI=%.3e<br/>mean=%.6f" % (mz2 - mz, I2 / I, mean)

        return "<pre>%s</pre>" % txt


def add_marker(plot):
    """ Marker is the red dot aka "peak ursor" """
    marker = Marker(label_cb=plot.label_info, constraint_cb=plot.on_plot)
    return marker


def make_peak_curve(mzs, iis):
    curve = make.curve([], [], color='b', curvestyle="Sticks")
    # inject modified behaviour:
    curve.__class__ = CurveWithoutPointSelection
    curve.set_data(mzs, iis)
    return curve


def make_label(marker, line):
    label = make.info_label("TR", [MzCursorInfo(marker, line)], title=None)
    label.labelparam.label = ""
    return label



class Annotation(AnnotatedPoint):

    def __init__(self, x, y, text, color="white"):
        super(Annotation, self).__init__(x, y)
        self.label.labelparam.color = color
        self.label.labelparam.bgalpha = 0.1
        self.label.labelparam.font.size = 8
        self.label.labelparam.border.width = 0
        self.label.labelparam.update_label(self.label)
        self.text = text

    def get_text(self):
        return self.text


class MzPlotWidget(PlotWidget):

    def __init__(self, parent):
        super(MzPlotWidget, self).__init__(parent, "m/z", "I", MzPlot)
        self.configure_plot()

    def configure_plot(self):

        self.marker = add_marker(self.plot)
        self.line = MeasurementLine()
        self.line.setVisible(0)
        self.label = make_label(self.marker, self.line)

        setupCommonStyle(self.line, self.marker)

        manager = PlotManager(self.widget)
        manager.add_plot(self.plot)

        tool = manager.add_tool(MzSelectionTool)
        tool.activate()
        manager.set_default_tool(tool)

        #self.plot.add_item(Annotation(300.0, 100.0, "y++\nKAR(*)", "red"))

        self.plot.add_item(self.marker)
        self.plot.add_item(self.label)
        self.plot.add_item(self.line)

        self.plot.startMeasuring.connect(self.line.start_measuring)
        self.plot.moveMeasuring.connect(self.line.move_measuring)
        self.plot.stopMeasuring.connect(self.line.stop_measuring)
        self.plot.moveMarker.connect(self.marker.move_local_point_to)
        self.line.updated.connect(self.plot.replot)

        self.annotations = []

    def set_annotations(self, annotations):
        self.annotations = []
        for (mz, I, text, color) in annotations:
            self.annotations.append(Annotation(mz, I, text, color))


    def plot_spectra(self, spectra):

        self.plot.del_all_items()

        self.plot.add_item(self.marker)
        self.plot.add_item(self.label)
        self.plot.add_item(self.line)

        all_peaks = []
        for spectrum in spectra:
            mzs, iis = spectrum.get_peaks()
            peaks = np.vstack((mzs, iis)).T
            all_peaks.append(peaks)
            curve = make_peak_curve(mzs, iis)
            self.plot.add_item(curve)

        self.plot.all_peaks = np.vstack(all_peaks)

        for annotation in self.annotations:
            self.plot.add_item(annotation)

        self.plot.reset_all_axes()
        self.replot()

    def plot_spectrum(self, spectrum):
        self.plot_spectra([spectrum])
