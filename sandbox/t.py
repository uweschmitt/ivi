from collections import defaultdict
import os.path
import pyopenms as p

fh = p.PepXMLFile()
props, peps = [], []

fh.load("InterProphet.pep.xml", props, peps)

print len(props), len(peps)

hits = defaultdict(set)

for pep in peps:
    base = pep.getMetaValue("summary_base_name")
    base = os.path.basename(base)
    for ph in pep.getHits():
        aaseq = ph.getSequence().toString()
        hits[aaseq].add(base)

for aaseq in sorted(hits):
    base = hits[aaseq]
    if len(base) > 1:
        print aaseq
        for b in base:
            print "  ", b
