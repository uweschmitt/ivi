
from guiqwt.plot import CurveWidget, PlotManager
from guiqwt.builder import make
from guiqwt.label import ObjectInfo

from modified_guiqwt import *
from config import setupStyleRangeMarker, setupCommonStyle, setupStyleRtMarker

from PyQt4.Qwt5 import QwtScaleDraw, QwtText

import numpy as np
import new

from helpers import protect_signal_handler

from emzed_optimizations.sample import sample_peaks


def getColor(i):
    colors = "bgrkm"
    return colors[i % len(colors)]


def formatSeconds(seconds):
    return "%.2fm" % (seconds / 60.0)


class RtRangeSelectionInfo(ObjectInfo):

    def __init__(self, range_):
        ObjectInfo.__init__(self)
        self.range_ = range_

    def get_text(self):
        rtmin, rtmax = sorted(self.range_.get_range())
        if rtmin != rtmax:
            return u"RT: %s ... %s" % (formatSeconds(rtmin),
                                       formatSeconds(rtmax))
        else:
            return u"RT: %s" % formatSeconds(rtmin)


class PlotterBase(object):

    def __init__(self, parent, xlabel, ylabel):
        self.widget = CurveWidget(parent, xlabel=xlabel, ylabel=ylabel)

    def setXAxisLimits(self, xmin, xmax):
        self.widget.plot.update_plot_xlimits(xmin, xmax)

    def updateAxes(self):
        self.widget.plot.updateAxes()

    def setYAxisLimits(self, ymin, ymax):
        self.widget.plot.update_plot_ylimits(ymin, ymax)

    def setMinimumSize(self, a, b):
        self.widget.setMinimumSize(a, b)

    def reset_x_limits(self, xmin=None, xmax=None, fac=1.2):
        self.widget.plot.reset_x_limits(xmin, xmax, fac)

    def reset_y_limits(self, ymin=None, ymax=None, fac=1.2):
        self.widget.plot.reset_y_limits(ymin, ymax, fac)

    def set_limit(self, ix, value):
        self.widget.plot.set_limit(ix, value)

    def getLimits(self):
        return self.widget.plot.get_plot_limits()

    def replot(self):
        self.widget.plot.replot()


class RtCursorInfo(ObjectInfo):
    def __init__(self, marker):
        ObjectInfo.__init__(self)
        self.marker = marker

    def get_text(self):
        rt = self.marker.xValue()
        txt = "%.2fm" % (rt / 60.0)
        return txt


class RtPlotter(PlotterBase):

    def __init__(self, parent, rangeSelectionCallback=None):
        super(RtPlotter, self).__init__(parent, "RT", "I")

        self.rangeSelectionCallback = rangeSelectionCallback

        widget = self.widget
        widget.plot.__class__ = RtPlot

        # todo: refactor as helper
        a = QwtScaleDraw()
        # render tic labels in modfied format:
        label = lambda self, v: QwtText(formatSeconds(v))
        a.label = new.instancemethod(label, widget.plot, QwtScaleDraw)
        widget.plot.setAxisScaleDraw(widget.plot.xBottom, a)

        self.pm = PlotManager(widget)
        self.pm.add_plot(widget.plot)

        t = self.pm.add_tool(RtSelectionTool)
        self.addTool(RtSelectionTool)
        self.pm.set_default_tool(t)

        marker = Marker(label_cb=self.widget.plot.label_info,
                        constraint_cb=self.widget.plot.on_plot)
        marker.rts = [0]
        setupStyleRtMarker(marker)
        marker.attach(self.widget.plot)
        self.marker = marker

        label = make.info_label("T", [RtCursorInfo(marker)], title=None)
        label.labelparam.label = ""
        self.label = label

        self.minRTRangeSelected = None
        self.maxRTRangeSelected = None

    def addTool(self, tool):
        t = self.pm.add_tool(tool)
        t.activate()

    def reset(self):
        self.plot([])
        self.marker.rts = [0]
        self.replot()

    def plot(self, chromatograms, titles=None, configs=None,
             withmarker=False):
        """ do not forget to call replot() after calling this function ! """
        allrts = set()
        self.widget.plot.del_all_items()
        # self.widget.plot.set_antialiasing(True)
        for i in range(len(chromatograms)):
            rts, chromatogram = chromatograms[i]
            config = None
            if configs is not None:
                config = configs[i]
            if config is None:
                config = dict(color=getColor(i))
            if titles:
                title = titles[i]
            else:
                title = ""

            curve = make.curve(rts, chromatogram, title=title, **config)
            curve.__class__ = ModifiedCurveItem
            allrts.update(rts)
            self.widget.plot.add_item(curve)

        if withmarker:
            self.widget.plot.add_item(self.label)
            allrts = sorted(allrts)
            self.marker.rts = allrts
            self.marker.attach(self.widget.plot)
            self.widget.plot.add_item(self.marker)
        if titles is not None:
            self.widget.plot.add_item(make.legend("TL"))
        self.addRangeSelector(allrts)

    def setEnabled(self, enabled):
        self.widget.plot.setVisible(enabled)

    def addRangeSelector(self, rtvalues):

        self.rtvalues = rtvalues
        self.minRTRangeSelected = 0
        self.maxRTRangeSelected = 0

        range_ = SnappingRangeSelection(self.minRTRangeSelected,
                                        self.maxRTRangeSelected, self.rtvalues)
        setupStyleRangeMarker(range_)
        self.range_ = range_

        # you have to register item to plot before you can register the
        # rtSelectionHandler:
        self.widget.plot.add_item(range_)
        self.widget.disconnect(range_.plot(), SIG_RANGE_CHANGED,
                               self.rangeSelectionHandler)
        self.widget.connect(range_.plot(), SIG_RANGE_CHANGED,
                            self.rangeSelectionHandler)

        cc = make.info_label("TR", [RtRangeSelectionInfo(range_)], title=None)
        cc.labelparam.label = ""
        self.widget.plot.add_item(cc)

    def getRangeSelectionLimits(self):
        return sorted((self.range_._min, self.range_._max))

    def setRangeSelectionLimits(self, xleft, xright):
        saved = self.rangeSelectionCallback
        self.rangeSelectionCallback = None
        self.minRTRangeSelected = xleft
        self.maxRTRangeSelected = xright
        # left and right bar of range marker
        self.range_.move_point_to(0, (xleft, 0), emitsignal=False)
        self.range_.move_point_to(1, (xright, 0))
        # calls self.rangeSelectionHandler !
        self.rangeSelectionCallback = saved

    @protect_signal_handler
    def rangeSelectionHandler(self, obj, left, right):
        min_, max_ = sorted((left, right))
        self.minRTRangeSelected = min_
        self.maxRTRangeSelected = max_
        if self.rangeSelectionCallback is not None:
            self.rangeSelectionCallback()


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


class MzPlotter(PlotterBase):

    def __init__(self, parent, c_callback=None, image_plot=None):
        super(MzPlotter, self).__init__(parent, "m/z", "I")

        self.c_callback = c_callback

        widget = self.widget

        # inject mofified behaviour of wigets plot attribute:
        widget.plot.__class__ = MzPlot
        widget.plot.register_c_callback(self.handle_c_pressed)
        widget.plot.image_plot = image_plot
        self.setHalfWindowWidth(0.05)
        self.centralMz = None

        # todo: refactor as helper
        a = QwtScaleDraw()
        label = lambda self, x: QwtText("%s" % x)
        a.label = new.instancemethod(label, widget.plot, QwtScaleDraw)
        widget.plot.setAxisScaleDraw(widget.plot.xBottom, a)

        self.pm = PlotManager(widget)
        self.pm.add_plot(widget.plot)
        self.curve = make.curve([], [], color='b', curvestyle="Sticks")
        # inject modified behaviour:
        self.curve.__class__ = ModifiedCurveItem

        self.widget.plot.add_item(self.curve)

        t = self.pm.add_tool(MzSelectionTool)
        self.pm.set_default_tool(t)
        t.activate()

        marker = Marker(label_cb=widget.plot.label_info,
                        constraint_cb=widget.plot.on_plot)
        marker.attach(self.widget.plot)

        line = make.segment(0, 0, 0, 0)
        line.__class__ = ModifiedSegment
        line.setVisible(0)

        setupCommonStyle(line, marker)

        label = make.info_label("TR", [MzCursorInfo(marker, line)], title=None)
        label.labelparam.label = ""

        self.marker = marker
        self.label = label
        self.line = line

    def setHalfWindowWidth(self, w2):
        self.widget.plot.set_half_window_width(w2)

    def setCentralMz(self, mz):
        self.widget.plot.set_central_mz(mz)

    def handle_c_pressed(self, p):
        if self.c_callback:
            self.c_callback(p)

    def plot_spectrum(self, spectrum):
        self.widget.plot.del_all_items()
        self.widget.plot.add_item(self.marker)
        self.widget.plot.add_item(self.label)

        peaks = spectrum.get_peaks()
        #mzmin = peaks.min(axis=0)
        #mzmax = peaks.max(axis=0)

        curve = make.curve([], [], curvestyle="Sticks")
        curve.set_data(peaks[:, 0], peaks[:, 1])
        curve.__class__ = ModifiedCurveItem
        self.widget.plot.add_item(curve)
        self.widget.plot.curves.append(curve)
        # self.widget.plot.data.append((pm, 0, 0, mzmin, mzmax, npeaks))
        self.widget.plot.all_peaks = peaks

    def plot(self, data, configs=None, titles=None):
        """ do not forget to call replot() after calling this function ! """
        self.widget.plot.del_all_items()
        self.widget.plot.add_item(self.marker)
        if titles is not None:
            self.widget.plot.add_item(make.legend("TL"))
        self.widget.plot.add_item(self.label)

        all_peaks = []
        self.widget.plot.data = []
        self.widget.plot.curves = []
        for i, (pm, rtmin, rtmax, mzmin, mzmax, npeaks) in enumerate(data):
            if rtmin is None and rtmax is None:
                rtmin, rtmax = pm.rtRange()
            elif rtmin is None:
                rtmin, __ = pm.rtRange()
            elif rtmax is None:
                __, rtmax = pm.rtRange()
            if mzmin is None and mzmax is None:
                mzmin, mzmax = pm.mzRange()
            elif mzmin is None:
                mzmin, __ = pm.mzRange()
            elif mzmax is None:
                __, mzmax = pm.mzRange()
            if npeaks is None:
                npeaks = 3000

            peaks = sample_peaks(pm, rtmin, rtmax, mzmin, mzmax, npeaks)
            all_peaks.append(peaks)
            config = configs[i] if configs is not None else None
            if config is None:
                config = dict(color=getColor(i))
            if titles is not None:
                title = titles[i]
            else:
                title = u""
            curve = make.curve([], [], title=title, curvestyle="Sticks", **config)
            curve.set_data(peaks[:, 0], peaks[:, 1])
            curve.__class__ = ModifiedCurveItem
            self.widget.plot.add_item(curve)
            self.widget.plot.curves.append(curve)
            self.widget.plot.data.append((pm, rtmin, rtmax, mzmin, mzmax, npeaks))
        self.widget.plot.add_item(self.line)
        if len(all_peaks):
            self.widget.plot.all_peaks = np.vstack(all_peaks)
        else:
            self.widget.plot.all_peaks = np.zeros((0, 2))

    def resetAxes(self):
        self.widget.plot.reset_x_limits()

    def reset(self):
        self.plot(np.ndarray((0, 2)))
        self.replot()
