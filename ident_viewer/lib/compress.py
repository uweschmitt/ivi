#encoding: utf-8

import pyopenms as oms
from collections import defaultdict
import glob
import os

from compress_io import CompressedDataWriter, Hit
from ..std_logger import logger

from ..helpers import measure_time, format_bytes


def _find_pep_xml_files(root_dir):
    return glob.glob(os.path.join(root_dir, "*", "*.pep.xml"))


def _find_mz_ml_files(root_dir):
    rv = dict()
    for p in glob.glob(os.path.join(root_dir, "*", "*.mzML")):
        base_name, __ = os.path.splitext(os.path.basename(p))
        rv[base_name] = p
    return rv

def _find_mz_xml_files(root_dir):
    rv = dict()
    for p in glob.glob(os.path.join(root_dir, "*", "*.mzXML")):
        base_name, __ = os.path.splitext(os.path.basename(p))
        rv[base_name] = p
    return rv

class Consumer(object):

    def __init__(self, writer, base_name, hits, rt_tolerance, mz_tolerance, matched_hit_ids):
        self.writer = writer
        hits = [h for h in hits if h.base_name == base_name]
        self.rt_tolerance = rt_tolerance
        self.mz_tolerance = mz_tolerance
        self.binned_hits = defaultdict(list)
        for h in hits:
            bin_id = self._bin_id(h.rt)
            self.binned_hits[bin_id].append(h)
        self.imin = 0
        self.imax = 0
        self.num_collected = 0
        self.matched_hit_ids = matched_hit_ids
        self.min_rt = None
        self.max_rt = None

    def _bin_id(self, rt):
        return int(rt / self.rt_tolerance)

    def _hits_in_bins_for(self, rt):
        """ yields candidates for rt hits up to given tolerance """
        # as a rt value might be next to a multiple of rt_tolerance we have to look up
        # the neighbouring bins to:
        bin_id = self._bin_id(rt)
        for h in self.binned_hits[bin_id - 1]:
            yield h
        for h in self.binned_hits[bin_id]:
            yield h
        for h in self.binned_hits[bin_id + 1]:
            yield h

    def consumeSpectrum(self, spec):
        if spec.getMSLevel() == 2:
            matching_hits = []
            rt = spec.getRT()
            if self.min_rt is None:
                self.min_rt = rt
                self.max_rt = rt
            else:
                self.min_rt = min(self.min_rt, rt)
                self.max_rt = max(self.max_rt, rt)
            mz = float(spec.getPrecursors()[0].getMZ())
            for hit in self._hits_in_bins_for(rt):
                if abs(hit.rt - rt) <= self.rt_tolerance:
                    # mz_tolerance has unit ppm:
                    if abs(hit.mz - mz) / mz <= self.mz_tolerance * 1e-6:
                        matching_hits.append(hit)
            if matching_hits:
                spec_id = self.writer.add_spectrum(spec)
                for hit in matching_hits:
                    self.writer.link_spec_with_hit(spec_id, hit.id_)
                    self.num_collected += 1
                    self.matched_hit_ids.add(hit.id_)

    def consumeChromatogram(self, chromo):
        pass

    def setExperimentalSettings(self, settings):
        file_name = settings.getSourceFiles()[0].getNameOfFile()
        self.base_name, __ = os.path.splitext(file_name)

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

    def _extract_hits(self, peps):

        hits = []
        hit_id = 0
        for pep in peps:
            li = []
            pep.getKeys(li)
            rt = pep.getMetaValue("RT")
            if rt == 0.0:
                continue
            mz = pep.getMetaValue("MZ")
            base_name = pep.getBaseName()
            base_name = os.path.basename(base_name)
            base_name, __, __ = base_name.partition("~")
            is_higher_score_better = pep.isHigherScoreBetter()
            for ph in pep.getHits():
                aa_sequence = ph.getSequence().toString()
                score = ph.getScore()
                hit = Hit(hit_id, aa_sequence, base_name, mz, rt, score, is_higher_score_better)
                hit_id += 1
                hits.append(hit)
        return hits

    def collect(self, out_file, unmatched_hits_file, mz_tolerance=20.0, rt_tolerance=5.0):
        with measure_time("collecting and compressing data for visualisation"):
            self._collect(out_file, unmatched_hits_file, mz_tolerance, rt_tolerance)


    def _collect(self, out_file, unmatched_hits_file, mz_tolerance, rt_tolerance):
        writer = CompressedDataWriter(out_file)
        with measure_time("reading identifcations"):
            fh = oms.PepXMLFile()
            prots, peps = [], []
            s = oms.String()
            e = oms.MSExperiment()
            fh.load(self.pep_file, prots, peps, "", e, 1)     # use precursor data
        logger.info("got %d protein and %d peptide identifications" % (len(prots), len(peps),))

        hits = self._extract_hits(peps)
        logger.info("extracted %d peptide hits" % len(hits))

        writer.add_hits(hits)
        logger.info("wrote hits")

        matched_hit_ids = set()

        for base_name, path in self.peak_map_files.items():
            with measure_time("fetching peaks from %s" % path):
                consumer = Consumer(writer, base_name, hits, rt_tolerance, mz_tolerance,
                                    matched_hit_ids)
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

        final_bytes = os.stat(out_file).st_size
        logger.info("target file %s written and closed" % out_file)
        logger.info("size of all input files: %s" % (format_bytes(self.summed_sizes)))
        logger.info("size of compressed file: %s" % (format_bytes(final_bytes)))
        factor = self.summed_sizes / final_bytes
        logger.info("compression factor is %.1f" % factor)

        writer.close()


if __name__ == "__main__":

    collector = CollectHitsData("/data/dose/")
    collector.collect("out.ivi")
