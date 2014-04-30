from collections import defaultdict, Counter

from tables import (IsDescription, StringCol, UInt64Col, Float32Col, Int64Col, Float64Atom,
                    Int16Col, Int8Col, open_file, Filters, Float32Atom, Float64Col, BoolCol,
                    UInt8Col, Float16Col)

import numpy as np

from data_structures import Hit, Spectrum, Precursor, PeakRange, PeakMap, Chromatogram, Feature


def invert_dict(d):
    return dict((v, k) for (k, v) in d.items())


def invert_non_injective_dict(d):
    inv_dict = defaultdict(list)
    for k, v in d.iteritems():
        inv_dict[v].append(k)
    return inv_dict


class IdProvider(object):

    def __init__(self, start_with_id=0):
        self.current_id = start_with_id
        self.id_to_item = dict()
        self.item_to_id = dict()

    def next_id(self):
        next_id = self.current_id
        self.current_id += 1
        return next_id

    def is_registered(self, item):
        return item in self.item_to_id

    def register(self, item):
        if self.is_registered(item):
            raise Exception("item %r is already registered" % item)
        assigned_id = self.current_id
        self.set_(assigned_id, item)
        self.current_id += 1
        return assigned_id

    def set_(self, id_, item):
        self.id_to_item[id_] = item
        self.item_to_id[item] = id_

    def unregister(self, item):
        if not self.is_registered(item):
            raise Exception("can not remove item %r as it is not registered yet" % item)
        id_ = self.lookup_id(item)
        del self.id_to_item[id_]
        del self.item_to_id[item]
        return id_

    def lookup_id(self, item):
        return self.item_to_id.get(item)

    def lookup_item(self, id_):
        return self.id_to_item.get(id_)

    def get_items_iter(self):
        return self.item_to_id.iterkeys()


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
        rt = Float16Col()
        i_low = UInt64Col()
        i_high = UInt64Col()

    class Feature(IsDescription):

        feature_id = Int64Col()     # no uint, as pytables can not index uints
        base_name_id = Int64Col()   # dito
        feature_id_from_file = UInt64Col()  # size_t in OpenMS
        rt_min = Float32Col()
        rt_max = Float32Col()
        mz_min = Float64Col()
        mz_max = Float64Col()
        area   = Float32Col()

    class MassTrace(IsDescription):

        mass_trace_id = Int64Col()     # no uint, as pytables can not index uints
        feature_id = Int64Col()       # dito
        rt_min = Float32Col()
        rt_max = Float32Col()
        mz_min = Float64Col()
        mz_max = Float64Col()
        area   = Float32Col()

    class HitFeatureLink(IsDescription):

        hit_id = Int64Col()           # no uint, as pytables can not index uints
        feature_id = Int64Col()   # dito

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
        rt_min, rt_max, mz_min, mz_max = self._range(hull)
        row = self.feature_table.row
        base_name_id = self.base_name_id_provider.lookup_id(base_name)
        feature_id_from_file = np.uint64(feature.getUniqueId())
        feature_id = self.feature_id_provider.next_id()
        row["feature_id"] = feature_id
        row["feature_id_from_file"] = feature_id_from_file
        row["base_name_id"] = base_name_id
        row["rt_min"] = rt_min
        row["rt_max"] = rt_max
        row["mz_min"] = mz_min
        row["mz_max"] = mz_max
        row["area"] = (rt_max - rt_min) * (mz_max - mz_min)
        row.append()

        for hull in feature.getConvexHulls():
            rt_min, rt_max, mz_min, mz_max = self._range(hull)
            row = self.mass_trace_table.row
            row["mass_trace_id"] = self.mass_trace_id_provider.next_id()
            row["feature_id"] = feature_id
            row["rt_min"] = rt_min
            row["rt_max"] = rt_max
            row["mz_min"] = mz_min
            row["mz_max"] = mz_max
            row["area"] = (rt_max - rt_min) * (mz_max - mz_min)
            row.append()

        return feature_id

    @staticmethod
    def _range(hull):
        hull_points = hull.getHullPoints()
        assert isinstance(hull_points, np.ndarray)
        assert hull_points.shape == (4, 2)   # 4 points, 2 coordinates
        rt_min, mz_min = hull_points.min(axis=0)
        rt_max, mz_max = hull_points.max(axis=0)
        return rt_min, rt_max, mz_min, mz_max

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
        self.hit_data_table.close()

        self.hit_spectrum_link_table.flush()
        self.hit_spectrum_link_table.cols.hit_id.create_index()
        self.hit_spectrum_link_table.cols.spec_id.create_index()
        self.hit_spectrum_link_table.flush()
        self.hit_spectrum_link_table.close()

        self.mass_trace_table.flush()
        self.mass_trace_table.cols.mass_trace_id.create_index()
        self.mass_trace_table.cols.feature_id.create_index()
        self.mass_trace_table.cols.rt_min.create_index()
        self.mass_trace_table.cols.rt_max.create_index()
        self.mass_trace_table.cols.mz_min.create_index()
        self.mass_trace_table.cols.mz_max.create_index()
        self.mass_trace_table.flush()
        self.mass_trace_table.close()

        self.feature_table.flush()
        self.feature_table.cols.feature_id.create_index()
        self.feature_table.cols.rt_min.create_index()
        self.feature_table.cols.rt_max.create_index()
        self.feature_table.cols.mz_min.create_index()
        self.feature_table.cols.mz_max.create_index()
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


class CompressedDataReader(object):

    def __init__(self, path):
        self.file_ = open_file(path, mode="r")

        # shortcuts
        self.spectrum_table = self.file_.root.spectra
        self.mz_array = self.file_.root.mzs
        self.intensity_array = self.file_.root.intensities
        self.base_name_table = self.file_.root.base_names
        self.aa_sequence_table = self.file_.root.aa_sequences
        self.feature_table = self.file_.root.features
        self.mass_trace_table = self.file_.root.mass_traces
        self.hit_data_table = self.file_.root.hit_data
        self.hit_counts_table = self.file_.root.hit_counts
        self.hit_spectrum_link_table = self.file_.root.hit_spectrum_links
        self.hit_feature_link_table = self.file_.root.hit_feature_links

        self._read_base_names()
        self._read_aa_sequences()

    @staticmethod
    def fetch_strings(table, id_col):
        collected_segments = defaultdict(list)
        for row in table.iterrows():
            id_ = row[id_col]
            segment_id = row["segment_id"]
            segment = row["segment"]
            collected_segments[id_].append((segment_id, segment))

        id_provider = IdProvider()
        for id_, segments in collected_segments.iteritems():
            segments.sort()  # sorts by segment_id
            full_str = "".join(s for (segment_id, s) in segments)
            id_provider.set_(id_, full_str)
        return id_provider

    def _read_base_names(self):
        self.base_name_id_provider = CompressedDataReader.fetch_strings(self.base_name_table,
                                                                        "base_name_id")

    def _read_aa_sequences(self):
        self.aa_sequence_id_provider = CompressedDataReader.fetch_strings(self.aa_sequence_table,
                                                                          "aa_sequence_id")
        self.no_hits_per_aa_sequence = dict()
        for row in self.hit_counts_table:
            id_ = row["aa_sequence_id"]
            counts = row["hit_count"]
            self.no_hits_per_aa_sequence[id_] = counts

    def get_base_names(self):
        return list(self.base_name_id_provider.get_items_iter())

    def get_aa_sequences(self):
        return list(self.aa_sequence_id_provider.get_items_iter())

    def get_number_of_hits_for(self, aa_sequence):
        id_ = self.aa_sequence_id_provider.lookup_id(aa_sequence)
        return self.no_hits_per_aa_sequence.get(id_, 0)

    def get_hits_for_aa_sequence(self, aa_sequence):
        hits = []
        aa_sequence_id = self.aa_sequence_id_provider.lookup_id(aa_sequence)
        rows = self.hit_data_table.where("aa_sequence_id == %d" % aa_sequence_id)
        for row in rows:
            base_name = self.base_name_id_provider.lookup_item(row["base_name_id"])
            hit = Hit(row["hit_id"], aa_sequence, base_name, row["mz"], row["rt"], row["charge"],
                      row["score"], row["is_higher_score_better"])
            hits.append(hit)
        return hits

    def get_hits_for_base_name(self, base_name):
        hits = []
        base_name_id = self.base_name_id_provider.lookup_id(base_name)
        rows = self.hit_data_table.where("base_name_id == %d" % base_name_id)
        for row in rows:
            aa_sequence = self.aa_sequence_id_provider.lookup_item(row["aa_sequence_id"])
            hit = Hit(row["hit_id"], aa_sequence, base_name, row["mz"], row["rt"], row["charge"],
                      row["score"], row["is_higher_score_better"])
            hits.append(hit)
        return hits

    def count_spectra_for(self, hit):
        rows = self.hit_spectrum_link_table.where("hit_id == %d" % hit.id_)
        return len(list(rows))

    def fetch_spectra(self, hit):
        rows0 = self.hit_spectrum_link_table.where("hit_id == %d" % hit.id_)
        # no look up with  base name needed, as hit has unique base name which is
        # implicitly contained when lookup up in hit_spectrum_link_table.
        for row0 in rows0:
            spec_id = row0["spec_id"]
            rows1 = self.spectrum_table.where("spec_id == %d" % spec_id)
            for row1 in rows1:
                i_low = row1["i_low"]
                i_high = row1["i_high"]
                mzs = self.mz_array[i_low:i_high]
                intensities = self.intensity_array[i_low:i_high]
                precursor = Precursor(hit.mz)
                spec = Spectrum(hit.rt, mzs, intensities, [precursor], 2)
                yield spec

    def fetch_mass_traces_for_hit(self, hit):
        rows0 = self.hit_feature_link_table.where("hit_id == %d" % hit.id_)
        for row0 in rows0:
            feature_id = row0["feature_id"]
            rows = self.mass_trace_table.where("feature_id == %d" % feature_id)
            for row in rows:
                rt_min = row["rt_min"]
                rt_max = row["rt_max"]
                mz_min = row["mz_min"]
                mz_max = row["mz_max"]
                yield PeakRange(rt_min, rt_max, mz_min, mz_max)

    def fetch_features_in_range(self, base_name, rt_min, rt_max, mz_min, mz_max):
        condition = """(%f <= rt_min) & (rt_max <= %f)\
                       & (%f <= mz_min) & (mz_max <= %f)""" % (rt_min, rt_max, mz_min, mz_max)
        return self._fetch_features(base_name, condition)

    def fetch_features_intersecting(self, base_name, rt_0, rt_1, mz_0, mz_1):
        condition = self._intersecting_condition(rt_0, rt_1, mz_0, mz_1)
        return self._fetch_features(base_name, condition)

    def _intersecting_condition(self, rt_0, rt_1, mz_0, mz_1):
        """
           (rt_min, mz_min) is in rect (rt_0, mz_0, rt_1, mz_1)
        or
           (rt_max, mz_max) is in rect (rt_0, mz_0, rt_1, mz_1)

        that is:

           rt_0 <= rt_min <= rt_1 and mz_0 <= mz_min <= mz_1
        or
           rt_0 <= rt_max <= rt_1 and mz_0 <= mz_max <= mz_1
        """
        cond_min = """({rt_0} <= rt_min) & (rt_min <= {rt_1}) \
                     &({mz_0} <= mz_min) & (mz_min <= {mz_1}) """.format(**locals())
        cond_max = """({rt_0} <= rt_max) & (rt_max <= {rt_1}) \
                     &({mz_0} <= mz_max) & (mz_max <= {mz_1}) """.format(**locals())

        condition = "({cond_min}) | ({cond_max})".format(**locals())
        return condition

    def _fetch_features(self, base_name, condition):
        base_name_id = self.base_name_id_provider.lookup_id(base_name)
        full_condition = "(base_name_id == %d) & (%s)" % (base_name_id, condition)
        rows = self.feature_table.where(full_condition)
        for row in rows:
            rt_min = row["rt_min"]
            rt_max = row["rt_max"]
            mz_min = row["mz_min"]
            mz_max = row["mz_max"]
            feature_id = row["feature_id"]
            feature_id_from_file = row["feature_id_from_file"]
            mass_traces = list(self._fetch_mass_traces_for_feature(feature_id))
            yield Feature(feature_id, base_name, feature_id_from_file,
                          rt_min, rt_max, mz_min, mz_max, mass_traces)

    def _fetch_mass_traces_for_feature(self, feature_id):
        rows = self.mass_trace_table.where("feature_id == %d" % feature_id)
        for row in rows:
            rt_min = row["rt_min"]
            rt_max = row["rt_max"]
            mz_min = row["mz_min"]
            mz_max = row["mz_max"]
            yield PeakRange(rt_min, rt_max, mz_min, mz_max)

    def fetch_mass_traces_in_range(self, base_name, rt_min, rt_max, mz_min, mz_max):
        base_name_id = self.base_name_id_provider.lookup_id(base_name)
        rows = self.mass_trace_table.where("""(base_name_id == %d) \
                                               & (%f <= rt_min) & (rt_max <= %f) \
                                               & (%f <= mz_min) & (mz_max <= %f) \
                                           """ % (base_name_id, rt_min, rt_max, mz_min, mz_max)
                                           )
        for row in rows:
            rt_min = row["rt_min"]
            rt_max = row["rt_max"]
            mz_min = row["mz_min"]
            mz_max = row["mz_max"]
            yield PeakRange(rt_min, rt_max, mz_min, mz_max)

    def fetch_mass_traces_intersecting(self, base_name, rt_0, rt_1, mz_0, mz_1):
        """
           (rt_min, mz_min) is in rect (rt_0, mz_0, rt_1, mz_1)
        or
           (rt_max, mz_max) is in rect (rt_0, mz_0, rt_1, mz_1)

        that is:

           rt_0 <= rt_min <= rt_1 and mz_0 <= mz_min <= mz_1
        or
           rt_0 <= rt_max <= rt_1 and mz_0 <= mz_max <= mz_1
        """
        base_name_id = self.base_name_id_provider.lookup_id(base_name)
        cond_base_name = "base_name_id == {base_name_id}".format(base_name_id=base_name_id)
        is_condition = self._intersecting_condition(rt_0, rt_1, mz_0, mz_1)
        condition = "({cond_base_name}) & ({is_condition}) ".format(**locals())
        rows = self.mass_trace_table.where(condition)
        for row in rows:
            rt_min = row["rt_min"]
            rt_max = row["rt_max"]
            mz_min = row["mz_min"]
            mz_max = row["mz_max"]
            yield PeakRange(rt_min, rt_max, mz_min, mz_max)

    def fetch_feature_ranges_for_base_name(self, base_name):
        base_name_id = self.base_name_id_provider.lookup_id(base_name)
        rows = self.feature_table.where("base_name_id == %d" % base_name_id)
        for row in rows:
            rt_min = row["rt_min"]
            rt_max = row["rt_max"]
            mz_min = row["mz_min"]
            mz_max = row["mz_max"]
            yield PeakRange(rt_min, rt_max, mz_min, mz_max)

# todo: test coverage !
#       profiling
#       concept profiler  -> filtering of hits (aa_sequence, oder feature_id !)
#       feature_id im hit-baum mit anzeigen !

    def fetch_chromatogram(self, rt_min, rt_max, mz_min, mz_max, base_name):
        base_name_id = self.base_name_id_provider.lookup_id(base_name)
        rows = self.spectrum_table.where(
            """(base_name_id == %d) & (%f <= rt) & (rt <= %f) & (ms_level == 1)""" % (base_name_id, rt_min, rt_max))
        rts = []
        ion_counts = []
        for row in rows:
            rts.append(row["rt"])
            i_low = row["i_low"]
            i_high = row["i_high"]
            mzs = self.mz_array[i_low:i_high]
            intensities = self.intensity_array[i_low:i_high]
            view = (mz_min <= mzs) * (mzs <= mz_max)
            # dtype conversion from float16 -> float128 in order to avoid overflow when
            # summing up many values:
            ion_count = intensities[view].astype(np.float128).sum()
            ion_counts.append(ion_count)
        return Chromatogram(rts, ion_counts)

    def fetch_peak_map(self, base_name):
        base_name_id = self.base_name_id_provider.lookup_id(base_name)
        rows = self.spectrum_table.where(
            """(base_name_id == %d) & (ms_level == 1)""" % (base_name_id, ))
        spectra = []
        for row in rows:
            rt = row["rt"]
            i_low = row["i_low"]
            i_high = row["i_high"]
            mzs = self.mz_array[i_low:i_high]
            intensities = self.intensity_array[i_low:i_high]
            spectrum = Spectrum(rt, mzs, intensities, [], 1)
            spectra.append(spectrum)
        return PeakMap(spectra)


if __name__ == "__main__":
    r = CompressedDataReader("/data/dose_minimized/collected.ivi")
    aaseq = "YYVPDTFLLQR"
    print r.get_number_of_hits_for(aaseq)
    print r.get_hits_for_aa_sequence(aaseq)
