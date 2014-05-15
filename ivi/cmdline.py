def main():

    import sys
    from PyQt4 import QtGui
    from PyQt4.QtCore import Qt
    from gui.ivi import IdentViewer

    from lib import CompressedDataReader
    import argparse

    parser = argparse.ArgumentParser(description='navigate and viualize data from ivi file')
    parser.add_argument('ivi_file_path')
    args = parser.parse_args()
    reader = CompressedDataReader(args.ivi_file_path)

    app = QtGui.QApplication(sys.argv)
    window = IdentViewer(reader)
    window.show()
    window.raise_()
    window.setWindowState(Qt.WindowActive)
    sys.exit(app.exec_())


def prepare():

    from std_logger import logger

    try:
        _prepare()
    except SystemExit:
        pass
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
    parser.add_argument('--unmatched', action="store", help='path of file for writing unmatched'
                        ' hits', type=str,)
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

    unmatched_hits_file = args.unmatched
    if unmatched_hits_file is not None:
        if not unmatched_hits_file.endswith(".txt"):
            raise Exception("please provide file extension .txt for UNMATCHED argument")

    mz_tolerance = args.mztol
    rt_tolerance = args.rttol

    logger.info("got argument mz_tolerance=%.2f ppm" % mz_tolerance)
    logger.info("got argument rt_tolerance=%.2f seconds" % rt_tolerance)
    logger.info("got argument experiment_root_path=%s" % root)
    logger.info("got argument out=%s" % out_file)
    logger.info("got argument unmatched=%s" % (unmatched_hits_file or "(None)"))

    def _create_dir_for(path):
        dirname = os.path.dirname(os.path.abspath(path))
        if not os.path.exists(dirname):
            logger.info("create directory %s" % dirname)
            os.makedirs(dirname)

    _create_dir_for(out_file)
    if unmatched_hits_file is not None:
        _create_dir_for(unmatched_hits_file)

    from lib import CollectHitsData
    from lib.compress_io import CompressedDataReader
    smiles = r"""
       _____         _____         _____         _____
     .'     '.     .'     '.     .'     '.     .'     '.
    /  o   o  \   /  o   o  \   /  o   o  \   /  o   o  \
   |           | |           | |           | |           |
   |  \     /  | |  \     /  | |  \     /  | |  \     /  |
    \  '---'  /   \  '---'  /   \  '---'  /   \  '---'  /
 jgs '._____.'     '._____.'     '._____.'     '._____.' """.split("\n")


    collector = CollectHitsData(root)
    collector.collect(out_file, unmatched_hits_file, mz_tolerance, rt_tolerance)
    logger.info("")
    logger.info("")
    for line in smiles:
        logger.info("    %s" % line)
    logger.info("")
    logger.info("")
    logger.info("=" * 80)
    logger.info("you can inspect your data now running")
    logger.info("")
    logger.info("ivi %s" % out_file)
    logger.info("")
    logger.info("from your commandline")
    logger.info("=" * 80)
    logger.info("")

    # with measure_time("reading and computing full chromatogram"):
    #   #reader = CompressedDataReader(out_file)
    #   #rts, chromo = reader.fetch_chromatogram(0, 1e30, 0, 1e30)
    #   #logger.info("chromatogram has length %d and max ion count %.1f" % (len(rts), max(chromo)))
