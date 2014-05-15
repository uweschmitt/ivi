from collections import defaultdict

from tables import open_file
import numpy as np

from id_provider import IdProvider
from data_structures import Hit, Spectrum, Precursor, PeakRange, PeakMap, Chromatogram, Feature


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

    def count_features_for(self, hit):
        rows = self.hit_feature_link_table.where("hit_id == %d" % hit.id_)
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

    def fetch_features_for_hit(self, hit):
        rows0 = self.hit_feature_link_table.where("hit_id == %d" % hit.id_)
        for row0 in rows0:
            feature_id = row0["feature_id"]
            rows = self.feature_table.where("feature_id == %d" % feature_id)
            for row in rows:
                base_name_id = row["base_name_id"]
                fid = row["feature_id_from_file"]
                base_name = self.base_name_id_provider.lookup_item(base_name_id)
                rtmin = row["rtmin"]
                rtmax = row["rtmax"]
                mzmin = row["mzmin"]
                mzmax = row["mzmax"]
                mass_traces = list(self._fetch_mass_traces_for_feature(feature_id))
                yield Feature(feature_id, base_name, fid, rtmin, rtmax, mzmin, mzmax,
                              mass_traces)

    def fetch_features_in_range(self, base_name, rtmin, rtmax, mzmin, mzmax):
        condition = """(%f <= rtmin) & (rtmax <= %f)\
                       & (%f <= mzmin) & (mzmax <= %f)""" % (rtmin, rtmax, mzmin, mzmax)
        return self._fetch_features(base_name, condition)

    def fetch_features_intersecting(self, base_name, rt_0, rt_1, mz_0, mz_1):
        condition = self._intersecting_condition(rt_0, rt_1, mz_0, mz_1)
        return self._fetch_features(base_name, condition)

    def _intersecting_condition(self, rt_0, rt_1, mz_0, mz_1):
        """
           (rtmin, mzmin) is in rect (rt_0, mz_0, rt_1, mz_1)
        or
           (rtmax, mzmax) is in rect (rt_0, mz_0, rt_1, mz_1)

        that is:

           rt_0 <= rtmin <= rt_1 and mz_0 <= mzmin <= mz_1
        or
           rt_0 <= rtmax <= rt_1 and mz_0 <= mzmax <= mz_1
        """
        cond_min = """({rt_0} <= rtmin) & (rtmin <= {rt_1}) \
                     &({mz_0} <= mzmin) & (mzmin <= {mz_1}) """.format(**locals())
        cond_max = """({rt_0} <= rtmax) & (rtmax <= {rt_1}) \
                     &({mz_0} <= mzmax) & (mzmax <= {mz_1}) """.format(**locals())

        condition = "({cond_min}) | ({cond_max})".format(**locals())
        return condition

    def _fetch_features(self, base_name, condition):
        base_name_id = self.base_name_id_provider.lookup_id(base_name)
        full_condition = "(base_name_id == %d) & (%s)" % (base_name_id, condition)
        rows = self.feature_table.where(full_condition)
        for row in rows:
            rtmin = row["rtmin"]
            rtmax = row["rtmax"]
            mzmin = row["mzmin"]
            mzmax = row["mzmax"]
            feature_id = row["feature_id"]
            fid = row["feature_id_from_file"]
            mass_traces = list(self._fetch_mass_traces_for_feature(feature_id))
            yield Feature(feature_id, base_name, fid, rtmin, rtmax, mzmin, mzmax, mass_traces)

    def _fetch_mass_traces_for_feature(self, feature_id):
        rows = self.mass_trace_table.where("feature_id == %d" % feature_id)
        for row in rows:
            rtmin = row["rtmin"]
            rtmax = row["rtmax"]
            mzmin = row["mzmin"]
            mzmax = row["mzmax"]
            yield PeakRange(rtmin, rtmax, mzmin, mzmax)

    def fetch_mass_traces_in_range(self, base_name, rtmin, rtmax, mzmin, mzmax):
        base_name_id = self.base_name_id_provider.lookup_id(base_name)
        rows = self.mass_trace_table.where("""(base_name_id == %d) \
                                               & (%f <= rtmin) & (rtmax <= %f) \
                                               & (%f <= mzmin) & (mzmax <= %f) \
                                           """ % (base_name_id, rtmin, rtmax, mzmin, mzmax)
                                           )
        for row in rows:
            rtmin = row["rtmin"]
            rtmax = row["rtmax"]
            mzmin = row["mzmin"]
            mzmax = row["mzmax"]
            yield PeakRange(rtmin, rtmax, mzmin, mzmax)

    def fetch_mass_traces_intersecting(self, base_name, rt_0, rt_1, mz_0, mz_1):
        """
           (rtmin, mzmin) is in rect (rt_0, mz_0, rt_1, mz_1)
        or
           (rtmax, mzmax) is in rect (rt_0, mz_0, rt_1, mz_1)

        that is:

           rt_0 <= rtmin <= rt_1 and mz_0 <= mzmin <= mz_1
        or
           rt_0 <= rtmax <= rt_1 and mz_0 <= mzmax <= mz_1
        """
        base_name_id = self.base_name_id_provider.lookup_id(base_name)
        cond_base_name = "base_name_id == {base_name_id}".format(base_name_id=base_name_id)
        is_condition = self._intersecting_condition(rt_0, rt_1, mz_0, mz_1)
        condition = "({cond_base_name}) & ({is_condition}) ".format(**locals())
        rows = self.mass_trace_table.where(condition)
        for row in rows:
            rtmin = row["rtmin"]
            rtmax = row["rtmax"]
            mzmin = row["mzmin"]
            mzmax = row["mzmax"]
            yield PeakRange(rtmin, rtmax, mzmin, mzmax)

    def fetch_feature_ranges_for_base_name(self, base_name):
        base_name_id = self.base_name_id_provider.lookup_id(base_name)
        rows = self.feature_table.where("base_name_id == %d" % base_name_id)
        for row in rows:
            rtmin = row["rtmin"]
            rtmax = row["rtmax"]
            mzmin = row["mzmin"]
            mzmax = row["mzmax"]
            yield PeakRange(rtmin, rtmax, mzmin, mzmax)

    def fetch_chromatogram(self, rtmin, rtmax, mzmin, mzmax, base_name):
        base_name_id = self.base_name_id_provider.lookup_id(base_name)
        rows = self.spectrum_table.where(
            """(base_name_id == %d) & (%f <= rt) & (rt <= %f) & (ms_level == 1)""" % (base_name_id, rtmin, rtmax))
        rts = []
        ion_counts = []
        for row in rows:
            rts.append(row["rt"])
            i_low = row["i_low"]
            i_high = row["i_high"]
            mzs = self.mz_array[i_low:i_high]
            intensities = self.intensity_array[i_low:i_high]
            view = (mzmin <= mzs) * (mzs <= mzmax)
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
