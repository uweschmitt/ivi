import pdb

import os
import shutil
from ident_viewer.lib import CollectHitsData, CompressedDataReader


def test_0(data_path, tmpdir):

    # setup experiment data folder
    pm_dir = tmpdir.join("peakmap00")
    ident_dir = tmpdir.join("idents")
    pm_dir.mkdir()
    ident_dir.mkdir()

    shutil.copy(data_path("reduced.mzXML"), pm_dir.strpath)
    shutil.copy(data_path("reduced.pep.xml"), ident_dir.strpath)
    shutil.copy(data_path("reduced.featureXML"), ident_dir.strpath)

    # compress data
    collector = CollectHitsData(tmpdir.strpath)
    collector.collect(tmpdir.join("out.ivi").strpath, tmpdir.join("unmatched.txt").strpath)

    # read compressed data and check it !
    reader = CompressedDataReader(tmpdir.join("out.ivi").strpath)

    aa_sequences = reader.get_aa_sequences()
    assert len(aa_sequences) == 475

    #for aa in aa_sequences:
        #hits = reader.get_hits_for_aa_sequence(aa)
        #print aa
        #for h in hits:
            #print "  ", len(list(reader.fetch_spectra(h))), len(list(reader.fetch_convex_hulls(h)))

    # as we reduced the peakmap a lot we only have one hit, which is tested below:
    assert "KEVALLNK" in aa_sequences

    assert reader.get_number_of_hits_for("KEVALLNK") == 2

    hits = reader.get_hits_for_aa_sequence("KEVALLNK")
    assert len(hits) == 2

    hit = hits[1]
    assert hit.mz is not None
    assert hit.rt is not None
    assert hit.is_higher_score_better is True
    spectra = list(reader.fetch_spectra(hit))
    assert len(spectra) == 0

    ch = list(reader.fetch_convex_hulls(hit))
    assert len(ch) == 0

    hit = hits[0]
    assert hit.mz is not None
    assert hit.rt is not None
    assert hit.is_higher_score_better is True
    spectra = list(reader.fetch_spectra(hit))
    assert len(spectra) == 1


    ch = list(reader.fetch_convex_hulls(hit))
    assert len(ch) == 3
    tobe = [(360.3659973144531, 372.4840087890625, 457.7884216308594, 457.7892761230469),
            (360.3659973144531, 372.4840087890625, 458.2905578613281, 458.29132080078125),
            (360.3659973144531, 370.1440124511719, 458.7908935546875, 458.79254150390625)]
    for i in range(3):
        t0 = tobe[i]
        c0 = ch[i]
        for tii, cii in zip(t0, c0):
            assert abs(tii - cii) < 1e-5


    spectrum = spectra[0]
    assert spectrum.getRT() == hit.rt
    assert spectrum.getPrecursors()[0].getMZ() == hit.mz
    assert spectrum.size() == 497
    # check if not alls peaks are zero:
    assert spectrum.get_peaks()[0].sum() > 0
    assert spectrum.get_peaks()[1].sum() > 0

    import time
    s = time.time()
    rts, intensities = reader.fetch_chromatogram(0, 1000, 0, 1000)
    print len(rts), len(intensities)
    print rts[:3], intensities[:3]
    print time.time() - s
