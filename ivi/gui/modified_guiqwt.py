import pdb
from exceptions import Exception
from PyQt4.QtCore import Qt, QPoint, pyqtSignal, QObject
from PyQt4.QtGui import QPainter
from guiqwt.curve import CurvePlot, CurveItem
from guiqwt.events import ObjectHandler, KeyEventMatch, QtDragHandler
from guiqwt.signals import (SIG_MOVE, SIG_START_TRACKING, SIG_STOP_NOT_MOVING, SIG_STOP_MOVING,
                            SIG_RANGE_CHANGED, SIG_PLOT_AXIS_CHANGED)

from guiqwt.events import ZoomHandler, PanHandler, MoveHandler, DragHandler

from guiqwt.tools import InteractiveTool, SelectTool

from guiqwt.shapes import Marker, SegmentShape, XRangeSelection
import numpy as np

from helpers import protect_signal_handler
from emzed_optimizations import sample_peaks



class RtSelectionTool(InteractiveTool):
    """
        modified event handling:
            - enter, space, backspace, lift crsr and right crsr keys trigger handlers in baseplot
    """
    TITLE = "Rt Selection"
    ICON = "selection.png"
    CURSOR = Qt.ArrowCursor

    def setup_filter(self, baseplot):
        filter = baseplot.filter
        # Initialisation du filtre
        start_state = filter.new_state()
        # Bouton gauche :
        ObjectHandler(filter, Qt.LeftButton, start_state=start_state)
        ObjectHandler(filter, Qt.LeftButton, mods=Qt.ControlModifier,
                      start_state=start_state, multiselection=True)

        filter.add_event(start_state,
                         KeyEventMatch((Qt.Key_Enter, Qt.Key_Return,)),

                         baseplot.do_enter_pressed, start_state)

        filter.add_event(start_state,
                         KeyEventMatch((Qt.Key_Space,)),
                         baseplot.do_space_pressed, start_state)

        filter.add_event(start_state,
                         KeyEventMatch((Qt.Key_Right,)),
                         baseplot.do_right_pressed, start_state)

        filter.add_event(start_state,
                         KeyEventMatch((Qt.Key_Left,)),
                         baseplot.do_left_pressed, start_state)

        filter.add_event(start_state,
                         KeyEventMatch((Qt.Key_Backspace, Qt.Key_Escape)),
                         baseplot.reset_all_axes_evt, start_state)

        # Bouton du milieu
        PanHandler(filter, Qt.MidButton, start_state=start_state)

        # Bouton droit
        ZoomHandler(filter, Qt.RightButton, start_state=start_state)

        # Autres (touches, move)
        MoveHandler(filter, start_state=start_state)
        MoveHandler(filter, start_state=start_state, mods=Qt.ShiftModifier)
        MoveHandler(filter, start_state=start_state, mods=Qt.AltModifier)
        return start_state


class MzSelectionTool(InteractiveTool):
    """
       modified event handling:
           - space and backspac keys trigger handlers in baseplot
           - calling handlers for dragging with mouse
    """

    TITLE = "mz Selection"
    ICON = "selection.png"
    CURSOR = Qt.CrossCursor

    def setup_filter(self, baseplot):
        filter_ = baseplot.filter
        # Initialisation du filtre
        start_state = filter_.new_state()

        # start_state = filter_.new_state()
        handler = QtDragHandler(filter_, Qt.LeftButton, start_state=start_state)

        filter_.add_event(start_state,
                          KeyEventMatch((Qt.Key_Space,)),
                          baseplot.do_space_pressed, start_state)
        filter_.add_event(start_state,
                          KeyEventMatch((Qt.Key_Backspace, Qt.Key_Escape)),
                          baseplot.reset_all_axes_evt, start_state)

        filter_.add_event(start_state,
                          KeyEventMatch((Qt.Key_C,)),
                          baseplot.do_c_pressed, start_state)

        self.connect(handler, SIG_MOVE, baseplot.move_in_drag_mode)
        self.connect(handler, SIG_START_TRACKING, baseplot.start_drag_mode)
        self.connect(handler, SIG_STOP_NOT_MOVING, baseplot.stop_drag_mode)
        self.connect(handler, SIG_STOP_MOVING, baseplot.stop_drag_mode)

        # Bouton du milieu
        PanHandler(filter_, Qt.MidButton, start_state=start_state)
        PanHandler(filter_, Qt.LeftButton, mods=Qt.AltModifier, start_state=start_state)

        ZoomHandler(filter_, Qt.RightButton, start_state=start_state)
        ZoomHandler(filter_, Qt.LeftButton, mods=Qt.ControlModifier, start_state=start_state)

        # Autres (touches, move)
        MoveHandler(filter_, start_state=start_state)
        MoveHandler(filter_, start_state=start_state, mods=Qt.ShiftModifier)
        MoveHandler(filter_, start_state=start_state, mods=Qt.AltModifier)
        return start_state



class CurvePlotWithModifiedZoomHandling(CurvePlot):
    """ modifications:
            - zooming preserves x asix at bottom of plot
            - panning is only in x direction
            - handler for backspace, called by RtSelectionTool and MzSelectionTool
    """

    @protect_signal_handler
    def do_zoom_view(self, dx, dy, lock_aspect_ratio=False):
        """
        modified version of do_zoom_view from base class,
        we restrict zooming and panning to positive y-values

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

            # patch for not zooming into "negative space" ;) :
            if axis_id in axis_ids_vertical:
                vmin = 0
                if vmax < 0:
                    vmax = -vmax

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
        axis_ids_vertical = (self.get_axis_id("left"), self.get_axis_id("right"))

        for (x1, x0, _start, _width), axis_id in axes_to_update:
            lbound, hbound = self.get_axis_limits(axis_id)
            i_lbound = self.transform(axis_id, lbound)
            i_hbound = self.transform(axis_id, hbound)
            delta = x1 - x0
            vmin = self.invTransform(axis_id, i_lbound - delta)
            vmax = self.invTransform(axis_id, i_hbound - delta)
            # patch for not zooming into "negative space" ;) :
            if axis_id in axis_ids_vertical:
                vmin = 0
                if vmax < 0:
                    vmax = -vmax
            self.set_axis_limits(axis_id, vmin, vmax)

        self.setAutoReplot(auto)
        # the signal MUST be emitted after replot, otherwise
        # we receiver won't see the new bounds (don't know why?)
        self.replot()
        self.emit(SIG_PLOT_AXIS_CHANGED, self)

    @protect_signal_handler
    def reset_all_axes_evt(self, filter, evt):
        """ reset axes of plot """
        self.reset_x_limits()

    def reset_all_axes(self):
        self.reset_x_limits()

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

    def set_limit(self, ix, value):
        limits = list(self.get_plot_limits())
        limits[ix] = value
        self.set_plot_limits(*limits)

    def reset_x_limits(self, xmin=None, xmax=None, fac=1.0):
        xvals = []
        for item in self.items:
            if isinstance(item, CurveItem):
                x, _ = item.get_data()
                xvals.extend(list(x))
        if xmin is None:
            if len(xvals):
                xmin = min(xvals) / fac
            else:
                xmin = 0
        if xmax is None:
            if len(xvals):
                xmax = max(xvals) * fac
            else:
                xmax = 1.0
        self.update_plot_xlimits(xmin, xmax)

    def reset_y_limits(self, ymin=None, ymax=None, fac=1.2):
        yvals = []
        # xmin, xmax, _, _ = self.get_plot_limits()

        for item in self.items:
            if isinstance(item, CurveItem):
                x, y = item.get_data()
                yvals.extend(y)
        if ymin is None:
            if len(yvals) > 0:
                ymin = min(yvals) / fac
            else:
                ymin = 0
        if ymax is None:
            if len(yvals) > 0:
                ymax = max(yvals) * fac
            else:
                ymax = 1.0
        self.update_plot_ylimits(ymin, ymax)

    def update_plot_xlimits(self, xmin, xmax):
        _, _, ymin, ymax = self.get_plot_limits()
        self.set_plot_limits(xmin, xmax, ymin, ymax)
        self.setAxisAutoScale(self.yLeft)  # y-achse
        self.updateAxes()
        self.replot()

    def update_plot_ylimits(self, ymin, ymax):
        xmin, xmax, _, _ = self.get_plot_limits()
        self.set_plot_limits(xmin, xmax, ymin, ymax)
        self.updateAxes()
        self.replot()


class RtPlot(CurvePlotWithModifiedZoomHandling):
    """ modified behavior:
            - space zooms to selected rt range
            - enter puts range marker to middle of currenct rt plot view
            - right crsr + left csrs + shift and alt modifiers move
              boundaries of selection tool
    """
    moveMarker = pyqtSignal(int, QPoint)

    @protect_signal_handler
    def do_space_pressed(self, filter, evt):
        """ zoom to limits of snapping selection tool """

        item = self.get_unique_item(SnappingRangeSelection)
        if item._min != item._max:
            min_neu = min(item._min, item._max)
            max_neu = max(item._min, item._max)
            self.update_plot_xlimits(min_neu, max_neu)

    @protect_signal_handler
    def do_enter_pressed(self, filter, evt):
        """ set snapping selection tool to center of actual x-range """

        xmin, xmax, _, _ = self.get_plot_limits()
        mid = (xmin + xmax) / 2.0

        item = self.get_unique_item(SnappingRangeSelection)
        item.move_point_to(0, (mid, 0), None, emitsignal=False)
        item.move_point_to(1, (mid, 0), None)
        filter.plot.replot()


    @protect_signal_handler
    def do_move_marker(self, evt):
        """ this means: mouse has moved handle this ! """
        self.moveMarker.emit(0, evt.pos())
        self.replot()

    def move_selection_bounds(self, evt, filter_, selector):
        shift_pressed = evt.modifiers() == Qt.ShiftModifier
        alt_pressed = evt.modifiers() == Qt.AltModifier

        item = self.get_unique_item(SnappingRangeSelection)
        neu1 = neu0 = None
        if not alt_pressed:
            neu1 = selector(item.get_neighbour_xvals(item._max))
        if not shift_pressed:
            neu0 = selector(item.get_neighbour_xvals(item._min))

        _min, _max = sorted((item._min, item._max))
        if neu0 is not None and (neu0 <= _max or neu0 == neu1):
            item.move_point_to(0, (neu0, 0), True)
        if neu1 is not None and (neu1 >= _min or neu0 == neu1):
            item.move_point_to(1, (neu1, 0), True)

        filter_.plot.replot()

    @protect_signal_handler
    def do_left_pressed(self, filter_, evt):
        self.move_selection_bounds(evt, filter_, lambda (a, b): a)

    @protect_signal_handler
    def do_right_pressed(self, filter_, evt):
        self.move_selection_bounds(evt, filter_, lambda (a, b): b)

    def label_info(self, x, y):
        # label next to cursor turned off:
        return None

    @protect_signal_handler
    def on_plot(self, x, y):
        """ callback for marker: determine marked point based on cursors coordinates """
        marker = self.get_unique_item(Marker)
        rts = np.array(marker.rts)
        if len(rts) == 0:
            return x, y
        distances = np.abs(x - rts)
        imin = np.argmin(distances)
        self.current_peak = rts[imin], 0
        return self.current_peak


class MzPlot(CurvePlotWithModifiedZoomHandling):

    """ modifications:
            - showing marker at peak next to mouse cursor
            - mouse drag handling for measuring distances between peaks
            - showing information about current peak and distances if in drag mode
    """

    # as we do not have a constructor, we provide default values here:
    data = []
    latest_mzmin = None
    latest_mzmax = None
    image_plot   = None

    all_peaks = np.zeros((0, 2))

    peakActivated = pyqtSignal(float, float)

    startMeasuring = pyqtSignal(float, float)
    moveMeasuring = pyqtSignal(float, float)
    stopMeasuring = pyqtSignal()
    moveMarker = pyqtSignal(int, QPoint)

    def label_info(self, x, y):
        # label next to cursor turned off:
        return None

    @protect_signal_handler
    def on_plot(self, x, y):
        """ callback for marker: determine marked point based on cursors coordinates """
        current_peak = self.next_peak_to(x, y)
        self.peakActivated.emit(current_peak[0], current_peak[1])
        return current_peak

    def set_mz(self, mz):
        raise NotImplemented("refac this with signal/slots")
        mz, I = self.next_peak_to(mz)
        marker = self.get_unique_item(Marker)
        new_x = self.transform(self.xBottom, mz)
        new_y = self.transform(self.yLeft, I)
        marker.setValue(mz, I)  # avoids sending signal
        self.replot()

    def do_finish_zoom_view(self, dx, dy):
        return

    def reset_all_axes_evt(self, filter, evt):
        """ reset axes of plot """
        self.reset_all_axes()

    def reset_all_axes(self):
        self.reset_x_limits()

    def next_peak_to(self, mz, I=None):
        if self.all_peaks.shape[0] == 0:
            return mz, I
        if I is None:
            distances  = (self.all_peaks[:, 0] - mz)**2
            imin = np.argmin(distances)
        else:
            peaks = self.all_peaks - np.array((mz, I))

            # scale according to zooms axis proportions:
            mzmin, mzmax, Imin, Imax = self.get_plot_limits()
            peaks /= np.array((mzmax - mzmin, Imax - Imin))
            # find minimal distacne
            distances = peaks[:, 0] ** 2 + peaks[:, 1] ** 2
            imin = np.argmin(distances)
        return self.all_peaks[imin]


    @protect_signal_handler
    def do_move_marker(self, evt):
        """ this means: mouse has moved handle this ! """
        self.moveMarker.emit(0, evt.pos())
        self.replot()


    @protect_signal_handler
    def do_space_pressed(self, filter, evt):
        """ finds 10 next (distance in mz) peaks tu current marker
            and zooms to them
        """
        return

    @protect_signal_handler
    def do_c_pressed(self, filter, evt):
        ##self.c_call_back(self.current_peak)
        pass

    @protect_signal_handler
    def start_drag_mode(self, filter_, evt):
        """ for measuring """
        mz = self.invTransform(self.xBottom, evt.x())
        I = self.invTransform(self.yLeft, evt.y())
        mz, I = self.next_peak_to(mz, I)
        self.startMeasuring.emit(mz, I)
        #self.replot()

    @protect_signal_handler
    def move_in_drag_mode(self, filter_, evt):
        """ for measuring """
        mz = self.invTransform(self.xBottom, evt.x())
        I = self.invTransform(self.yLeft, evt.y())
        mz, I = self.next_peak_to(mz, I)
        self.moveMeasuring.emit(mz, I)
        self.replot()

    @protect_signal_handler
    def stop_drag_mode(self, filter_, evt):
        """ for measuring """
        self.stopMeasuring.emit()
        self.replot()

    def resample_peaks(self, mzmin, mzmax):
        raise NotImplemented("???")
        if mzmin == self.latest_mzmin and mzmax == self.latest_mzmax:
            return
        self.latest_mzmin = mzmin
        self.latest_mzmax = mzmax
        all_peaks = []
        for i, (pm, rtmin, rtmax, __, __, npeaks) in enumerate(self.data):
            peaks = sample_peaks(pm, rtmin, rtmax, mzmin, mzmax, npeaks)
            curve = self.curves[i]
            curve.set_data(peaks[:, 0], peaks[:, 1])
            all_peaks.append(peaks)
        if len(all_peaks):
            self.all_peaks = np.vstack(all_peaks)
        else:
            self.all_peaks = np.zeros((0, 2))

    def update_plot_xlimits(self, xmin, xmax, rescale_y=True):
        _, _, ymin, ymax = self.get_plot_limits()
        self.set_plot_limits(xmin, xmax, ymin, ymax)
        #self.resample_peaks(xmin, xmax)
        if rescale_y:
            self.setAxisAutoScale(self.yLeft)  # y-achse
        self.updateAxes()
        self.replot()

    def update_plot_ylimits(self, ymin, ymax):
        xmin, xmax, _, _ = self.get_plot_limits()
        #self.resample_peaks(xmin, xmax)
        self.set_plot_limits(xmin, xmax, ymin, ymax)
        self.updateAxes()
        self.replot()


class MeasurementLine(SegmentShape):
    """
        This is plottet as a line
        modifications are:
            - no point int the middle of the line
            - no antialising for the markers
    """


    #####################################################################################
    # the following trick simulates an event updated which is attached to MeasurementLine:
    # (multiple inheritance incl QObject does not work)

    class _Mediator(QObject):
        updated = pyqtSignal()

    @property
    def updated(self):
        return self._mediator.updated

    #####################################################################################

    def __init__(self):
        super(MeasurementLine, self).__init__(0, 0, 0, 0)
        self._mediator = MeasurementLine._Mediator()

        self.start_x = None
        self.start_y = None
        self.setVisible(0)

    def start_measuring(self, x, y):
        self.start_x = x
        self.start_y = y
        self.setVisible(1)
        self.updated.emit()

    def move_measuring(self, x, y):
        if self.start_x is not None and self.start_y is not None:
            self.set_rect(self.start_x, self.start_y, x, y)
        self.setVisible(1)
        self.updated.emit()

    def stop_measuring(self):
        self.setVisible(0)
        self.updated.emit()

    def set_rect(self, x1, y1, x2, y2):
        """
        Set the start point of this segment to (x1, y1)
        and the end point of this line to (x2, y2)
        """
        # the original shape has a extra point in the middle
        # of the line, which is the last tuple, I moved this point to the beginning:

        self.set_points([(x1, y1), (x2, y2), (x1, y1)])

    def _draw(self, painter, xMap, yMap, canvasRect):
        # code copied and rearanged such that line has antialiasing,
        # but symbols have not.
        pen, brush, symbol = self.get_pen_brush(xMap, yMap)

        painter.setPen(pen)
        painter.setBrush(brush)

        points = self.transform_points(xMap, yMap)
        if self.ADDITIONNAL_POINTS:
            shape_points = points[:-self.ADDITIONNAL_POINTS]
            other_points = points[-self.ADDITIONNAL_POINTS:]
        else:
            shape_points = points
            other_points = []

        for i in xrange(points.size()):
            symbol.draw(painter, points[i].toPoint())

        painter.setRenderHint(QPainter.Antialiasing)
        if self.closed:
            painter.drawPolygon(shape_points)
        else:
            painter.drawPolyline(shape_points)

        if self.LINK_ADDITIONNAL_POINTS and other_points:
            pen2 = painter.pen()
            pen2.setStyle(Qt.DotLine)
            painter.setPen(pen2)
            painter.drawPolyline(other_points)


class SnappingRangeSelection(XRangeSelection):

    """ modification:
            - only limit bars can be moved
            - snaps to given rt-values which are in general not equally spaced
    """

    def __init__(self, min_, max_, xvals):
        super(SnappingRangeSelection, self).__init__(min_, max_)

    def move_local_point_to(self, hnd, pos, ctrl=None):
        """ had to rewrite this function as the orginal does not give
            the ctrl parameter value to self.move_point_to method
        """
        val = self.plot().invTransform(self.xAxis(), pos.x())
        self.move_point_to(hnd, (val, 0), ctrl)

    def get_xvals(self):
        xvals = []
        for item in self.plot().get_items():
            if isinstance(item, CurveItem):
                xvals.append(np.array(item.get_data()[0]))
        return np.sort(np.hstack(xvals))

    def move_point_to(self, hnd, pos, ctrl=True, emitsignal=True):
        xvals = self.get_xvals()
        x, y = pos

        # modify pos to the next x-value
        # fast enough
        if len(xvals) > 0:
            val, y = pos
            imin = np.argmin(np.fabs(val - xvals))
            x = xvals[imin]

        if self._min == self._max and not ctrl:
            self._min = x
            self._max = x
        else:
            if hnd == 0:
                self._min = x
            elif hnd == 1:
                self._max = x
            elif hnd == 2:
                move = val - (self._max + self._min) / 2
                self._min += move
                self._max += move

        if emitsignal:
            self.plot().emit(SIG_RANGE_CHANGED, self, self._min, self._max)

    def get_neighbour_xvals(self, x):
        """ used for moving boundaries """

        xvals = self.get_xvals()
        imin = np.argmin(np.fabs(x - xvals))
        if imin == 0:
            return xvals[0], xvals[1]
        if imin == len(xvals) - 1:
            return xvals[imin - 1], xvals[imin]
        return xvals[imin - 1], xvals[imin + 1]

    def move_shape(self, old_pos, new_pos):
        # disabled, that is: do nothing !
        return
