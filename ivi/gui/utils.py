import types

from PyQt4.Qwt5 import QwtScaleDraw, QwtText


def set_x_axis_scale_draw(widget):
    """ formats ticks on time axis as minutes """
    drawer = QwtScaleDraw()
    drawer.setMinimumExtent(20)
    formatSeconds = lambda v: "%.2fm" % (v / 60.0)
    format_label = lambda self, v: QwtText(formatSeconds(v))
    drawer.label = types.MethodType(format_label, widget.plot, QwtScaleDraw)
    widget.plot.setAxisScaleDraw(widget.plot.xBottom, drawer)


def set_y_axis_scale_draw(widget):
    """ sets minimum extent for horizontal aligning plots """
    drawer = QwtScaleDraw()
    drawer.setMinimumExtent(40)
    widget.plot.setAxisScaleDraw(widget.plot.yLeft, drawer)
