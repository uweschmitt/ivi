import pdb
from collections import defaultdict, namedtuple, Counter
import pyopenms as oms

from tables import (IsDescription, StringCol, UInt64Col, Float32Col, Int64Col, Float64Atom,
                    Int16Col, Int8Col, open_file, Filters, Float16Atom, Float32Atom, Float64Col,
                    BoolCol, UInt8Col, Float16Col)

import numpy as np


def invert_dict(d):
    return dict((v, k) for (k, v) in d.items())

def invert_non_injective_dict(d):
    inv_dict = defaultdict(list)
    for k, v in d.iteritems():
        inv_dict[v].append(k)
    return inv_dict


Hit = namedtuple("Hit", "id_, aa_sequence, base_name, mz, rt, score, is_higher_score_better")


CHUNKLEN = 32


class CompressedDataWriter(object):

    class AASequence(IsDescription):

        """ pytables has no variable length string arrays, so we split strings into segments
            of size CHUNKLEN indexed by segment_id
        """

        aa_seq_id = Int64Col()     # no uint, as pytables can not index uints
        segment_id = Int8Col()     # no uint, as pytables can not index uints
        segment = StringCol(CHUNKLEN)

    class HitsPerAASequenceCounter(IsDescription):

        """ counts number of hits per aa sequenc
        """
        aa_seq_id = Int64Col()     # no uint, as pytables can not index uints
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

        spec_id = Int64Col()     # no uint, as pytables can not index uints
        ms_level = UInt8Col()
        rt = Float16Col()
        i_low = UInt64Col()
        i_high = UInt64Col()

    class ConvexHull(IsDescription):

        convex_hull_id = Int64Col()     # no uint, as pytables can not index uints
        rt_min = Float32Col()
        rt_max = Float32Col()
        mz_min = Float32Col()
        mz_max = Float32Col()

    class HitConvexHullLink(IsDescription):

        hit_id = Int64Col()     # no uint, as pytables can not index uints
        convex_hull_id = Int64Col()

    class HitData(IsDescription):

        hit_id = Int64Col()     # no uint, as pytables can not index uints
        base_name_id = Int16Col()
        mz = Float64Col()
        rt = Float32Col()
        aa_seq_id = Int64Col()
        score = Float64Col()
        is_higher_score_better = BoolCol()

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

        """ pytables has no variable length string arrays, so we split strings into chunks """
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

        self.convex_hull_table = self.file_.create_table(self.root,
                                                      'convex_hulls',
                                                      self.ConvexHull,
                                                      "ConvexHulls",
                                                      filters=filters)

        self.hit_convex_hull_link_table = self.file_.create_table(self.root,
                                                                'hit_convex_hulls_links',
                                                                self.HitConvexHullLink,
                                                                "HitConvexHullLink",
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
                                                    Float64Atom(),
                                                    (0,),
                                                    filters=filters,)

        self.base_name_to_id = dict()
        self.aa_sequence_to_id = dict()
        self.peak_imin = 0
        self.peak_imax = 0
        self.spec_id = 0
        self.convex_hull_id = 0

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

    def add_aa_sequence(self, id_, sequence):
        CompressedDataWriter.add_string(self.aa_sequence_table, "aa_seq_id", id_, sequence)
        #self.aa_sequence_to_id[sequence] = id_

    def finish_writing_aa_sequences(self):
        self.aa_sequence_table.flush()
        self.hit_counts_table.flush()

    def add_base_name(self, id_, name):
        CompressedDataWriter.add_string(self.base_name_table, "base_name_id", id_, name)
        self.base_name_to_id[name] = id_

    def finish_writing_base_names(self):
        self.base_name_table.flush()

    def _add_aa_sequences(self, hits):
        aa_sequences = dict(enumerate(set(h.aa_sequence for h in hits)))
        for id_, aa_sequence in aa_sequences.iteritems():  # enumerate(set(aa_sequences)):
            self.add_aa_sequence(id_, aa_sequence)

        self.aa_sequence_to_id = invert_dict(aa_sequences)
        counts = Counter((self.aa_sequence_to_id[h.aa_sequence] for h in hits))
        for aa_seq_id, count in counts.iteritems():
            row = self.hit_counts_table.row
            row["aa_seq_id"] = aa_seq_id
            row["hit_count"] = count
            row.append()

        self.finish_writing_aa_sequences()

    def _add_base_names(self, base_names):
        for id_, base_name in enumerate(set(base_names)):
            self.add_base_name(id_, base_name)
        self.finish_writing_base_names()

    def _add_hit(self, hit):
        aa_seq_id = self.aa_sequence_to_id[hit.aa_sequence]
        row = self.hit_data_table.row
        row["hit_id"] = hit.id_
        row["base_name_id"] = self.base_name_to_id[hit.base_name]
        row["rt"] = hit.rt
        row["mz"] = hit.mz
        row["aa_seq_id"] = self.aa_sequence_to_id[hit.aa_sequence]
        row["score"] = hit.score
        row["is_higher_score_better"] = hit.is_higher_score_better
        row.append()

    def add_hits(self, hits):
        # it is important to write aa sequences and basenames before we write the hits
        # as hits link to aa sequences and base names
        self._add_aa_sequences(hits)
        self._add_base_names(set(h.base_name for h in hits))
        for hit in hits:
            self._add_hit(hit)

    def add_spectrum(self, spec):
        mzs, intensities = spec.get_peaks()
        self.mz_array.append(mzs)
        self.intensity_array.append(intensities)
        self.peak_imax += mzs.shape[0]
        # register peaks
        row = self.spectrum_table.row
        row["spec_id"] = self.spec_id
        row["ms_level"] = spec.getMSLevel()
        row["rt"] = spec.getRT()
        row["i_low"] = self.peak_imin
        row["i_high"] = self.peak_imax
        row.append()
        self.peak_imin = self.peak_imax
        last_spec_id = self.spec_id
        self.spec_id += 1
        return last_spec_id

    def link_spec_with_hit(self, spec_id, hit_id):
        row = self.hit_spectrum_link_table.row
        row["spec_id"] = spec_id
        row["hit_id"] = hit_id
        row.append()

    def add_convex_hull(self, hull):
        assert isinstance(hull, np.ndarray)
        assert hull.shape == (4, 2)   # 4 points, 2 coordinates
        rt_min, mz_min = hull.min(axis=0)
        rt_max, mz_max = hull.max(axis=0)
        row = self.convex_hull_table.row
        row["convex_hull_id"] = self.convex_hull_id
        row["rt_min"] = rt_min
        row["rt_max"] = rt_max
        row["mz_min"] = mz_min
        row["mz_max"] = mz_max
        row.append()
        last_hull_id = self.convex_hull_id
        self.convex_hull_id += 1
        return last_hull_id

    def link_convex_hull_with_hit(self, hull_id, hit_id):
        row = self.hit_convex_hull_link_table.row
        row["hit_id"] = hit_id
        row["convex_hull_id"] = hull_id
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
        self.hit_data_table.cols.aa_seq_id.create_index()
        self.hit_data_table.close()

        self.hit_spectrum_link_table.flush()
        self.hit_spectrum_link_table.cols.hit_id.create_index()
        self.hit_spectrum_link_table.cols.spec_id.create_index()
        self.hit_spectrum_link_table.flush()
        self.hit_spectrum_link_table.close()

        self.convex_hull_table.flush()
        self.convex_hull_table.cols.convex_hull_id.create_index()
        self.convex_hull_table.flush()
        self.convex_hull_table.close()

        self.hit_convex_hull_link_table.flush()
        self.hit_convex_hull_link_table.cols.hit_id.create_index()
        self.hit_convex_hull_link_table.cols.convex_hull_id.create_index()
        self.hit_convex_hull_link_table.flush()
        self.hit_convex_hull_link_table.close()

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
        self.convex_hull_table = self.file_.root.convex_hulls
        self.hit_data_table = self.file_.root.hit_data
        self.hit_counts_table = self.file_.root.hit_counts
        self.hit_spectrum_link_table = self.file_.root.hit_spectrum_links
        self.hit_convex_hull_link_table = self.file_.root.hit_convex_hulls_links

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

        strings = dict()
        for id_, segments in collected_segments.iteritems():
            segments.sort()  # sorts by segment_id
            full_str = "".join(s for (segment_id, s) in segments)
            strings[id_] = full_str
        return strings

    def _read_base_names(self):
        self.id_to_base_name = CompressedDataReader.fetch_strings(self.base_name_table, "base_name_id")

    def _read_aa_sequences(self):
        self.id_to_aa_sequence = CompressedDataReader.fetch_strings(self.aa_sequence_table, "aa_seq_id")
        self.aa_sequence_to_id = invert_dict(self.id_to_aa_sequence)
        self.no_hits_per_aa_sequence = dict()
        for row in self.hit_counts_table:
            id_ = row["aa_seq_id"]
            counts = row["hit_count"]
            self.no_hits_per_aa_sequence[id_] = counts

    def get_aa_sequences(self):
        return self.id_to_aa_sequence.values()

    def get_number_of_hits_for(self, aa_sequence):
        id_ = self.aa_sequence_to_id.get(aa_sequence)
        return self.no_hits_per_aa_sequence.get(id_, 0)

    def get_hits_for_aa_sequence(self, aa_sequence):
        t = self.hit_data_table

        hits = []
        aa_seq_id = self.aa_sequence_to_id.get(aa_sequence)
        rows = self.hit_data_table.where("aa_seq_id == %d" % aa_seq_id)
        for row in rows:
            base_name = self.id_to_base_name.get(row["base_name_id"])
            hit = Hit(row["hit_id"], aa_sequence, base_name, row["mz"], row["rt"], row["score"],
                      row["is_higher_score_better"])
            hits.append(hit)
        return hits

    def count_spectra_for(self, hit):
        rows = self.hit_spectrum_link_table.where("hit_id == %d" % hit.id_)
        return len(list(rows))

    def fetch_spectra(self, hit):
        rows0 = self.hit_spectrum_link_table.where("hit_id == %d" % hit.id_)
        for row0 in rows0:
            spec_id = row0["spec_id"]
            rows1 = self.spectrum_table.where("spec_id == %d" % spec_id)
            for row1 in rows1:
                i_low = row1["i_low"]
                i_high = row1["i_high"]
                mzs = self.mz_array[i_low:i_high]
                intensities = self.intensity_array[i_low:i_high]
                spec = oms.MSSpectrum()
                spec.set_peaks((mzs, intensities))
                spec.setRT(hit.rt)
                precursor = oms.Precursor()
                precursor.setMZ(hit.mz)
                spec.setPrecursors([precursor])
                yield spec

    def fetch_convex_hulls(self, hit):
        rows0 = self.hit_convex_hull_link_table.where("hit_id == %d" % hit.id_)
        for row0 in rows0:
            hull_id = row0["convex_hull_id"]
            rows = self.convex_hull_table.where("convex_hull_id == %d" % hull_id)
            for row in rows:
                rt_min = row["rt_min"]
                rt_max = row["rt_max"]
                mz_min = row["mz_min"]
                mz_max = row["mz_max"]
                yield rt_min, rt_max, mz_min, mz_max

    def fetch_chromatogram(self, rt_min, rt_max, mz_min, mz_max):
        rows0 = self.spectrum_table.where("(%d <= rt) & (rt <= %d) & (ms_level == 1)" % (rt_min, rt_max))
        rts = []
        ion_counts = []
        for row in rows0:
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
        return rts, ion_counts




if __name__ == "__main__":
    r = CompressedDataReader("/data/dose_minimized/collected.ivi")
    aaseq = "YYVPDTFLLQR"
    print r.get_number_of_hits_for(aaseq)
    print r.get_hits_for_aa_sequence(aaseq)
