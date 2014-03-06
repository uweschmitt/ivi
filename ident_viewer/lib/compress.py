#encoding: utf-8

import pyopenms as oms
from collections import namedtuple, defaultdict
import time
import glob
import os

from compress_io import PyTablesWriter
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


Hit = namedtuple("Hit", "aa_sequence, base_name, mz, rt, score, is_higher_score_better")


class Consumer(object):

    def __init__(self, writer, base_name, hits, rt_tolerance, mz_tolerance):
        self.writer = writer
        hits = [h for h in hits if h.base_name == base_name]
        self.binned_hits = defaultdict(list)
        for h in hits:
            bin_id = int(h.rt / rt_tolerance)
            #self.binned_hits[bin_id - 1].append(h)
            self.binned_hits[bin_id].append(h)
            #self.binned_hits[bin_id + 1].append(h)
        self.imin = 0
        self.imax = 0
        self.rt_tolerance = rt_tolerance
        self.mz_tolerance = mz_tolerance
        self.num_collected = 0

    def _hits_in_bins_for(self, rt):
        bin_id = int(rt / self.rt_tolerance)
        for h in self.binned_hits[bin_id - 1]:
            yield h
        for h in self.binned_hits[bin_id]:
            yield h
        for h in self.binned_hits[bin_id + 1]:
            yield h

    def consumeSpectrum(self, spec):
        if spec.getMSLevel() == 2:
            matched_hits = []
            rt = spec.getRT()
            mz = float(spec.getPrecursors()[0].getMZ())
            for hit in self._hits_in_bins_for(rt):
                if abs(hit.rt - rt) <= self.rt_tolerance:
                    # mz_tolerance has unit ppm:
                    if abs(hit.mz - mz) / mz <= self.mz_tolerance * 1e-6:
                        matched_hits.append(hit)

            if matched_hits:
                self.writer.add_spec_with_hits(spec, matched_hits)
                self.num_collected += 1

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
        self.peak_map_files = _find_mz_ml_files(path_root_dir)
        if self.peak_map_files:
            for f in self.peak_map_files.values():
                self.summed_sizes += os.stat(f).st_size
                logger.info("found peak map file %s" % f)
        else:
            logger.error("found no peak map files below %s" % path_root_dir)
            raise Exception("no peak maps found below %s" % path_root_dir)

    def _extract_hits(self, peps):

        hits = []
        for pep in peps:
            li = []
            pep.getKeys(li)
            rt = pep.getMetaValue("RT")
            mz = pep.getMetaValue("MZ")
            base_name = pep.getMetaValue("summary_base_name")
            base_name = os.path.basename(base_name)
            base_name, __, __ = base_name.partition("~")
            is_higher_score_better = pep.isHigherScoreBetter()
            for ph in pep.getHits():
                aa_sequence = ph.getSequence().toString()
                score = ph.getScore()
                hit = Hit(aa_sequence, base_name, mz, rt, score, is_higher_score_better)
                hits.append(hit)
        return hits

    def collect(self, out_file, mz_tolerance=20.0, rt_tolerance=5.0):
        with measure_time("reading identifcations"):
            writer = PyTablesWriter(out_file)
            fh = oms.PepXMLFile()
            prots, peps = [], []
            fh.load(self.pep_file, prots, peps)
        logger.info("got %d protein and %d peptide identifications" % (len(prots), len(peps),))

        hits = self._extract_hits(peps)
        logger.info("extracted %d peptide hits" % len(hits))

        writer.add_aa_sequences(set(h.aa_sequence for h in hits))
        logger.info("wrote aa sequences")
        writer.add_base_names(set(h.base_name for h in hits))
        logger.info("wrote base names")

        for base_name, path in self.peak_map_files.items():
            with measure_time("fetching peaks from %s" % path):
                consumer = Consumer(writer, base_name, hits, rt_tolerance, mz_tolerance)
                mzml_file = oms.MzMLFile()
                mzml_file.transform(path, consumer)

        writer.close()
        final_bytes = os.stat(out_file).st_size
        logger.info("target file %s written and closed" % out_file)
        logger.info("size of all input files: %s" % (format_bytes(self.summed_sizes)))
        logger.info("size of compressed file: %s" % (format_bytes(final_bytes)))
        factor = self.summed_sizes / final_bytes
        logger.info("compression factor is %.1f" % factor)


if __name__ == "__main__":

    collector = CollectHitsData("/data/dose/")
    collector.collect()

# todo:

#  - multiprocessing ??

