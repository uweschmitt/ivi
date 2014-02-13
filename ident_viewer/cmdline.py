

def main():
    import sys
    from PyQt4 import QtGui
    from gui.ivi import IdentViewer
    from lib import load_idxml_file, load_experiment
    assert len(sys.argv) >= 3
    pep_identifications, prot_identifications = load_idxml_file(sys.argv[1])
    peakmaps = map(load_experiment, sys.argv[2:])

    app = QtGui.QApplication(sys.argv)
    window = IdentViewer(pep_identifications, prot_identifications, *peakmaps)
    window.show()
    sys.exit(app.exec_())
