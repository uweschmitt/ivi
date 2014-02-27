import os.path

import ident_viewer as iv

def test_0(data_path):
    here = os.path.dirname(os.path.abspath(__file__))
    result = iv.lib.collect_files(here, postfixes=(".mzML", ".idXML"))
    assert ".mzML" in result
    mzmls = result[".mzML"]
    assert len(mzmls) == 1
    assert os.path.basename(mzmls[0]) == "BSA1.mzML"

    assert ".idXML" in result
    idxmls = result[".idXML"]
    assert len(idxmls) == 1
    assert os.path.basename(idxmls[0]) == "BSA1_OMSSA.idXML"
