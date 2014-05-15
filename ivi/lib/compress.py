import pdb
# encoding: utf-8

import pyopenms as oms
from collections import defaultdict
import glob
import os

from compress_io_write import CompressedDataWriter
from data_structures import Hit
from id_provider import IdProvider

from ..std_logger import logger

from ..helpers import measure_time, format_bytes

from data_structures import Spectrum, Precursor


def _find_pep_xml_files(root_dir):
    return glob.glob(os.path.join(root_dir, "*", "*.pep.xml"))


def _find_files(root_dir, pattern):
    rv = dict()
    for p in glob.glob(os.path.join(root_dir, "*", pattern)):
        base_name, __ = os.path.splitext(os.path.basename(p))
        rv[base_name] = p
    return rv


def _find_mz_ml_files(root_dir):
    return _find_files(root_dir, "*.mzML")


def _find_mz_xml_files(root_dir):
    return _find_files(root_dir, "*.mzXML")


def _find_feature_xml_files(root_dir):
    return _find_files(root_dir, "*.featureXML")


class HitFinder(object):

    """ fast rt / mz pair search with given tolerances

        internally maps floating point rt / mz values to bin integer indices which serve as
        dictionary keys.
    """

    def __init__(self, rt_tolerance_s, mz_tolerance_ppm):
        self.rt_tolerance_s = rt_tolerance_s
        self.mz_tolerance_ppm = mz_tolerance_ppm
        self.max_mz_tol_abs = 5000.0 * mz_tolerance_ppm * 1e-6
        self.binned_hits = dict()

    def add_hit(self, hit):
        bin_id_rt, bin_id_mz = self._bin_id(hit.rt, hit.mz)
        self.binned_hits.setdefault(bin_id_rt, dict()).setdefault(bin_id_mz, []).append(hit)

    def _bin_id(self, rt, mz):
        # this mapping is "compressing", aka "non injective", as it maps
        # different rt / mz values to the same bin_id pair:
        return int(rt / self.rt_tolerance_s), int(mz / self.max_mz_tol_abs)

    def find_hits(self, rt, mz):
        """ yields candidates for rt hits up to given tolerance """
        # as a rt value might be next to a multiple of rt_tolerance we have to look up
        # the neighbouring bins to:
        bin_id_rt, bin_id_mz = self._bin_id(rt, mz)
        for i in (-1, 0, 1):
            sub_dict = self.binned_hits.get(bin_id_rt + i)
            if sub_dict is None:
                continue
            for j in (-1, 0, 1):
                for h in sub_dict.get(bin_id_mz + j, ()):
                    if abs(h.rt - rt) <= self.rt_tolerance_s:
                        if abs(h.mz - mz) / mz <= self.mz_tolerance_ppm * 1.0e-6:
                            yield h


class Consumer(object):

    def __init__(self, writer, hit_finder, matched_hit_ids, base_name):
        self.writer = writer
        self.hit_finder = hit_finder
        self.imin = 0
        self.imax = 0
        self.num_collected = 0
        self.matched_hit_ids = matched_hit_ids
        self.min_rt = None
        self.max_rt = None
        self.base_name = base_name

    def _convert_from_oms_type(self, spectrum):
        mzs, intensities = spectrum.get_peaks()
        precursors = [Precursor(p.getMZ()) for p in spectrum.getPrecursors()]
        return Spectrum(spectrum.getRT(), mzs, intensities, precursors, spectrum.getMSLevel())

    def consumeSpectrum(self, oms_spec):
        if oms_spec.getMSLevel() == 2:
            rt = oms_spec.getRT()
            if self.min_rt is None:
                self.min_rt = rt
                self.max_rt = rt
            else:
                self.min_rt = min(self.min_rt, rt)
                self.max_rt = max(self.max_rt, rt)
            mz = float(oms_spec.getPrecursors()[0].getMZ())
            matching_hits = [hit for hit in self.hit_finder.find_hits(rt, mz)]
            if matching_hits:
                spectrum = self._convert_from_oms_type(oms_spec)
                spectrum = spectrum.cleaned()
                spec_id = self.writer.add_spectrum(spectrum, self.base_name)
                for hit in matching_hits:
                    self.writer.link_spec_with_hit(spec_id, hit.id_)
                    self.num_collected += 1
                    self.matched_hit_ids.add(hit.id_)

        elif oms_spec.getMSLevel() == 1:
            spectrum = self._convert_from_oms_type(oms_spec)
            spectrum = spectrum.cleaned()
            self.writer.add_spectrum(spectrum, self.base_name)

    def consumeChromatogram(self, chromo):
        pass

    def setExperimentalSettings(self, settings):
        file_name = settings.getSourceFiles()[0].getNameOfFile()
        print file_name
        self.orig_base_name, __ = os.path.splitext(file_name)

    def setExpectedSize(self, n, m):
        pass


class CollectHitsData(object):

    def __init__(self, path_root_dir):
        pep_files = _find_pep_xml_files(path_root_dir)
        if not pep_files:
            raise Exception("no pep.xml file found below %s" % path_root_dir)
        if len(pep_files) > 1:
            raise Exception("multiple pepe files %s found below %s" % (", ".join(pep_files),
                                                                       path_root_dir))

        self.summed_sizes = 0
        self.hit_id_provider = IdProvider(10000000)
        self.pep_file = pep_files[0]

        self.summed_sizes += os.stat(self.pep_file).st_size

        logger.info("input pep.xml file is %s" % self.pep_file)

        self.peak_map_files = _find_mz_xml_files(path_root_dir)
        if self.peak_map_files:
            for f in self.peak_map_files.values():
                self.summed_sizes += os.stat(f).st_size
                logger.info("found peak map file %s" % f)
        else:
            logger.error("found no peak map files below %s" % path_root_dir)
            raise Exception("no peak maps found below %s" % path_root_dir)

        self.feature_map_files = _find_feature_xml_files(path_root_dir)
        if self.feature_map_files:
            for f in self.feature_map_files.values():
                self.summed_sizes += os.stat(f).st_size
                logger.info("found feature map file %s" % f)
        else:
            logger.error("found no feature map files below %s" % path_root_dir)
            raise Exception("no feature maps found below %s" % path_root_dir)

    def _extract_hits(self, peps, mz_tolerance_ppm, rt_tolerance_s):

        hits = []
        hit_finders = defaultdict(lambda: HitFinder(rt_tolerance_s, mz_tolerance_ppm))
        for pep in peps:
            li = []
            pep.getKeys(li)
            rt = pep.getRT()
            #  if rt == 0.0:
            #      continue
            mz = pep.getMZ()
            base_name = pep.getBaseName()
            base_name = os.path.basename(base_name)
            base_name, __, __ = base_name.partition("~")
            is_higher_score_better = pep.isHigherScoreBetter()
            for ph in pep.getHits():
                aa_sequence = ph.getSequence().toString()
                score = ph.getScore()
                hit_id = self.hit_id_provider.next_id()
                charge = ph.getCharge()
                hit = Hit(hit_id, aa_sequence, base_name, mz, rt, charge, score, is_higher_score_better)
                hits.append(hit)
                hit_finders[base_name].add_hit(hit)
        logger.info("extracted %d peptide hits" % len(hits))
        return hits, hit_finders

    def collect(self, out_file, unmatched_hits_file, mz_tolerance_ppm=20.0, rt_tolerance_s=5.0):
        with measure_time("collecting and compressing data for visualisation"):
            self._collect(out_file, unmatched_hits_file, mz_tolerance_ppm, rt_tolerance_s)

    def _collect(self, out_file, unmatched_hits_file, mz_tolerance_ppm, rt_tolerance_s):
        writer = CompressedDataWriter(out_file)

        # extract and write all hits from pep xml file:
        prots, peps = self._read_identifcations()
        hits, hit_finders = self._extract_hits(peps, mz_tolerance_ppm, rt_tolerance_s)
        writer.write_hits(hits)
        logger.info("wrote hits")

        # find features related to hits
        self._match_and_write_features(hits, hit_finders, writer)

        # collect ms1 spectra and find ms2 spectra related to hits
        self._match_and_write_spectra(hits, hit_finders, unmatched_hits_file, writer)

        writer.close()

        self._report_size_of_final_file(out_file)

    def _read_identifcations(self):
        prots, peps = [], []
        with measure_time("reading identifcations"):
            fh = oms.PepXMLFile()
            e = oms.MSExperiment()
            fh.load(self.pep_file, prots, peps, "", e, 1)     # use precursor data
        logger.info("got %d protein and %d peptide identifications" % (len(prots), len(peps),))
        return prots, peps

    def _match_and_write_features(self, hits, hit_finders, writer):
        for p in self.feature_map_files.values():
            with measure_time("match features from %s" % p):
                feature_counter = 0
                feature_map = oms.FeatureMap()
                oms.FeatureXMLFile().load(p, feature_map)
                base_file_name, __, __ = os.path.basename(p).partition("~")
                base_name, __ = os.path.splitext(base_file_name)
                hit_finder = hit_finders.get(base_name)
                if hit_finder is None:
                    logger.warn("no hits in .pep.xml for features in %s" % p)
                    continue
                for feature in feature_map:
                    feature_id = writer.add_feature(feature, base_name)
                    feature_counter += 1
                    for pep_id in feature.getPeptideIdentifications():
                        rt = pep_id.getRT()
                        mz = pep_id.getMZ()
                        is_higher_score_better = pep_id.isHigherScoreBetter()
                        for oms_hit in pep_id.getHits():
                            for hit in hit_finder.find_hits(rt, mz):
                                if hit.aa_sequence == oms_hit.getSequence().toString():
                                    break
                            else:
                                # no hit found in for loop, so create new hit:
                                hit_id = self.hit_id_provider.next_id()
                                aa_sequence = oms_hit.getSequence().toString()
                                score = oms_hit.getScore()
                                charge = oms_hit.getCharge()
                                hit = Hit(hit_id, aa_sequence, base_name, mz, rt, charge, score,
                                          is_higher_score_better)
                                hits.append(hit)
                                writer.add_hit(hit)
                            writer.link_feature_with_hit(feature_id, hit)

            logger.info("inserted %d features" % feature_counter)

    def _report_size_of_final_file(self, out_file):

        final_bytes = os.stat(out_file).st_size
        logger.info("target file %s written and closed" % out_file)
        logger.info("size of all input files: %s" % (format_bytes(self.summed_sizes)))
        logger.info("size of compressed file: %s" % (format_bytes(final_bytes)))
        factor = float(self.summed_sizes) / final_bytes
        logger.info("compression factor is %.1f" % factor)

    def _match_and_write_spectra(self, hits, hit_finders, unmatched_hits_file, writer):
        matched_hit_ids = set()
        for base_name, path in self.peak_map_files.items():
            hit_finder = hit_finders[base_name]
            with measure_time("fetching peaks from %s" % path):
                consumer = Consumer(writer, hit_finder, matched_hit_ids, base_name)
                mzxml_file = oms.MzXMLFile()
                mzxml_file.transform(path, consumer)
                logger.info("rt range in this file is %.1f ... %.1f seconds" % (consumer.min_rt,
                                                                                consumer.max_rt))

        all_hit_ids = set(h.id_ for h in hits)
        missing_hit_ids = sorted(all_hit_ids - matched_hit_ids)

        if missing_hit_ids:
            logger.warn("did not find ms2 spectrum for %d hits" % len(missing_hit_ids))
            if unmatched_hits_file is not None:
                i = 0
                hits.sort(key=lambda hit: (hit.base_name, hit.rt))
                with open(unmatched_hits_file, "w") as fp:
                    for hit in hits:
                        if hit.id_ in missing_hit_ids:
                            if i > 0:
                                print >> fp, "-" * 79
                            print >> fp, "%4d" % i, hit.aa_sequence
                            print >> fp, "base_name=", hit.base_name,
                            print >> fp, "mz=%10.5f" % hit.mz, "rt=%.1f" % hit.rt
                            i += 1
                logger.info("wrote unmatched hits to %s" % unmatched_hits_file)
        else:
            logger.info("found ms2 spectrum for all hits")


if __name__ == "__main__":

    collector = CollectHitsData("/data/dose/")
    collector.collect("out.ivi")
