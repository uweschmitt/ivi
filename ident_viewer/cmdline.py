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

def prepare():

    from std_logger import logger

    try:
        _prepare()
    except:
        logger.error("execution failed", exc_info=True)

def _prepare():

    from std_logger import logger
    from helpers import measure_time

    import os
    import argparse
    import time

    parser = argparse.ArgumentParser(description='Prepare experiment data for ivi tool')
    parser.add_argument('--out', action="store", help='path of output file', type=str,)
    parser.add_argument('--tolerance.mz', dest="mztol", action='store', default=20.0, type=float,
                        help="tolerance in ppm for matching peptide hits and MS2 spectra")
    parser.add_argument('--tolerance.rt', dest="rttol", action='store', default=5.0, type=float,
                        help="tolerance in seconds for matching peptide hits and MS2 spectra")
    parser.add_argument('experiment_root_path')

    args = parser.parse_args()
    root = args.experiment_root_path
    out_file = args.out
    if out_file is None:
        out_file = os.path.join(root, "collected.ivi")
    if not out_file.endswith(".ivi"):
        raise Exception("please provide file extension .ivi for OUT argument")
    mz_tolerance = args.mztol
    rt_tolerance = args.rttol

    logger.info("got argument mz_tolerance=%.2f ppm" % mz_tolerance)
    logger.info("got argument rt_tolerance=%.2f seconds" % rt_tolerance)
    logger.info("got argument experiment_root_path=%s" % root)
    logger.info("got argument out_file=%s" % out_file)

    dirname = os.path.dirname(os.path.abspath(out_file))
    if not os.path.exists(dirname):
        logger.info("create directory %s" % dirname)
        os.makedirs(dirname)

    from lib import CollectHitsData

    collector = CollectHitsData(root)
    collector.collect(out_file, mz_tolerance, rt_tolerance)
