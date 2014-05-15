# -*- coding: utf-8 -*-

import types

import numpy as np


from PyQt4.QtGui import (QDialog, QGridLayout, QSlider, QLabel, QCheckBox, QWidget,
                         QLineEdit, QFrame, QSizePolicy, QHBoxLayout, QPushButton, QMenuBar,
                         QAction, QMenu, QKeySequence, QVBoxLayout, QFileDialog, QPixmap, QPainter,
                         QTableWidget, QPen, QBrush, QColor, QPolygonF, QTransform,
                         QTableWidgetItem, QSplitter, QHeaderView, QSpacerItem, QTextDocument)

from PyQt4.QtCore import (Qt, SIGNAL, QRectF, QPointF, pyqtSignal)
from PyQt4.QtWebKit import (QWebView, QWebSettings)
from PyQt4.Qwt5 import (QwtScaleDraw, QwtText)


import guidata


from guiqwt.builder import make
from guiqwt.config import CONF
from guiqwt.events import (KeyEventMatch, QtDragHandler, PanHandler, MoveHandler, ZoomHandler,)
from guiqwt.interfaces import IBasePlotItem, IShapeItemType
from guiqwt.image import ImagePlot, RawImageItem
from guiqwt.label import ObjectInfo
from guiqwt.plot import ImageWidget
from guiqwt.shapes import RectangleShape, AbstractShape, QwtPlotItem
from guiqwt.signals import (SIG_MOVE, SIG_START_TRACKING, SIG_STOP_NOT_MOVING, SIG_STOP_MOVING,
                            SIG_PLOT_AXIS_CHANGED, )
from guiqwt.tools import SelectTool, InteractiveTool
from guiqwt.transitional import QwtSymbol

from helpers import protect_signal_handler

from ..lib.data_structures import Feature, PeakRange, PeakMap

from utils import set_x_axis_scale_draw, set_y_axis_scale_draw

from lru_cache import lru_cache


class PeakMapImageBase(object):

    def __init__(self, peakmaps):
        self.peakmaps = peakmaps
        ranges = [pm.get_ranges() for pm in peakmaps if len(pm)]
        if ranges:  # list might be empty
            rtmins, rtmaxs, mzmins, mzmaxs, iimins, iimaxs = zip(*ranges)
            self.rtmin = min(rtmins)
            self.rtmax = max(rtmaxs)
            self.mzmin = min(mzmins)
            self.mzmax = max(mzmaxs)
            self.imax = max(iimaxs)

        else:
            self.rtmin = self.rtmax = self.mzmin = self.mzmax = self.imax = 0.0

        self.bounds = QRectF(QPointF(self.rtmin, self.mzmin), QPointF(self.rtmax, self.mzmax))

        self.imin = 0.0
        self.upper_limit_imax = self.imax
        self.gamma = 1.0
        self.log_scale = 1

        self.cached_matrix = None

    def get_peakmap_bounds(self):
        return self.rtmin, self.rtmax, self.mzmin, self.mzmax

    def set_processing_parameters(self, parameters):
        self.set_gamma(parameters.gamma)
        self.set_logarithmic_scale(parameters.log_scale)
        self.set_imin(parameters.imin)
        self.set_imax(parameters.imax)

    def set_gamma(self, gamma):
        self.gamma = gamma

    def set_logarithmic_scale(self, log_scale):
        self.log_scale = log_scale

    def set_imin(self, imin):
        self.imin = imin

    def set_imax(self, imax):
        self.imax = imax

    def get_gamma(self):
        return self.gama

    @lru_cache(maxsize=100)
    # NX = 400, NX = 300 -> per image 300 * 400 * 1 byte = 12e4 bytes
    # 100 images in cache: 12e6 bytes = 12 mb
    def compute_image(self, idx, NX, NY, rtmin, rtmax, mzmin, mzmax):

        if rtmin >= rtmax or mzmin >= mzmax:
            smoothed = np.zeros((1, 1))
        else:
            # optimized:
            # one additional row / col as we loose one row and col during smoothing:
            #data = sample_image(self.peakmaps[idx], rtmin, rtmax, mzmin, mzmax, NX + 1, NY + 1)
            data = self.peakmaps[idx].sample_image(rtmin, rtmax, mzmin, mzmax, NX + 1, NY + 1, 1)

            # enlarge single pixels to 2 x 2 pixels:
            smoothed = data[:-1, :-1] + data[:-1, 1:] + data[1:, :-1] + data[1:, 1:]

        # turn up/down
        smoothed = smoothed[::-1, :]
        imin = self.imin
        imax = self.imax

        if self.log_scale:
            smoothed = np.log(1.0 + smoothed)
            imin = np.log(1.0 + imin)
            imax = np.log(1.0 + imax)

        smoothed[smoothed < imin] = imin
        smoothed[smoothed > imax] = imax
        smoothed -= imin

        # scale to 1.0
        maxd = np.max(smoothed)
        if maxd:
            smoothed /= maxd

        # apply gamma
        smoothed = smoothed ** (self.gamma) * 255
        to_plot = smoothed.astype(np.uint8)
        return to_plot


class PeakMapImageItem(PeakMapImageBase, RawImageItem):

    """ draws peakmap 2d view dynamically based on given limits """

    def __init__(self, peakmap):

        RawImageItem.__init__(self, data=np.zeros((1, 1), np.uint8))
        PeakMapImageBase.__init__(self, [peakmap])

        self.update_border()
        self.IMAX = 255
        self.set_lut_range([0, self.IMAX])
        self.set_color_map("hot")

        self.last_canvas_rect = None
        self.last_src_rect = None
        self.last_dst_rect = None
        self.last_xmap = None
        self.last_ymap = None

    def paint_pixmap(self, widget):
        assert self.last_canvas_rect is not None
        x1, y1 = self.last_canvas_rect.left(), self.last_canvas_rect.top()
        x2, y2 = self.last_canvas_rect.right(), self.last_canvas_rect.bottom()

        NX = x2 - x1
        NY = y2 - y1
        pix = QPixmap(NX, NY)
        painter = QPainter(pix)
        painter.begin(widget)
        try:
            self.draw_border(painter, self.last_xmap, self.last_ymap, self.last_canvas_rect)
            self.draw_image(painter, self.last_canvas_rect, self.last_src_rect, self.last_dst_rect,
                            self.last_xmap, self.last_xmap)
            # somehow guiqwt paints a distorted border at left/top, so we remove it:
            return pix.copy(2, 2, NX - 2, NY - 2)
        finally:
            painter.end()

    #---- QwtPlotItem API ------------------------------------------------------
    def draw_image(self, painter, canvasRect, srcRect, dstRect, xMap, yMap):

        # normally we use this method indirectly from quiqwt which takes the burden of constructing
        # the right parameters. if we want to call this method manually, eg for painting on on a
        # QPixmap for saving the image, we just use the last set of parmeters passed to this
        # method, this is much easier than constructing the params seperatly, and so we get the
        # exact same result as we see on screen:
        self.last_canvas_rect = canvasRect
        self.last_src_rect = srcRect
        self.last_dst_rect = dstRect
        self.last_xmap = xMap
        self.last_ymap = yMap

        x1, y1 = canvasRect.left(), canvasRect.top()
        x2, y2 = canvasRect.right(), canvasRect.bottom()
        NX = x2 - x1
        NY = y2 - y1
        rtmin, mzmax, rtmax, mzmin = srcRect

        self.data = self.compute_image(0, NX, NY, rtmin, rtmax, mzmin, mzmax)

        # draw
        srcRect = (0, 0, NX, NY)
        x1, y1, x2, y2 = canvasRect.getCoords()
        RawImageItem.draw_image(self, painter, canvasRect, srcRect, (x1, y1, x2, y2), xMap, yMap)


class PeakmapCursorRangeInfo(ObjectInfo):

    def __init__(self, marker):
        ObjectInfo.__init__(self)
        self.marker = marker

    def get_text(self):
        rtmin, mzmin, rtmax, mzmax = self.marker.get_rect()
        if not np.isnan(rtmax):
            rtmin, rtmax = sorted((rtmin, rtmax))
        if not np.isnan(mzmax):
            mzmin, mzmax = sorted((mzmin, mzmax))
        if not np.isnan(rtmax):
            delta_mz = mzmax - mzmin
            delta_rt = rtmax - rtmin
            line0 = "mz: %10.5f ..  %10.5f (delta=%5.5f)" % (mzmin, mzmax, delta_mz)
            line1 = "rt:  %6.2fm   ..   %6.2fm   (delta=%.1fs)" % (rtmin / 60.0,
                                                                   rtmax / 60.0,
                                                                   delta_rt)
            return "<pre>%s</pre>" % "<br>".join((line0, line1))
        else:
            return """<pre>mz: %9.5f<br>rt: %6.2fm</pre>""" % (mzmin, rtmin / 60.0)


class PeakmapZoomTool(InteractiveTool):

    """ selects rectangle from peakmap """

    TITLE = "Selection"
    ICON = "selection.png"
    CURSOR = Qt.CrossCursor

    def setup_filter(self, baseplot):
        filter_ = baseplot.filter
        # Initialisation du filtre

        start_state = filter_.new_state()
        filter_.add_event(start_state,
                         KeyEventMatch((Qt.Key_Backspace, Qt.Key_Escape, Qt.Key_Home)),
                         baseplot.reset_zoom_to_full_map, start_state)

        filter_.add_event(start_state,
                         KeyEventMatch((Qt.Key_Space,)), baseplot.reset_zoom_to_initial_view,
                         start_state)

        handler = QtDragHandler(filter_, Qt.LeftButton, start_state=start_state)
        self.connect(handler, SIG_MOVE, baseplot.move_in_drag_mode)
        self.connect(handler, SIG_START_TRACKING, baseplot.start_drag_mode)
        self.connect(handler, SIG_STOP_NOT_MOVING, baseplot.stop_drag_mode)
        self.connect(handler, SIG_STOP_MOVING, baseplot.stop_drag_mode)

        handler = QtDragHandler(
            filter_, Qt.LeftButton, start_state=start_state, mods=Qt.ShiftModifier)
        self.connect(handler, SIG_MOVE, baseplot.move_in_drag_mode)
        self.connect(handler, SIG_START_TRACKING, baseplot.start_drag_mode)
        self.connect(handler, SIG_STOP_NOT_MOVING, baseplot.stop_drag_mode)
        self.connect(handler, SIG_STOP_MOVING, baseplot.stop_drag_mode)

        # Bouton du milieu
        PanHandler(filter_, Qt.MidButton, start_state=start_state)
        PanHandler(filter_, Qt.LeftButton, mods=Qt.AltModifier, start_state=start_state)
        # AutoZoomHandler(filter_, Qt.MidButton, start_state=start_state)

        # Bouton droit
        ZoomHandler(filter_, Qt.RightButton, start_state=start_state)
        ZoomHandler(filter_, Qt.LeftButton, mods=Qt.ControlModifier, start_state=start_state)
        # MenuHandler(filter_, Qt.RightButton, start_state=start_state)

        # Autres (touches, move)
        MoveHandler(filter_, start_state=start_state)
        MoveHandler(filter_, start_state=start_state, mods=Qt.ShiftModifier)
        MoveHandler(filter_, start_state=start_state, mods=Qt.AltModifier)

        return start_state


class ModifiedImagePlot(ImagePlot):

    """ special handlers for dragging selection, source is PeakmapZoomTool """

    # as this class is used for patching, the __init__ is never called, so we set default
    # values as class atributes:

    rtmin = rtmax = mzmin = mzmax = imin = imax = None
    peakmap_range = (None, None, None, None, None, None)
    coords = (None, None)
    dragging = False

    chromatogram_plot = None
    mz_plot = None

    def set_initial_image_limits(self, rtmin, rtmax, mzmin, mzmax):
        #  sollte man später durch history funktion ersetzen könnnen..
        self.rtmin = max(rtmin, self.peakmap_range[0])
        self.rtmax = min(rtmax, self.peakmap_range[1])
        self.mzmin = max(mzmin, self.peakmap_range[2])
        self.mzmax = min(mzmax, self.peakmap_range[3])
        self.update_image_limits(self.rtmin, self.rtmax, self.mzmin, self.mzmax)

    def update_image_limits(self, rtmin, rtmax, mzmin, mzmax):
        rtmin = max(rtmin, self.peakmap_range[0])
        rtmax = min(rtmax, self.peakmap_range[1])
        mzmin = max(mzmin, self.peakmap_range[2])
        mzmax = min(mzmax, self.peakmap_range[3])
        self.set_plot_limits(rtmin, rtmax, mzmin, mzmax, "bottom", "right")
        self.set_plot_limits(rtmin, rtmax, mzmin, mzmax, "top", "left")

        self.replot()
        self.emit(SIG_PLOT_AXIS_CHANGED, self)

    def get_coords(self, evt):
        return self.invTransform(self.xBottom, evt.x()), self.invTransform(self.yLeft, evt.y())

    def get_items_of_class(self, clz):
        for item in self.items:
            if item.__class__ == clz:
                yield item

    def get_unique_item(self, clz):
        items = set(self.get_items_of_class(clz))
        if len(items) == 0:
            return None
        if len(items) != 1:
            raise Exception("%d instance(s) of %s among CurvePlots items !" % (len(items), clz))
        return items.pop()

    @protect_signal_handler
    def reset_zoom_to_full_map(self, filter_, evt):
        rtmin = self.peakmap_range[0]
        rtmax = self.peakmap_range[1]
        mzmin = self.peakmap_range[2]
        mzmax = self.peakmap_range[3]
        self.update_image_limits(rtmin, rtmax, mzmin, mzmax)

    @protect_signal_handler
    def reset_zoom_to_initial_view(self, filter_, evt):
        self.update_image_limits(self.rtmin, self.rtmax, self.mzmin, self.mzmax)

    @protect_signal_handler
    def start_drag_mode(self, filter_, evt):
        self.start_at = self.get_coords(evt)
        self.moved = False
        self.dragging = True
        marker = self.get_unique_item(RectangleShape)
        marker.set_rect(self.start_at[0], self.start_at[1], self.start_at[0], self.start_at[1])
        self.cross_marker.setVisible(False)  # no cross marker when dragging
        self.rect_label.setVisible(1)
        self.with_shift_key = evt.modifiers() == Qt.ShiftModifier
        self.replot()

    @protect_signal_handler
    def move_in_drag_mode(self, filter_, evt):
        now = self.get_coords(evt)
        marker = self.get_unique_item(RectangleShape)
        marker.setVisible(1)
        now_rt = max(self.peakmap_range[0], min(now[0], self.peakmap_range[1]))
        now_mz = max(self.peakmap_range[2], min(now[1], self.peakmap_range[3]))
        marker.set_rect(self.start_at[0], self.start_at[1], now_rt, now_mz)
        self.moved = True
        self.replot()

    def mouseReleaseEvent(self, evt):
        # stop drag mode is not called immediatly when dragging and releasing shift
        # during dragging.
        if self.dragging:
            self.stop_drag_mode(None, evt)

    @protect_signal_handler
    def stop_drag_mode(self, filter_, evt):
        stop_at = self.get_coords(evt)
        marker = self.get_unique_item(RectangleShape)
        marker.setVisible(0)

        # reactivate cursor
        self.cross_marker.set_pos(stop_at[0], stop_at[1])
        self.cross_marker.setZ(self.get_max_z() + 1)

        # passing None here arives as np.nan if you call get_rect later, so we use
        # np.nan here:
        marker.set_rect(stop_at[0], stop_at[1], np.nan, np.nan)

        self.dragging = False

        if self.moved and not self.with_shift_key:
            rtmin, rtmax = self.start_at[0], stop_at[0]
            # be sure that rtmin <= rtmax:
            rtmin, rtmax = min(rtmin, rtmax), max(rtmin, rtmax)

            mzmin, mzmax = self.start_at[1], stop_at[1]
            # be sure that mzmin <= mzmax:
            mzmin, mzmax = min(mzmin, mzmax), max(mzmin, mzmax)

            # keep coordinates in peakmap:
            rtmin = max(self.peakmap_range[0], min(self.peakmap_range[1], rtmin))
            rtmax = max(self.peakmap_range[0], min(self.peakmap_range[1], rtmax))
            mzmin = max(self.peakmap_range[2], min(self.peakmap_range[3], mzmin))
            mzmax = max(self.peakmap_range[2], min(self.peakmap_range[3], mzmax))

            self.update_image_limits(rtmin, rtmax, mzmin, mzmax)
        else:
            self.replot()

    @protect_signal_handler
    def do_zoom_view(self, dx, dy, lock_aspect_ratio=False):
        """
        modified version of do_zoom_view from base class,
        we restrict zooming and panning to ranges of peakmap.

        Change the scale of the active axes (zoom/dezoom) according to dx, dy
        dx, dy are tuples composed of (initial pos, dest pos)
        We try to keep initial pos fixed on the canvas as the scale changes
        """
        # See guiqwt/events.py where dx and dy are defined like this:
        #   dx = (pos.x(), self.last.x(), self.start.x(), rct.width())
        #   dy = (pos.y(), self.last.y(), self.start.y(), rct.height())
        # where:
        #   * self.last is the mouse position seen during last event
        #   * self.start is the first mouse position (here, this is the
        #     coordinate of the point which is at the center of the zoomed area)
        #   * rct is the plot rect contents
        #   * pos is the current mouse cursor position
        auto = self.autoReplot()
        self.setAutoReplot(False)
        dx = (-1,) + dx  # adding direction to tuple dx
        dy = (1,) + dy  # adding direction to tuple dy
        if lock_aspect_ratio:
            direction, x1, x0, start, width = dx
            F = 1 + 3 * direction * float(x1 - x0) / width
        axes_to_update = self.get_axes_to_update(dx, dy)

        axis_ids_horizontal = (self.get_axis_id("bottom"), self.get_axis_id("top"))
        axis_ids_vertical = (self.get_axis_id("left"), self.get_axis_id("right"))

        for (direction, x1, x0, start, width), axis_id in axes_to_update:
            lbound, hbound = self.get_axis_limits(axis_id)
            if not lock_aspect_ratio:
                F = 1 + 3 * direction * float(x1 - x0) / width
            if F * (hbound - lbound) == 0:
                continue
            if self.get_axis_scale(axis_id) == 'lin':
                orig = self.invTransform(axis_id, start)
                vmin = orig - F * (orig - lbound)
                vmax = orig + F * (hbound - orig)
            else:  # log scale
                i_lbound = self.transform(axis_id, lbound)
                i_hbound = self.transform(axis_id, hbound)
                imin = start - F * (start - i_lbound)
                imax = start + F * (i_hbound - start)
                vmin = self.invTransform(axis_id, imin)
                vmax = self.invTransform(axis_id, imax)

            # patch for not "zooming out"
            if axis_id in axis_ids_horizontal:
                vmin = max(vmin, self.peakmap_range[0])
                vmax = min(vmax, self.peakmap_range[1])
            elif axis_id in axis_ids_vertical:
                vmin = max(vmin, self.peakmap_range[2])
                vmax = min(vmax, self.peakmap_range[3])

            self.set_axis_limits(axis_id, vmin, vmax)

        self.setAutoReplot(auto)
        # the signal MUST be emitted after replot, otherwise
        # we receiver won't see the new bounds (don't know why?)
        self.replot()
        self.emit(SIG_PLOT_AXIS_CHANGED, self)

    @protect_signal_handler
    def do_pan_view(self, dx, dy):
        """
        modified version of do_pan_view from base class,
        we restrict zooming and panning to ranges of peakmap.

        Translate the active axes by dx, dy
        dx, dy are tuples composed of (initial pos, dest pos)
        """
        auto = self.autoReplot()
        self.setAutoReplot(False)
        axes_to_update = self.get_axes_to_update(dx, dy)
        axis_ids_horizontal = (self.get_axis_id("bottom"), self.get_axis_id("top"))
        axis_ids_vertical = (self.get_axis_id("left"), self.get_axis_id("right"))

        for (x1, x0, _start, _width), axis_id in axes_to_update:
            lbound, hbound = self.get_axis_limits(axis_id)
            i_lbound = self.transform(axis_id, lbound)
            i_hbound = self.transform(axis_id, hbound)
            delta = x1 - x0
            vmin = self.invTransform(axis_id, i_lbound - delta)
            vmax = self.invTransform(axis_id, i_hbound - delta)
            # patch for not "panning out"
            if axis_id in axis_ids_horizontal:
                vmin = max(vmin, self.peakmap_range[0])
                vmax = min(vmax, self.peakmap_range[1])
            elif axis_id in axis_ids_vertical:
                vmin = max(vmin, self.peakmap_range[2])
                vmax = min(vmax, self.peakmap_range[3])
            self.set_axis_limits(axis_id, vmin, vmax)

        self.setAutoReplot(auto)
        # the signal MUST be emitted after replot, otherwise
        # we receiver won't see the new bounds (don't know why?)
        self.replot()
        self.emit(SIG_PLOT_AXIS_CHANGED, self)

    cursorMoved = pyqtSignal(float, float)

    @protect_signal_handler
    def do_move_marker(self, evt):
        super(ModifiedImagePlot, self).do_move_marker(evt)
        rt = self.invTransform(self.xBottom, evt.x())
        mz = self.invTransform(self.yLeft, evt.y())
        self.cursorMoved.emit(rt, mz)


def get_range(*peakmaps):

    rtmins = []
    rtmaxs = []
    mzmins = []
    mzmaxs = []
    iimins = []
    iimaxs = []
    for peakmap in peakmaps:
        if peakmap is not None and len(peakmap):
            ranges = peakmap.get_ranges()
            rtmins.append(ranges[0])
            rtmaxs.append(ranges[1])
            mzmins.append(ranges[2])
            mzmaxs.append(ranges[3])
            iimins.append(ranges[4])
            iimaxs.append(ranges[5])

    if len(rtmins):
        return min(rtmins), max(rtmaxs), min(mzmins), max(mzmaxs), min(iimins), max(iimaxs)
    return 0.0, 0.0, 0.0, 0.0, 0.0, 0.0


def create_image_widget():
    # patched plot in widget
    widget = ImageWidget(lock_aspect_ratio=False, xlabel="rt", ylabel="m/z")

    # patch memeber's methods:
    widget.plot.__class__ = ModifiedImagePlot
    widget.plot.set_axis_direction("left", False)
    widget.plot.set_axis_direction("right", False)

    set_x_axis_scale_draw(widget)
    set_y_axis_scale_draw(widget)
    widget.plot.enableAxis(widget.plot.colormap_axis, False)

    return widget


class LabeledPolygonShape(QwtPlotItem):

    __implements__ = (IBasePlotItem,)

    # we implemented IBasePlotItem because guiqwt manages these objects in a consistent way
    # although we have to implement many empty methods below for conforming to IBasePlotItem
    # API.

    def __init__(self, item, label=None):
        super(LabeledPolygonShape, self).__init__()  # feature.rtmin, feature.rtmax,
                                                     # feature.mzmin, feature.mzmax)
        self.item = item
        self.label = label

    # <IBasePlotItem API>

    selected = False

    do_nothing = lambda *a, **kw: None

    set_resizable = set_movable = set_rotatable = set_read_only = set_private = set_selectable\
                  = select = unselect = set_item_parameters = get_item_parameter\
                  = move_local_point_to = move_local_shape = move_with_selection = do_nothing

    return_false = lambda *a, **kw: False

    can_resize = cat_move = can_rotate = is_readonly = is_private = can_select = return_false

    def types(self):
        return (IShapeItemType,)

    def hit_test(self, pos):
        return 99999.99, 0, False, None

    # </IBasePlotItem API>

    # somehow light blue which contasts to the yellow/red/black colors of the peakmap:
    color = (170, 220, 255)

    def _set_inner_pen_and_brush(self, painter, xMap, yMap):
        r, g, b = self.color
        pen = QPen(QColor(r, g, b, 255), 1.0)
        brush = QBrush()
        painter.setPen(pen)
        painter.setBrush(brush)

    def _set_outer_pen_and_brush(self, painter, xMap, yMap):
        r, g, b = self.color
        pen = QPen()
        brush = QBrush(QColor(r, g, b, 80))
        painter.setPen(pen)
        painter.setBrush(brush)

    def _draw_polygon(self, painter, xMap, yMap, range_tuple):
        # range_tuple might contain more then four values !
        rtmin, rtmax, mzmin, mzmax = range_tuple[:4]
        points = QPolygonF()
        points.append(QPointF(xMap.transform(rtmin), yMap.transform(mzmin)))
        points.append(QPointF(xMap.transform(rtmin), yMap.transform(mzmax)))
        points.append(QPointF(xMap.transform(rtmax), yMap.transform(mzmax)))
        points.append(QPointF(xMap.transform(rtmax), yMap.transform(mzmin)))
        painter.drawPolygon(points)
        return points

    def _setup_painter(self, painter):
        painter.setRenderHint(QPainter.Antialiasing)


class PeakRangeShape(LabeledPolygonShape):

    def draw(self, painter, xMap, yMap, canvasRect):
        self._setup_painter(painter)
        self._set_inner_pen_and_brush(painter, xMap, yMap)
        self._draw_polygon(painter, xMap, yMap, self.item)

        if self.label is not None:
            self._draw_label(painter, xMap, yMap)

    def _draw_label(self, painter, xMap, yMap):
        self.text = QTextDocument()
        self.text.setDefaultStyleSheet("""div { color: rgb(%d, %d, %d); }""" % self.color)
        self.text.setHtml("<div>%s</div>" % (self.label, ))

        x0 = xMap.transform(self.item.rtmax)
        # y0: height between m0 and m1 masstrace if m1 exists, else at height of m0
        y0 = yMap.transform(0.5 * self.item.mzmin + 0.5 * self.item.mzmax)
        h = self.text.size().height()
        painter.translate(x0, y0 - 0.5 * h)
        self.text.drawContents(painter)


class FeatureShape(LabeledPolygonShape):

    def draw(self, painter, xMap, yMap, canvasRect):
        self._setup_painter(painter)

        self._set_outer_pen_and_brush(painter, xMap, yMap)
        rtmin = self.item.rtmin
        rtmax = self.item.rtmax
        mzmin = self.item.mzmin
        mzmax = self.item.mzmax
        self._draw_polygon(painter, xMap, yMap, (rtmin, rtmax, mzmin, mzmax))

        self._set_inner_pen_and_brush(painter, xMap, yMap)
        for mass_trace in self.item.mass_traces:
            self._draw_polygon(painter, xMap, yMap, mass_trace)

        if self.label is not None:
            self._draw_label(painter, xMap, yMap)

    def _draw_label(self, painter, xMap, yMap):
        self.text = QTextDocument()
        self.text.setDefaultStyleSheet("""div { color: rgb(%d, %d, %d); }""" % self.color)
        self.text.setHtml("<div>%s</div>" % (self.label, ))

        x0 = xMap.transform(self.item.rtmax)
        # y0: height between m0 and m1 masstrace if m1 exists, else at height of m0
        yi = sorted(m.mzmin for m in self.item.mass_traces)
        if len(yi) >= 2:
            y0 = yMap.transform(0.5 * yi[0] + 0.5 * yi[1])
        else:
            y0 = yMap.transform(yi[0])
        h = self.text.size().height()
        painter.translate(x0, y0 - 0.5 * h)
        self.text.drawContents(painter)

class PeakmapPlotter(QWidget):

    def __init__(self, parent):
        super(PeakmapPlotter, self).__init__(parent)
        self.layout = QGridLayout(self)
        self.widget = create_image_widget()
        self.image_item = None
        self.extra_items = []

        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.widget.setSizePolicy(sizePolicy)

        left, top, right, bottom = 0, 0, 0, 0
        self.widget.setContentsMargins(left, top, right, bottom)
        self.layout.setContentsMargins(left, top, right, bottom)
        self.layout.addWidget(self.widget, 0, 0, 1, 1)

        self.widget.plot.cursorMoved.connect(self.marker_moved)

        self.clear()

    def clear(self):

        pm = PeakMap([])
        self.set_peakmaps(pm, None)

    cursorMoved = pyqtSignal(float, float)
    cursorMovedRt = pyqtSignal(float)
    cursorMovedMz = pyqtSignal(float)

    def marker_moved(self, rt, mz):
        self.cursorMoved.emit(rt, mz)
        self.cursorMovedRt.emit(rt)
        self.cursorMovedMz.emit(mz)

    def plot_feature(self, peakmap, feature, hit):
        self.set_peakmaps(peakmap, None, [(feature, hit.aa_sequence)])
        self.widget.plot.set_initial_image_limits(feature.rtmin - 30.0, feature.rtmax + 30.0,
                                                  feature.mzmin - 10.0, feature.mzmax + 10.0)

    def plot_mass_trace(self, peakmap, rtmin, rtmax, mzmin, mzmax, aa_sequence):
        item = PeakRange(rtmin, rtmax, mzmin, mzmax)
        self.set_peakmaps(peakmap, None, [(item, aa_sequence)])
        self.widget.plot.set_initial_image_limits(rtmin - 10.0, rtmax + 10.0, mzmin - 3.0,
                                                  mzmax + 3.0)

    def set_peakmaps(self, peakmap, peakmap2, extra_items=None):

        self.peakmap = peakmap
        self.peakmap2 = peakmap2

        # only makes sense for gamma, after reload imin/imax and rt/mz bounds will not be
        # valid any more

        if peakmap2 is not None:
            pass
            #self.image_item = RGBPeakMapImageItem(peakmap, peakmap2)
        else:
            self.image_item = PeakMapImageItem(peakmap)

        self.widget.plot.peakmap_range = get_range(peakmap, peakmap2)
        self.widget.plot.del_all_items()
        self.widget.plot.add_item(self.image_item)
        if extra_items is not None:
            for item, label in extra_items:
                if isinstance(item, Feature):
                    self.widget.plot.add_item(FeatureShape(item, label))
                if isinstance(item, PeakRange):
                    self.widget.plot.add_item(PeakRangeShape(item, label))
        # widget.plot.reset_history()
        self.create_peakmap_labels()
        # for zooming and panning with mouse drag:
        t = self.widget.add_tool(SelectTool)
        self.widget.set_default_tool(t)
        t.activate()
        # for selecting zoom window
        t = self.widget.add_tool(PeakmapZoomTool)
        t.activate()

    def move_marker_to_rt(self, rt):
        __, mz = self.cross_marker.get_pos()
        self.cross_marker.set_pos(rt, mz)
        self.replot()

    def create_peakmap_labels(self):
        plot = self.widget.plot
        rect_marker = RectangleShape()
        rect_label = make.info_label("TR", [PeakmapCursorRangeInfo(rect_marker)], title=None)
        rect_label.labelparam.label = ""
        rect_label.setVisible(1)
        plot.rect_label = rect_label
        plot.add_item(rect_label)

        params = {
            "shape/drag/symbol/size": 0,
            "shape/drag/line/color": "#cccccc",
            "shape/drag/line/width": 1.5,
            "shape/drag/line/alpha": 0.4,
            "shape/drag/line/style": "SolidLine",

        }
        CONF.update_defaults(dict(plot=params))
        rect_marker.shapeparam.read_config(CONF, "plot", "shape/drag")
        rect_marker.shapeparam.update_shape(rect_marker)
        rect_marker.setVisible(0)
        rect_marker.set_rect(0, 0, np.nan, np.nan)
        plot.add_item(rect_marker)

        plot.canvas_pointer = True  # x-cross marker on
        # we hack label_cb for updating legend:

        def label_cb(rt, mz):
            # passing None here arives as np.nan if you call get_rect later, so we use
            # np.nan here:
            rect_marker.set_rect(rt, mz, np.nan, np.nan)
            return ""

        cross_marker = plot.cross_marker
        cross_marker.label_cb = label_cb
        params = {
            "marker/cross/line/color": "#cccccc",
            "marker/cross/line/width": 1.5,
            "marker/cross/line/alpha": 0.4,
            "marker/cross/line/style": "DashLine",
            "marker/cross/symbol/marker": "NoSymbol",
            "marker/cross/markerstyle": "Cross",
        }
        CONF.update_defaults(dict(plot=params))
        cross_marker.markerparam.read_config(CONF, "plot", "marker/cross")
        cross_marker.markerparam.update_marker(cross_marker)

        self.cross_marker = cross_marker
        self.rect_marker = rect_marker


    def clear_plot(self):
        self.widget.plot.del_all_items()
        self.replot()

    def replot(self):
        self.widget.plot.replot()

    def __getattr__(self, name):
        return getattr(self.widget.plot, name)

    def get_plot(self):
        return self.widget.plot

    def paint_pixmap(self):
        return self.image_item.paint_pixmap(self.widget)

    def set_processing_parameters(self, parameters):
        self.image_item.set_processing_parameters(parameters)
        self.replot()


class PeakMapExplorer(QDialog):

    def __init__(self, parent=None):
        super(PeakMapExplorer, self).__init__(parent)
        self.setWindowFlags(Qt.Window)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowFlags(Qt.Window)

    def keyPressEvent(self, e):
        if e.key() != Qt.Key_Escape:
            super(PeakMapExplorer, self).keyPressEvent(e)

    def setup(self, peakmap, peakmap2=None, extra_items=None):
        self.setup_widgets_and_layout()
        self.connect_signals_and_slots()
        self.setup_peakmap_plotter(peakmap, peakmap2, extra_items)
        self.setup_processing_parameters()
        self.plot_peakmap()

    def connect_signals_and_slots(self):
        self.params.paramsChanged.connect(self.peakmap_plotter.set_processing_parameters)

    def setup_processing_parameters(self):
        self.params.setup_initial_values(gamma_min=0.05,
                                         gamma_max=10.0,
                                         gamma_start=4.0,
                                         log_scale=True,
                                         imin=self.imin,
                                         imax=self.imax)

    def setup_peakmap_plotter(self, peakmap, peakmap2, extra_items):

        self.peakmap = peakmap  # .getDominatingPeakmap()
        self.dual_mode = peakmap2 is not None
        self.peakmap2 = peakmap2
        if self.dual_mode:
            self.peakmap2 = peakmap2.getDominatingPeakmap()

        (self.rtmin, self.rtmax, self.mzmin, self.mzmax,
                                 self.imin, self.imax) = get_range(peakmap, peakmap2)

        # jparam = PeakMapProcessingParameters(self.params.gamma_start, True, 0, self.imax)
        # self.peakmap_plotter.set_processing_parameters(param)


    def plot_peakmap(self):
        # includes replot:
        self.peakmap_plotter.update_image_limits(self.rtmin, self.rtmax, self.mzmin, self.mzmax)

    def setup_widgets_and_layout(self):

        sizePolicy = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(sizePolicy)

        self.gridLayout = QGridLayout(self)
        self.splitter = QSplitter(self)
        self.splitter.setOrientation(Qt.Horizontal)

        self.peakmap_plotter = PeakmapPlotter(self.splitter)

        self.verticalLayoutWidget = QWidget(self.splitter)
        self.verticalLayout = QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setMargin(0)

        self.params = PeakMapScalingParameters(self.verticalLayoutWidget)
        sizePolicy = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.params.sizePolicy().hasHeightForWidth())
        self.params.setSizePolicy(sizePolicy)

        self.verticalLayout.addWidget(self.params)

        spacerItem = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.MinimumExpanding)
        self.verticalLayout.addItem(spacerItem)
        self.gridLayout.addWidget(self.splitter, 0, 0, 1, 1)



def inspectPeakMap(peakmap, peakmap2=None, extra_items=None, table=None, modal=True, parent=None):
    """
    allows the visual inspection of a peakmap
    """

    app = guidata.qapplication()  # singleton !
    win = PeakMapExplorer(parent=parent)
    win.setup(peakmap, peakmap2, extra_items)
    if modal:
        win.raise_()
        win.exec_()
    else:
        win.show()


if __name__ == "__main__":
    from ivi.lib.compress_io import CompressedDataReader
    print "open"
    dr = CompressedDataReader("/Users/uweschmitt/data/dose/collected.ivi")
    print "opened"
    for base_name in dr.get_base_names():
        print base_name
        pm = dr.fetch_peak_map(base_name)
        if pm.spectra:
            print "data loaded from", base_name
            hits = dr.get_hits_for_base_name(base_name)
            features = []
            for i, hit in enumerate(hits):
                if len(features) < 50:
                    for f in dr.fetch_features_for_hit(hit):
                        features.append(f)
            inspectPeakMap(pm, extra_items=features)
            break
    else:
        raise Exception("peakmap is empty")
