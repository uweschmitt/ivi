
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

"""
for aaseq in sorted(hits):
    base = hits[aaseq]
    if len(base) > 1:
        print aaseq
        for b in base:
            print "  ", b
"""

accessions = defaultdict(set)
for i, pep in enumerate(peps):
    mz = pep.getMetaValue("MZ")
    rt = pep.getMetaValue("RT")
    base_name = pep.getMetaValue("summary_base_name")
    for ph in pep.getHits():
        for acc in ph.getProteinAccessions():
            accessions[acc].add((ph.getSequence().toString(), mz, rt, base_name))



fp = open("method_1.txt", "w")

for acc in accessions:
    print >> fp, acc
    items = sorted(accessions[acc])
    for seq, mz, rt, base_name in items:
        print >> fp, "    %-25s" % seq, "mz=%10.5f" % mz, "rt=%7.1f" % rt, "base_name=", base_name

fp.close()

sequences = defaultdict(set)

fp = open("method_2.txt", "w")

for i, pep in enumerate(peps):
    mz = pep.getMetaValue("MZ")
    rt = pep.getMetaValue("RT")
    base_name = pep.getMetaValue("summary_base_name")
    for ph in pep.getHits():
        seq = ph.getSequence().toString()
        sequences[seq].add((base_name, mz, rt))

for seq in sorted(sequences):
    print >> fp, seq
    items = sorted(sequences[seq])
    for base_name,mz, rt in items:
        print >> fp, "    mz=%10.5f" % mz, "rt=%7.1f" % rt, "base_name=", base_name
    print >> fp

fp.close()

