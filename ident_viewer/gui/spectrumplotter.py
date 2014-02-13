from PyQt4.QtGui import QPushButton, QFrame

class SpectrumPlotter(QFrame):

    def __init__(self, parent):
        super(SpectrumPlotter, self).__init__(parent)

    def update(self, *a):
        print a


