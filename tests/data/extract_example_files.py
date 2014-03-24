import pyopenms as oms
from collections import namedtuple
from ident_viewer.lib import HitFinder


TMAX = 400.0
N = 20

Hit = namedtuple("Hit", "rt mz")

fh = oms.PepXMLFile()
peps, prots = [], []

# find 1000 peps from B08-08319 and 1000 from B08-08318, the first one will find matches
# in the featurexml file below, the othor one won't find matches.

fh.load("/data/dose/10_20140217062512939-923281/InterProphet.pep.xml", prots, peps)
prots = prots[:100]
pn = [pi for pi in peps if pi.getBaseName().startswith("B08-08319")][:1000]
print len(pn)
pn += [pi for pi in peps if pi.getBaseName().startswith("B08-08318")][:1000]
print len(pn)
peps = pn

fh = oms.FeatureXMLFile()
fmap = oms.FeatureMap()
fh.load("/data/dose/11_20140217094009824-923303/B08-08319~20100910185134835-50516.featureXML",
        fmap)

fh = oms.FileHandler()
mse = oms.MSExperiment()
fh.loadExperiment("/data/dose/01_20100910185134835-50516/B08-08319.mzXML", mse)

hf = HitFinder(5, 20)
for pi in peps:
    mz = pi.getMetaValue("MZ")
    rt = pi.getMetaValue("RT")
    if rt > TMAX:
        continue
    hf.add_hit(Hit(rt, mz))

matchin_hits_count = 0
non_matching_hits_count = 0
fmneu = oms.FeatureMap()
fmneu.setProteinIdentifications(fmap.getProteinIdentifications())

seen = set()

for f in fmap:
    for pi in f.getPeptideIdentifications():
        mz = pi.getMetaValue("MZ")
        rt = pi.getMetaValue("RT")
        if rt > TMAX:
            continue
        found = False
        for hit in hf.find_hits(rt, mz):
            if matchin_hits_count < N:
                if f.getUniqueId() not in seen:
                    fmneu.push_back(f)
                    seen.add(f.getUniqueId())
            found = True
        if not found:
            if non_matching_hits_count < N:
                if f.getUniqueId() not in seen:
                    fmneu.push_back(f)
                    seen.add(f.getUniqueId())
        if found:
            matchin_hits_count += 1
        else:
            non_matching_hits_count += 1

    if matchin_hits_count >= N and non_matching_hits_count >= N:
        print "done"
        break

print N, matchin_hits_count, non_matching_hits_count

fh = oms.FeatureXMLFile()
fh.store("reduced.featureXML", fmneu)
msneu = oms.MSExperiment()
for spec in mse:
    if spec.getRT() <= TMAX:
        msneu.addSpectrum(spec)

fh = oms.FileHandler()
fh.storeExperiment("reduced.mzXML", msneu)

pepsneu = []
for pep in peps:
    if pep.getMetaValue("RT") <= TMAX:
        pepsneu.append(pep)

fh = oms.PepXMLFile()
fh.store("reduced.pep.xml", prots, pepsneu)

fh = open("reduced.pep.xml", "r")
data = fh.read()
fh.close()

# writing pep.xml files sets base_name to filename, so we change this 
# now:
# (assumption for identiviewer_dataprocessing)
data = data.replace('base_name="reduced.pep.xml"', 'base_name="reduced~"')
data = data.replace("base_name='reduced.pep.xml'", "base_name='reduced~'")

fh = open("reduced.pep.xml", "w")
fh.write(data)
fh.close()

# now we read everything for timing and for checking file validity:

print
import time
start_at = time.time()

fh = oms.PepXMLFile()
print "read pep.xml"
fh.load("reduced.pep.xml", prots, peps)

fh = oms.FileHandler()
print "read mzXML"
fh.loadExperiment("reduced.mzXML", msneu)

fh = oms.FeatureXMLFile()
print "read featureXML"
fh.load("reduced.featureXML", fmneu)

print
print "reading reduced data sets needs %.1f seconds" % (time.time() - start_at)

import os
print
os.system("ls -ltrh reduced.*")
print
