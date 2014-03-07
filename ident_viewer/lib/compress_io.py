from collections import defaultdict, namedtuple, Counter
import pyopenms as oms

from tables import (IsDescription, StringCol, UInt64Col, Float32Col, Int64Col, Float64Atom,
                    Int16Col, Int8Col, open_file, Filters, Float32Atom, Float64Col, BoolCol)


def invert_dict(d):
    return dict((v, k) for (k, v) in d.items())

def invert_non_injective_dict(d):
    inv_dict = defaultdict(list)
    for k, v in d.iteritems():
        inv_dict[v].append(k)
    return inv_dict


Hit = namedtuple("Hit", "aa_sequence, base_name, mz, rt, score, is_higher_score_better, spec_id")


CHUNKLEN = 32


class CompressedDataWriter(object):

    class AASequence(IsDescription):

        """ pytables has no variable length string arrays, so we split strings into segments
            of size CHUNKLEN indexed by segment_id
        """

        aa_seq_id = Int64Col()
        segment_id = Int8Col()
        segment = StringCol(CHUNKLEN)

    class HitsPerAASequenceCounter(IsDescription):

        """ counts number of hits per aa sequenc
        """
        aa_seq_id = Int64Col()
        hit_count = UInt64Col()

    class BaseName(IsDescription):

        """ pytables has no variable length string arrays, so we split strings into segments
            of size CHUNKLEN indexed by segment_id
        """

        base_name_id = Int16Col()
        segment_id = Int8Col()
        segment = StringCol(CHUNKLEN)

    class Spectrum(IsDescription):

        """ we keep all peaks in one huge peaks_array of size (N, 2).
            this table references a spectrum with id 'spec_id' to peaks_array[i_low:ihigh, :]
        """

        spec_id = Int64Col()
        i_low = UInt64Col()
        i_high = UInt64Col()

    class HitData(IsDescription):

        hit_id = Int64Col()
        base_name_id = Int16Col()
        mz = Float64Col()
        rt = Float32Col()
        spec_id = Int64Col()
        aa_seq_id = Int64Col()
        score = Float64Col()
        is_higher_score_better = BoolCol()

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

        self.hit_data_table = self.file_.create_table(self.root,
                                                      "hit_data",
                                                      self.HitData,
                                                      "HitData",
                                                      filters=filters)

        self.peaks_array = self.file_.create_earray(self.root,
                                                    'peaks_array',
                                                    Float64Atom(),
                                                    (0, 2),
                                                    filters=filters,)

        self.base_name_to_id = dict()
        self.aa_sequence_to_id = dict()
        self.peak_imin = 0
        self.peak_imax = 0
        self.spec_id = 0
        self.hit_id = 0

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

    def add_aa_sequence(self, id_, sequence):
        CompressedDataWriter.add_string(self.aa_sequence_table, "aa_seq_id", id_, sequence)
        self.aa_sequence_to_id[sequence] = id_

    def finish_writing_aa_sequences(self):
        self.aa_sequence_table.flush()
        self.hit_counts_table.flush()

    def add_base_name(self, id_, name):
        CompressedDataWriter.add_string(self.base_name_table, "base_name_id", id_, name)
        self.base_name_to_id[name] = id_

    def finish_writing_base_names(self):
        self.base_name_table.flush()

    def add_aa_sequences(self, hits):
        aa_sequences = dict(enumerate(set(h.aa_sequence for h in hits)))
        for id_, aa_sequence in aa_sequences.iteritems():  # enumerate(set(aa_sequences)):
            self.add_aa_sequence(id_, aa_sequence)

        aa_sequence_to_id = invert_dict(aa_sequences)
        counts = Counter((aa_sequence_to_id[h.aa_sequence] for h in hits))

        for aa_seq_id, count in counts.iteritems():
            row = self.hit_counts_table.row
            row["aa_seq_id"] = aa_seq_id
            row["hit_count"] = count
            row.append()

        self.finish_writing_aa_sequences()

    def add_base_names(self, base_names):
        for id_, base_name in enumerate(set(base_names)):
            self.add_base_name(id_, base_name)
        self.finish_writing_base_names()

    def add_hit(self, hit, spec_id):
        row = self.hit_data_table.row
        row["hit_id"] = self.hit_id
        row["base_name_id"] = self.base_name_to_id[hit.base_name]
        row["rt"] = hit.rt
        row["mz"] = hit.mz
        row["spec_id"] = spec_id
        row["aa_seq_id"] = self.aa_sequence_to_id[hit.aa_sequence]
        row["score"] = hit.score
        row["is_higher_score_better"] = hit.is_higher_score_better
        row.append()
        self.hit_id += 1

    def add_spectrum(self, spec):
        peaks = spec.get_peaks()
        self.peaks_array.append(peaks)
        self.peak_imax += peaks.shape[0]
        # register peaks
        row = self.spectrum_table.row
        row["spec_id"] = self.spec_id
        row["i_low"] = self.peak_imin
        row["i_high"] = self.peak_imax
        row.append()
        self.peak_imin = self.peak_imax
        last_spec_id = self.spec_id
        self.spec_id += 1
        return last_spec_id

    def add_spec_with_hits(self, spec, hits):
        spec_id = self.add_spectrum(spec)
        for hit in hits:
            self.add_hit(hit, spec_id)

    def close(self):
        self.aa_sequence_table.close()
        self.spectrum_table.cols.spec_id.create_index()
        self.spectrum_table.close()
        self.hit_data_table.cols.hit_id.create_index()
        self.hit_data_table.cols.aa_seq_id.create_index()
        self.hit_data_table.close()
        self.peaks_array.close()
        self.file_.close()


class CompressedDataReader(object):

    def __init__(self, path):
        self.file_ = open_file(path, mode="r")

        # shortcuts
        self.spec_table = self.file_.root.spectra
        self.peaks_array = self.file_.root.peaks_array
        self.base_name_table = self.file_.root.base_names
        self.aa_sequence_table = self.file_.root.aa_sequences
        self.hit_data_table = self.file_.root.hit_data
        self.hit_counts_table = self.file_.root.hit_counts

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
        hits = []
        aa_seq_id = self.aa_sequence_to_id.get(aa_sequence)
        if aa_seq_id is None:
            return hits
        rows = self.hit_data_table.where("aa_seq_id == %d" % aa_seq_id)
        for row in rows:
            base_name = self.id_to_base_name.get(row["base_name_id"])
            hit = Hit(aa_sequence, base_name, row["mz"], row["rt"], row["score"],
                      row["is_higher_score_better"], row["spec_id"])
            hits.append(hit)
        return hits

    def fetch_spectrum(self, hit):
        rows = self.spec_table.where("spec_id == %d" % hit.spec_id)
        for row in rows:
            i_low = row["i_low"]
            i_high = row["i_high"]
            peaks = self.peaks_array[i_low:i_high, :]
            spec = oms.MSSpectrum()
            spec.set_peaks(peaks)
            spec.setRT(hit.rt)
            precursor = oms.Precursor()
            precursor.setMZ(hit.mz)
            spec.setPrecursors([precursor])
            return spec
