#encoding: utf-8

import pyopenms as oms
from collections import namedtuple, defaultdict
import time
import glob
import os

from structures import PyTablesWriter


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

    def __init__(self, writer, base_name, hits, rt_tol=1.0, mz_tol=0.1):
        self.writer = writer
        hits = sorted((h for h in hits if h.base_name == base_name), key=lambda hit: hit.rt)
        self.binned_hits = defaultdict(list)
        for h in hits:
            bin_id = int(h.rt / rt_tol)
            self.binned_hits[bin_id - 1].append(h)
            self.binned_hits[bin_id].append(h)
            self.binned_hits[bin_id + 1].append(h)
        self.imin = 0
        self.imax = 0
        self.rt_tol = rt_tol
        self.mz_tol = mz_tol
        self.num_collected = 0

    def _hits_in_bins_for(self, rt):
        bin_id = int(rt / self.rt_tol)
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
            mz = spec.getPrecursors()[0].getMZ()
            for hit in self._hits_in_bins_for(rt):
                if abs(hit.rt - rt) <= self.rt_tol and abs(hit.mz - mz) <= self.mz_tol:
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

        self.pep_file = pep_files[0]
        self.peak_map_files = _find_mz_ml_files(path_root_dir)


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

    def collect(self, out_file="hits.h5"):
        writer = PyTablesWriter(out_file)
        fh = oms.PepXMLFile()
        prots, peps = [], []
        fh.load(self.pep_file, prots, peps)
        print "got", len(prots), "proteins and", len(peps), "peptides in .pep.xml file"

        hits = self._extract_hits(peps)
        print "found", len(hits), "hits"

        writer.add_aa_sequences(set(h.aa_sequence for h in hits))
        writer.add_base_names(set(h.base_name for h in hits))

        for base_name, path in self.peak_map_files.items():
            print path
            consumer = Consumer(writer, base_name, hits, rt_tol=1.0, mz_tol=0.1)
            mzml_file = oms.MzMLFile()
            mzml_file.transform(path, consumer)

        writer.close()


collector = CollectHitsData("/data/dose/")
collector.collect()

# todo:

#  - multiprocessing ??

