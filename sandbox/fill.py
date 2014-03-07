import pdb
import tables
import numpy
import random

class MS1Peak(tables.IsDescription):
    rt = tables.Float32Col()
    mz = tables.Float32Col()
    intensity = tables.Float32Col()


h5file = tables.open_file('peaks.h5', mode='w')
group = h5file.create_group("/", 'lcms', 'LCMS data')

filters = tables.Filters(complevel=9, complib="blosc")


table = h5file.create_table(group, 'ms1', MS1Peak, "MS1 peaks", expectedrows=1000*1000,
        filters=filters)

peak = table.row

for rt in range(1000):
    for ii in range(1000):
        peak["rt"] = random.random()
        peak["mz"] = random.random()
        peak["intensity"] = random.random()
        peak.append()

table.cols.rt.create_csindex()
table.flush()

h5file.close()

