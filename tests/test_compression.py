
import os
import shutil
from ident_viewer.lib import CollectHitsData, CompressedDataReader


def test_0(data_path, tmpdir):

    # setup experiment data folder
    pm_dir = tmpdir.join("peakmap00")
    ident_dir = tmpdir.join("idents")
    pm_dir.mkdir()
    ident_dir.mkdir()

    shutil.copy(data_path("reduced.mzML"), pm_dir.strpath)
    shutil.copy(data_path("reduced.pep.xml"), ident_dir.strpath)

    # compress data
    collector = CollectHitsData(tmpdir.strpath)
    collector.collect(tmpdir.join("out.ivi").strpath)

    # read compressed data and check it !
    reader = CompressedDataReader(tmpdir.join("out.ivi").strpath)

    aa_sequences = reader.get_aa_sequences()
    assert len(aa_sequences) == 49

    # as we reduced the peakmap a lot we only have one hit, which is tested below:
    assert "VVAPGNANDAK" in aa_sequences

    assert reader.get_number_of_hits_for("VVAPGNANDAK") == 1

    hits = reader.get_hits_for_aa_sequence("VVAPGNANDAK")
    assert len(hits) == 1
    hit = hits[0]
    assert hit.mz is not None
    assert hit.rt is not None
    assert hit.is_higher_score_better is True
    assert hit.spec_id == 0

    spec = reader.fetch_spectrum(hit)
    assert spec.getRT() == hit.rt
    assert spec.getPrecursors()[0].getMZ() == hit.mz
    assert spec.size() == 425
    # check if not alls peaks are zero:
    assert spec.get_peaks().sum() > 0
