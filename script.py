#!/usr/bin/env python3.6
import fileinput
import numpy as np
import sys
import os
dirname = '/bighome/KomarovK/Projects/soc-dir/tests/SOC-molec/Thy4-opt-FC'
files = os.listdir(dirname)

for kk in files:
    if "script" in kk:
        continue
    out = open(kk, 'r')
    filedata = out.read()
    out.close()
    outdata = filedata.replace('RELWFN=DK','').replace('NSTATE=5','NSTATE=1').replace('GBASIS=cc-pVTZ EXTFIL=.T.','GBASIS=N31 NGAUSS=6 NDFUNC=1')
    fout = open(kk,'w')
    fout.write(outdata)
    fout.close()
