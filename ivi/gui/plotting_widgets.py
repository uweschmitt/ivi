import types
import new

from guiqwt.plot import CurveWidget, PlotManager
from guiqwt.builder import make
from guiqwt.label import ObjectInfo

from PyQt4.Qwt5 import QwtText, QwtScaleDraw
from PyQt4.QtGui import QWidget
from PyQt4 import QtGui

import numpy as np

from helpers import protect_signal_handler
from modified_guiqwt import *
from config import setupStyleRangeMarker, setupCommonStyle, setupStyleRtMarker

from emzed_optimizations.sample import sample_peaks

from utils import set_x_axis_scale_draw, set_y_axis_scale_draw



def getColor(i, light=False):
    colors = [(0, 0, 200), (70, 70, 70), (0, 150, 0), (200, 0, 0), (200, 200, 0), (100, 70, 0)]
    c = colors[i % len(colors)]
    if light:
        c = tuple([min(ii + 50, 255) for ii in c])

    # create hex string  "#rrggbb":
    return "#" + "".join("%02x" % v for v in c)

def formatSeconds(seconds):
    return "%.2fm" % (seconds / 60.0)


class PlotWidget(QWidget):

    def __init__(self, parent, xlabel, ylabel, modified_parent_class=None):
        super(PlotWidget, self).__init__(parent)

        self.layout = QtGui.QGridLayout(self)

        self.widget = CurveWidget(parent, xlabel=xlabel, ylabel=ylabel)
        set_y_axis_scale_draw(self.widget) 
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
        self.del_foreground_items()
        self.del_background_items()

    def del_background_items(self):
        self.background_items = []

    def del_foreground_items(self):
        self.foreground_items = []

    def add_background_item(self, item):
        self.background_items.append(item)

    def add_foreground_item(self, item):
        self.foreground_items.append(item)

    def reset_x_limits(self, xmin=None, xmax=None, fac=1.2):
        self.plot.reset_x_limits(xmin, xmax, fac)

    def reset_y_limits(self, ymin=None, ymax=None, fac=1.2):
        self.plot.reset_y_limits(ymin, ymax, fac)

    def replot(self):
        self.plot.replot()

    def clear_plot(self):
        self.plot.del_all_items()
        self.replot()

    def plot_background_items(self):
        for item in self.background_items:
            self.plot.add_item(item)

    def plot_foreground_items(self):
        for item in self.foreground_items:
            self.plot.add_item(item)

class MzCursorInfo(ObjectInfo):

    def __init__(self, marker, line):
        super(MzCursorInfo, self).__init__()
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


class RtCursorInfo(ObjectInfo):

    def __init__(self, marker):
        super(RtCursorInfo, self).__init__()
        self.marker = marker

    def get_text(self):
        rt = self.marker.xValue()
        txt = "%.2fm" % (rt / 60.0)
        return txt


def add_marker(plot):
    """ Marker is the red dot aka "peak ursor" """
    marker = Marker(label_cb=plot.label_info, constraint_cb=plot.on_plot)
    return marker


def make_curve_without_point_selection(**kwargs):
    curve = make.curve([], [], **kwargs)
    curve.can_select = types.MethodType(lambda self: False, curve, CurveItem)
    return curve


def make_peak_curve(mzs, iis):
    curve = make_curve_without_point_selection(color='b', curvestyle='Sticks')
    curve.set_data(mzs, iis)
    return curve


def make_chromatorgram_curve(rts, iis, title, color):
    curve = make_curve_without_point_selection(title=title, color=color, linewidth=1.5)
    curve.set_data(rts, iis)
    return curve


def make_label(marker, line):
    label = make.info_label("TR", [MzCursorInfo(marker, line)], title=None)
    label.labelparam.label = ""
    return label





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

        self.plot.add_item(self.marker)
        self.plot.add_item(self.label)
        self.plot.add_item(self.line)

        self.plot.startMeasuring.connect(self.line.start_measuring)
        self.plot.moveMeasuring.connect(self.line.move_measuring)
        self.plot.stopMeasuring.connect(self.line.stop_measuring)
        self.plot.moveMarker.connect(self.marker.move_local_point_to)
        self.line.updated.connect(self.plot.replot)

    def plot_spectra(self, spectra):

        self.plot.del_all_items()

        self.plot.add_item(self.marker)
        self.plot.add_item(self.label)
        self.plot.add_item(self.line)

        self.plot_background_items()

        all_peaks = []
        for (mzs, iis) in spectra:
            peaks = np.vstack((mzs, iis)).T
            all_peaks.append(peaks)
            curve = make_peak_curve(mzs, iis)
            self.plot.add_item(curve)

        self.plot.all_peaks = np.vstack(all_peaks)

        self.plot_foreground_items()
        self.plot.reset_all_axes()
        self.replot()

    def plot_spectrum(self, spectrum):
        self.plot_spectra([spectrum])



class RtPlotWidget(PlotWidget):

    rtCursorMoved = pyqtSignal(float)

    def __init__(self, parent):
        super(RtPlotWidget, self).__init__(parent, "rt", "I", RtPlot)
        self.configure_plot()

    def configure_plot(self):

        set_x_axis_scale_draw(self.widget)
        manager = PlotManager(self.widget)
        manager.add_plot(self.plot)

        tool = manager.add_tool(RtSelectionTool)
        tool.activate()
        manager.set_default_tool(tool)

        self.marker = add_marker(self.plot)
        setupStyleRtMarker(self.marker)
        self.marker.rts = (0, )
        self.plot.moveMarker.connect(self.marker.move_local_point_to)
        self.plot.moveMarker.connect(self.move_rt_cursor)

    def move_rt_cursor(self, hnd, pos):
        rt = self.plot.invTransform(self.plot.xBottom, pos.x())
        self.rtCursorMoved.emit(rt)

    def move_marker(self, rt, mz):
        self.marker.setXValue(rt)
        self.replot()

    def plot_chromatograms(self, chromatograms):

        self.plot.del_all_items()
        self.plot.add_item(make.legend("TR"))
        self.plot.add_item(self.marker)

        self.plot_background_items()

        rtall = set()

        for i, (rts, iis, title) in enumerate(chromatograms):
            curve = make_chromatorgram_curve(rts, iis, title, getColor(i, True))
            self.plot.add_item(curve)
            rtall.update(rts)

        self.marker.rts = sorted(rtall)

        self.plot_foreground_items()

        self.plot.reset_all_axes()
        self.replot()


