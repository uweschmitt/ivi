import os
import shutil
from ivi.lib import CollectHitsData, CompressedDataReader


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
    assert len(aa_sequences) == 484
    assert len(aa_sequences) == len(set(aa_sequences))

    # as we reduced the peakmap a lot we only have one hit, which is tested below:
    assert "KEVALLNK" in aa_sequences

    assert reader.get_number_of_hits_for("KEVALLNK") == 2

    hits = reader.get_hits_for_aa_sequence("KEVALLNK")
    assert len(hits) == 2

    hit = hits[1]
    assert hit.mz is not None
    assert hit.rt is not None
    assert hit.is_higher_score_better is True
    assert hit.base_name == "reduced"
    spectra = list(reader.fetch_spectra(hit))
    assert len(spectra) == 0

    ch = list(reader.fetch_features_for_hit(hit))
    assert len(ch) == 0

    hit = hits[0]
    assert hit.mz is not None
    assert hit.rt is not None
    assert hit.is_higher_score_better is True
    assert hit.base_name == "reduced"
    spectra = list(reader.fetch_spectra(hit))
    assert len(spectra) == 1

    hits = list(reader.fetch_features_for_hit(hit))
    ch = hits[0].mass_traces
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
    assert spectrum.rt == hit.rt
    assert spectrum.precursors[0].mz == hit.mz
    assert len(spectrum.mzs) == 497
    # check if not alls peaks are zero:
    assert spectrum.mzs.sum() > 0
    assert spectrum.intensities.sum() > 0

    import time
    s = time.time()
    rts, intensities = reader.fetch_chromatogram(0, 1000, 0, 1000, hit.base_name)
    print len(rts), len(intensities)
    print rts[:3], intensities[:3]
    print time.time() - s
    s = time.time()
    rts, intensities = reader.fetch_chromatogram(0, 1000, 0, 1000, hit.base_name)
    print len(rts), len(intensities)
    print rts[:3], intensities[:3]
    print time.time() - s

    pm = reader.fetch_peak_map(hit.base_name)
    assert len(pm.spectra) == 248
    assert all(s.ms_level == 1 for s in pm.spectra)
    assert len(pm.spectra[0].mzs) == 5881
    assert len(pm.spectra[0].intensities) == 5881
    assert len(pm.spectra[0].precursors) == 0
    assert abs(pm.spectra[0].rt - 0.5800) < 1e-4

    hulls = list(reader.fetch_feature_ranges_for_base_name("reduced"))
    assert len(hulls) == 40

    hits = list(reader.get_hits_for_base_name("reduced"))
    assert len(hits) == 910


    hits.sort(key=lambda k:hit.id_)
    count = 0
    for h in hits:
        f = reader.fetch_features_for_hit(h)
        for fi in f:
            count += 1

    assert count == 40
    assert fi.id_ == 39
    assert fi.fid == 8921995772518139576L

    ranges = list(reader.fetch_mass_traces_in_range("reduced", 0, 1000, 0, 5000))
    assert len(ranges) == 160

    ranges = list(reader.fetch_mass_traces_in_range("reduced", 100, 300, 200, 500))
    assert len(ranges) == 2

    ranges = list(reader.fetch_mass_traces_intersecting("reduced", 100, 300, 200, 500))
    assert len(ranges) == 5

    ranges = list(reader.fetch_mass_traces_intersecting("reduced", 100, 300, 458, 460))
    assert len(ranges) == 2

    features = list(reader.fetch_features_in_range("reduced", 100, 300,  200, 500))
    assert len(features) == 1
    feature = features[0]
    assert len(feature.mass_traces) == 2

    features = list(reader.fetch_features_intersecting("reduced", 100, 300,  200, 500))
    assert len(features) == 2
    feature = features[0]
    assert len(feature.mass_traces) == 3
    feature = features[1]
    assert len(feature.mass_traces) == 2


