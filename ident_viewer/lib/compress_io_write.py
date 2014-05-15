from collections import defaultdict, Counter

from tables import (IsDescription, StringCol, UInt64Col, Float32Col, Int64Col, Float64Atom,
                    Int16Col, Int8Col, Filters, Float32Atom, Float64Col, BoolCol, UInt8Col,
                    open_file)

import numpy as np

from id_provider import IdProvider


def invert_dict(d):
    return dict((v, k) for (k, v) in d.items())


def invert_non_injective_dict(d):
    inv_dict = defaultdict(list)
    for k, v in d.iteritems():
        inv_dict[v].append(k)
    return inv_dict


CHUNKLEN = 32


class CompressedDataWriter(object):

    class AASequence(IsDescription):

        """ pytables has no variable length string arrays, so we split strings into segments
            of size CHUNKLEN indexed by segment_id
        """

        aa_sequence_id = Int64Col()     # no uint, as pytables can not index uints
        segment_id = Int8Col()     # no uint, as pytables can not index uints
        segment = StringCol(CHUNKLEN)

    class HitsPerAASequenceCounter(IsDescription):

        """ counts number of hits per aa sequenc
        """
        aa_sequence_id = Int64Col()     # no uint, as pytables can not index uints
        hit_count = UInt64Col()

    class BaseName(IsDescription):

        """ pytables has no variable length string arrays, so we split strings into segments
            of size CHUNKLEN indexed by segment_id
        """

        base_name_id = Int16Col()     # no uint, as pytables can not index uints
        segment_id = Int8Col()     # no uint, as pytables can not index uints
        segment = StringCol(CHUNKLEN)

    class Spectrum(IsDescription):

        """ we keep all peaks in two huge arrays for mz and intensities.
            this table references a spectrum with id 'spec_id' to mz[i_low:ihigh, :]
            and intensity[i_low:i_high, :]
        """

        spec_id = Int64Col()       # no uint, as pytables can not index uints
        base_name_id = Int64Col()  # no uint, as pytables can not index uints
        ms_level = UInt8Col()
        rt = Float32Col()
        i_low = UInt64Col()
        i_high = UInt64Col()

    class Feature(IsDescription):

        feature_id = Int64Col()     # no uint, as pytables can not index uints
        base_name_id = Int64Col()   # dito
        feature_id_from_file = UInt64Col()  # size_t in OpenMS
        rtmin = Float32Col()
        rtmax = Float32Col()
        mzmin = Float64Col()
        mzmax = Float64Col()
        area = Float32Col()

    class MassTrace(IsDescription):

        mass_trace_id = Int64Col()     # no uint, as pytables can not index uints
        feature_id = Int64Col()       # dito
        rtmin = Float32Col()
        rtmax = Float32Col()
        mzmin = Float64Col()
        mzmax = Float64Col()
        area = Float32Col()

    class HitFeatureLink(IsDescription):

        hit_id = Int64Col()           # no uint, as pytables can not index uints
        feature_id = Int64Col()       # dito

    class HitData(IsDescription):

        hit_id = Int64Col()     # no uint, as pytables can not index uints
        base_name_id = Int16Col()
        mz = Float64Col()
        rt = Float32Col()
        aa_sequence_id = Int64Col()
        score = Float64Col()
        is_higher_score_better = BoolCol()
        charge = UInt8Col()

    class HitSpectrumLink(IsDescription):

        """
        in most cases we have one spec linked to 0..n hits, but depending on tolerance,
        this might be n:m, that is we find multiple specs for one hit....
        """

        hit_id = Int64Col()     # no uint, as pytables can not index uints
        spec_id = Int64Col()     # no uint, as pytables can not index uints

    def __init__(self, path):
        self.path = path
        self.file_ = open_file(path, mode="w")
        self.root = self.file_.root

        filters = Filters(complib='blosc', complevel=9)

        self.aa_sequence_table = self.file_.create_table(self.root,
                                                         'aa_sequences',
                                                         self.AASequence,
                                                         "AASequences",
                                                         filters=filters)

        self.hit_counts_table = self.file_.create_table(self.root,
                                                        'hit_counts',
                                                        self.HitsPerAASequenceCounter,
                                                        "HitsPerAASequenceCounter",
                                                        filters=filters)

        self.base_name_table = self.file_.create_table(self.root,
                                                       'base_names',
                                                       self.BaseName,
                                                       "BaseNames",
                                                       filters=filters)

        self.spectrum_table = self.file_.create_table(self.root,
                                                      'spectra',
                                                      self.Spectrum,
                                                      "Spectra",
                                                      filters=filters)

        self.feature_table = self.file_.create_table(self.root,
                                                     'features',
                                                     self.Feature,
                                                     "Features",
                                                     filters=filters)

        self.mass_trace_table = self.file_.create_table(self.root,
                                                        'mass_traces',
                                                        self.MassTrace,
                                                        "MassTraces",
                                                        filters=filters)

        self.hit_feature_link_table = self.file_.create_table(self.root,
                                                              'hit_feature_links',
                                                              self.HitFeatureLink,
                                                              "HitFeatureLink",
                                                              filters=filters)

        self.hit_data_table = self.file_.create_table(self.root,
                                                      "hit_data",
                                                      self.HitData,
                                                      "HitData",
                                                      filters=filters)

        self.hit_spectrum_link_table = self.file_.create_table(self.root,
                                                               "hit_spectrum_links",
                                                               self.HitSpectrumLink,
                                                               "HitSpectrumLinks",
                                                               filters=filters)

        self.mz_array = self.file_.create_earray(self.root,
                                                 'mzs',
                                                 Float64Atom(),
                                                 (0,),
                                                 filters=filters,)

        self.intensity_array = self.file_.create_earray(self.root,
                                                        'intensities',
                                                        Float32Atom(),
                                                        (0,),
                                                        filters=filters,)

        self.base_name_id_provider = IdProvider()
        self.aa_sequence_id_provider = IdProvider()
        self.peak_imin = 0
        self.peak_imax = 0
        self.spec_id_provider = IdProvider()
        self.feature_id_provider = IdProvider()
        self.mass_trace_id_provider = IdProvider()

    @staticmethod
    def add_string(table, id_col, id_, string):
        """ pytables has no variable length string arrays, so we split strings into chunks """
        row = table.row
        for i, imin in enumerate(xrange(0, len(string), CHUNKLEN)):
            segment = string[imin:imin + CHUNKLEN]
            row[id_col] = id_
            row['segment_id'] = i
            row['segment'] = segment
            row.append()
        table.flush()

    def add_aa_sequence(self, sequence):
        id_ = self.aa_sequence_id_provider.register(sequence)
        CompressedDataWriter.add_string(self.aa_sequence_table, "aa_sequence_id", id_, sequence)
        return id_

    def finish_writing_aa_sequences(self):
        self.aa_sequence_table.flush()
        self.hit_counts_table.flush()

    def add_base_name(self, name):
        id_ = self.base_name_id_provider.register(name)
        CompressedDataWriter.add_string(self.base_name_table, "base_name_id", id_, name)
        return id_

    def finish_writing_base_names(self):
        self.base_name_table.flush()

    def _add_aa_sequences(self, hits):

        for aa_sequence in set(h.aa_sequence for h in hits):
            self.add_aa_sequence(aa_sequence)

        for aa_sequence, count in Counter((h.aa_sequence for h in hits)).iteritems():
            id_ = self.aa_sequence_id_provider.lookup_id(aa_sequence)
            assert id_ is not None, "may not happen"
            row = self.hit_counts_table.row
            row["aa_sequence_id"] = id_
            row["hit_count"] = count
            row.append()

        self.finish_writing_aa_sequences()

    def _add_base_names(self, base_names):
        for base_name in set(base_names):
            self.add_base_name(base_name)
        self.finish_writing_base_names()

    def _lookup_or_insert_base_name(self, base_name):
        base_name_id = self.base_name_id_provider.lookup_id(base_name)
        if base_name_id is None:
            base_name_id = self.add_base_name(base_name)
        return base_name_id

    def _lookup_or_insert_aa_sequence(self, aa_sequence):
        aa_sequence_id = self.aa_sequence_id_provider.lookup_id(aa_sequence)
        if aa_sequence_id is None:
            aa_sequence_id = self.add_aa_sequence(aa_sequence)
        return aa_sequence_id

    def add_hit(self, hit):
        base_name_id = self._lookup_or_insert_base_name(hit.base_name)
        aa_sequence_id = self._lookup_or_insert_aa_sequence(hit.aa_sequence)
        row = self.hit_data_table.row
        row["hit_id"] = hit.id_
        row["base_name_id"] = base_name_id
        row["rt"] = hit.rt
        row["mz"] = hit.mz
        row["aa_sequence_id"] = aa_sequence_id
        row["score"] = hit.score
        row["charge"] = hit.charge
        row["is_higher_score_better"] = hit.is_higher_score_better
        row.append()

    def write_hits(self, hits):
        # it is important to write aa sequences and basenames before we write the hits
        # as hits link to aa sequences and base names
        self._add_aa_sequences(hits)
        self._add_base_names(set(h.base_name for h in hits))
        for hit in hits:
            self.add_hit(hit)

    def add_spectrum(self, spec, base_name):
        base_name_id = self._lookup_or_insert_base_name(base_name)
        rt, mzs, intensities, precursors, ms_level = spec
        self.mz_array.append(mzs)
        self.intensity_array.append(intensities)
        self.peak_imax += mzs.shape[0]
        # register peaks
        row = self.spectrum_table.row
        row["spec_id"] = self.spec_id_provider.next_id()
        row["base_name_id"] = base_name_id
        row["ms_level"] = ms_level
        row["rt"] = rt
        row["i_low"] = self.peak_imin
        row["i_high"] = self.peak_imax
        id_ = row["spec_id"]  # row.append() below destroys content of row !
        row.append()
        self.peak_imin = self.peak_imax
        return id_

    def link_spec_with_hit(self, spec_id, hit_id):
        row = self.hit_spectrum_link_table.row
        row["spec_id"] = spec_id
        row["hit_id"] = hit_id
        row.append()

    def add_feature(self, feature, base_name):
        hull = feature.getConvexHull()
        rtmin, rtmax, mzmin, mzmax = self._range(hull)
        row = self.feature_table.row
        base_name_id = self.base_name_id_provider.lookup_id(base_name)
        fid = np.uint64(feature.getUniqueId())
        feature_id = self.feature_id_provider.next_id()
        row["feature_id"] = feature_id
        row["feature_id_from_file"] = fid
        row["base_name_id"] = base_name_id
        row["rtmin"] = rtmin
        row["rtmax"] = rtmax
        row["mzmin"] = mzmin
        row["mzmax"] = mzmax
        row["area"] = (rtmax - rtmin) * (mzmax - mzmin)
        row.append()

        for hull in feature.getConvexHulls():
            rtmin, rtmax, mzmin, mzmax = self._range(hull)
            row = self.mass_trace_table.row
            row["mass_trace_id"] = self.mass_trace_id_provider.next_id()
            row["feature_id"] = feature_id
            row["rtmin"] = rtmin
            row["rtmax"] = rtmax
            row["mzmin"] = mzmin
            row["mzmax"] = mzmax
            row["area"] = (rtmax - rtmin) * (mzmax - mzmin)
            row.append()

        return feature_id

    @staticmethod
    def _range(hull):
        hull_points = hull.getHullPoints()
        assert isinstance(hull_points, np.ndarray)
        assert hull_points.shape == (4, 2)   # 4 points, 2 coordinates
        rtmin, mzmin = hull_points.min(axis=0)
        rtmax, mzmax = hull_points.max(axis=0)
        return rtmin, rtmax, mzmin, mzmax

    def link_feature_with_hit(self, feature_id, hit):
        row = self.hit_feature_link_table.row
        row["feature_id"] = feature_id
        row["hit_id"] = hit.id_
        row.append()

    def close(self):
        self.aa_sequence_table.flush()
        self.aa_sequence_table.close()

        self.spectrum_table.flush()
        self.spectrum_table.cols.spec_id.create_index()
        self.spectrum_table.cols.ms_level.create_index()
        self.spectrum_table.cols.rt.create_index()
        self.spectrum_table.flush()
        self.spectrum_table.close()

        self.hit_data_table.flush()
        self.hit_data_table.cols.hit_id.create_index()
        self.hit_data_table.cols.aa_sequence_id.create_index()
        self.hit_data_table.flush()
        self.hit_data_table.close()

        self.hit_spectrum_link_table.flush()
        self.hit_spectrum_link_table.cols.hit_id.create_index()
        self.hit_spectrum_link_table.cols.spec_id.create_index()
        self.hit_spectrum_link_table.flush()
        self.hit_spectrum_link_table.close()

        self.mass_trace_table.flush()
        self.mass_trace_table.cols.mass_trace_id.create_index()
        self.mass_trace_table.cols.feature_id.create_index()
        self.mass_trace_table.cols.rtmin.create_index()
        self.mass_trace_table.cols.rtmax.create_index()
        self.mass_trace_table.cols.mzmin.create_index()
        self.mass_trace_table.cols.mzmax.create_index()
        self.mass_trace_table.flush()
        self.mass_trace_table.close()

        self.feature_table.flush()
        self.feature_table.cols.feature_id.create_index()
        self.feature_table.cols.rtmin.create_index()
        self.feature_table.cols.rtmax.create_index()
        self.feature_table.cols.mzmin.create_index()
        self.feature_table.cols.mzmax.create_index()
        self.feature_table.flush()
        self.feature_table.close()

        self.hit_feature_link_table.flush()
        self.hit_feature_link_table.cols.hit_id.create_index()
        self.hit_feature_link_table.cols.feature_id.create_index()
        self.hit_feature_link_table.flush()
        self.hit_feature_link_table.close()

        self.mz_array.flush()
        self.mz_array.close()

        self.intensity_array.flush()
        self.intensity_array.close()

        self.file_.close()
