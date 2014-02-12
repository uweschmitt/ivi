import ident_viewer as iv
import sys
import cStringIO


def _read(data_path):
    peptide_ids, protein_ids = iv.io.load_idxml_file(data_path("BSA1_OMSSA.idXML"))
    mse = iv.io.load_experiment(data_path("BSA1.mzML"))
    return mse, peptide_ids, protein_ids


def test_0(data_path):

    mse, peptide_ids, protein_ids = _read(data_path)

    score, seq, hit, spec = iv.assign.extract_hits(mse, peptide_ids, protein_ids).next()

    assert seq == "SHC(Carbamidomethyl)IAEVEK"

    sys.stdout = cStringIO.StringIO()
    try:
        for mz, ii, ion, info in iv.assign.PeptideHitAssigner().compute_assignment(hit, spec):
            print "%10.5f" % mz, "%e" % ii, "%-10s" % ion, info
    finally:
        output = sys.stdout.getvalue()
        sys.stdout = sys.__stdout__

    tobe = [line.strip() for line in """
                129.11508 5.574852e+00 b3+++      SHC*
                147.13916 4.676226e+01 y1+        K
                166.98907 4.726707e+00 b4+++      SHC*I
                188.03242 1.824428e+01 y3++       KEV
                190.16794 4.597599e+01 b5+++      SHC*IA
                193.22107 4.685121e+00 b3++       SHC*
                233.67889 2.499043e+01 b6+++      SHC*IAE
                252.83282 3.398308e+01 y4++       KEVE
                276.14185 1.092804e+02 y2+        KE
                285.22861 3.875825e+02 b5++       SHC*IA
                288.17639 5.589767e+01 y5++       KEVEA
                329.36063 7.927781e+00 y8+++      KEVEAIC*H
                375.31989 2.972997e+02 y3+        KEV
                385.13821 5.314980e+01 b3+        SHC*
                399.19064 1.024677e+01 b7++       SHC*IAEV
                424.69345 1.669854e+01 y7++       KEVEAIC*
                493.13998 2.392593e+00 y8++       KEVEAIC*H
                498.13400 2.578728e+02 b4+        SHC*I
                504.27200 8.241715e+02 y4+        KEVE
                569.28241 6.562495e+01 b5+        SHC*IA
                575.40710 7.541013e+01 y5+        KEVEA
                698.27173 1.949970e+00 b6+        SHC*IAE
                797.51617 1.818095e+00 b7+        SHC*IAEV
        """.split("\n")]
    tobe = [l for l in tobe if l]

    is_ = [l.strip() for l in output.split("\n")]
    is_ = [l for l in is_ if l]
    for (t, i) in zip(tobe, is_):
        assert t == i


def test_1(data_path):

    mse, pep_ids, prot_ids = _read(data_path)
    sequences = [seq for score, seq, hit, spec in iv.assign.extract_hits(mse, pep_ids, prot_ids)]

    sequences.sort()
    assert sequences[:9] == ['AEFVEVTK', 'AEFVEVTK', 'AEFVEVTK', 'AGAFSLPK', 'AGAFSLPK',
                             'AGDLLFFK', 'C(Carbamidomethyl)C(Carbamidomethyl)TESLVNR',
                             'C(Carbamidomethyl)C(Carbamidomethyl)TESLVNR',
                             'C(Carbamidomethyl)C(Carbamidomethyl)TESLVNR', ]

    assert sequences[-10:] == ['YIC(Carbamidomethyl)DNQDTISSK', 'YLYEIAR', 'YLYEIAR', 'YLYEIAR',
                               'YLYEIAR', 'YLYEIAR', 'YLYEIAR', 'YLYEIAR', 'YLYEIAR', 'YLYEIAR']

    assert len(sequences) == 77
