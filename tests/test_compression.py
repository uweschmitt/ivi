import pdb

import os
import shutil
from ident_viewer.lib import CollectHitsData


def test_0(data_path, tmpdir):

    pm_dir = tmpdir.join("peakmap00")
    ident_dir = tmpdir.join("idents")
    pm_dir.mkdir()
    ident_dir.mkdir()

    shutil.copy(data_path("reduced.mzML"), pm_dir.strpath)
    shutil.copy(data_path("reduced.pep.xml"), ident_dir.strpath)

    collector = CollectHitsData(tmpdir.strpath)
    collector.collect("out.ivi")

    # todo:
    # read result and checki it!
