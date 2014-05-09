from PyQt4.QtGui import QFrame, QGridLayout, QSizePolicy

from plotting_widgets import MzPlotWidget

from guiqwt.annotations import AnnotatedPoint

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

class SpectrumPlotter(MzPlotWidget):

    def __init__(self, *a, **kw):
        super(SpectrumPlotter, self).__init__(*a, **kw)
        self.last_hit_id = None


    def plot_hit(self, spectrum, assignment):
        for mz, ii, ion_name, info in assignment:
            color = dict(y="red", b="green").get(ion_name[0], "black")
            self.add_foreground_item(Annotation(mz, ii, "%s<br>%s" % (ion_name, info or ""), color))
        self.plot_spectrum((spectrum.mzs, spectrum.intensities))
