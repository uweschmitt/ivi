from collections import defaultdict
import os

from tables import (IsDescription, StringCol, UInt64Col, UInt8Col, UInt16Col, Float32Col, Int64Col,
                    Int16Col, Int8Col, open_file, Filters, Float32Atom, Float64Col, BoolCol)


def invert_dict(d):
    return dict((v, k) for (k, v) in d.items())


CHUNKLEN = 32

class PyTablesAccessor(object):


    class AASequence(IsDescription):

        aa_seq_id = Int64Col()
        segment_id = Int8Col()
        segment = StringCol(CHUNKLEN)


    class BaseName(IsDescription):

        base_name_id = Int16Col()
        segment_id = Int8Col()
        segment = StringCol(CHUNKLEN)


    class Spectrum(IsDescription):

        spec_id = Int64Col()
        i_low = UInt64Col()
        i_high = UInt64Col()


    class HitData(IsDescription):

        hit_id = Int64Col()
        base_name_id = Int16Col()
        mz = Float32Col()
        rt = Float32Col()
        spec_id = Int64Col()
        aa_seq_id = Int64Col()
        score = Float64Col()
        is_higher_score_better = BoolCol()


class PyTablesWriter(PyTablesAccessor):

    def __init__(self, path):
        self.path = path
        self.file_ = open_file(path, mode="w")

        group = self.file_.create_group("/", 'hits', 'peptide hits')

        filters = Filters(complib='blosc', complevel=9)

        self.aa_sequence_table = self.file_.create_table(group,
                                                         'aa_sequences',
                                                         self.AASequence,
                                                         "AASequences",
                                                         filters=filters)
        self.base_name_table = self.file_.create_table(group,
                                                       'base_names',
                                                       self.BaseName,
                                                       "BaseNames",
                                                       filters=filters)
        self.spectrum_table = self.file_.create_table(group,
                                                      'spectra',
                                                      self.Spectrum,
                                                      "Spectra",
                                                      filters=filters)
        self.hit_data_table = self.file_.create_table(group,
                                                      "hit_data",
                                                      self.HitData,
                                                      "HitData",
                                                      filters=filters)

        self.peaks_array = self.file_.create_earray(group,
                                                    'peaks_array',
                                                    Float32Atom(),
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
        row = table.row
        for i, imin in enumerate(xrange(0, len(string), CHUNKLEN)):
            segment = string[imin:imin + CHUNKLEN]
            row[id_col] = id_
            row['segment_id'] = i
            row['segment'] = segment
            row.append()

    def add_aa_sequence(self, id_, sequence):
        PyTablesWriter.add_string(self.aa_sequence_table, "aa_seq_id", id_, sequence)
        self.aa_sequence_to_id[sequence] = id_

    def finish_writing_aa_sequences(self):
        self.aa_sequence_table.flush()

    def add_base_name(self, id_, name):
        PyTablesWriter.add_string(self.base_name_table, "base_name_id", id_, name)
        self.base_name_to_id[name] = id_

    def finish_writing_base_names(self):
        self.base_name_table.flush()

    def add_aa_sequences(self, aa_sequences):
        for id_, aa_sequence in enumerate(set(aa_sequences)):
            self.add_aa_sequence(id_, aa_sequence)
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
        self.hit_data_table.close()
        self.peaks_array.close()
        self.file_.close()


def fetch_spectrum(spec_table, peaks_array, id_):
    rows = spec_table.where("spec_id == %d" % id_)
    for row in rows:
        i_low = row["i_low"]
        i_high = row["i_high"]
        spec = peaks_array[i_low:i_high, :]
        return spec




def assemble_strings(table, id_col):
    collected = defaultdict(list)
    for row in table.iterrows():
        id_ = row[id_col]
        segment_id = row["segment_id"]
        segment = row["segment"]
        collected[id_].append((segment_id, segment))

    result = dict()
    for id_, segments in collected.iteritems():
        segments.sort()  # sorts by segment_id
        full_str = "".join(s for (segment_id, s) in segments)
        result[id_] = full_str

    return result


def fetch_hit(hit_id, hit_data_table, spec_table, peaks_array, base_names):
    rows = hit_data_table.where("hit_id == %d" % hit_id)
    for row in rows:
        mz = row["mz"]
        rt = row["rt"]
        spec_id = row["spec_id"]
        base_name_id = row["base_name_id"]
        spec = fetch_spectrum(spec_table, peaks_array, spec_id)
        base_name = base_names[base_name_id]
        return mz, rt, base_name, spec


def fetch_hits(aa_seq,  aa_sequence_to_hit_ids, hit_data_table, spec_table, peaks_array, base_names):
    hit_ids = aa_sequence_to_hit_ids[aa_seq]
    for hit_id in hit_ids:
        mz, rt, base_name, spec = fetch_hit(hit_id, hit_data_table, spec_table, peaks_array, base_names)
        yield aa_seq, hit_id, mz, rt, base_name, spec.shape


