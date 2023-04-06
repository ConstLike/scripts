#!/usr/bin/env python3.8
import fileinput


DFTTYP_data = ('PBE0', 'BHHLYP', 'M06-2X', 'B3LYP',)

#GBASIS = 'GBASIS=cc-pVDZ EXTFIL=.T.', 'GBASIS=cc-pVTZ EXTFIL=.T.', 'GBASIS=cc-pVQZ EXTFIL=.T.', 'GBASIS=N31 NGAUSS=6 NDFUNC=1'
#GBASIS_out = 'cc-pVDZ', 'cc-pVTZ', 'cc-pVQZ', '6-31G-d'

GBASIS = ('GBASIS=TZVPall EXTFIL=.T.', 'GBASIS=aug-pcX2 EXTFIL=.T.', )
GBASIS_out = ('x2c-TZVPall', 'aug-pcX2' )

kegms = []
ikegms = 'kegms -q ryzn '

kegms.append('#!/bin/bash')

#atoms = ('C', 'Si', 'Ge')
atoms = ('C', 'Si', )
for atom in atoms:
    filedata = None
    f = open('mrsf-soc-'+atom+'-draft-DK.inp', 'r')
    inp = 'soc-'+atom+'-'
    filedata = f.read()
    f.close()
    ii=0
    for l in GBASIS:
        j = GBASIS_out[ii]
        for k in DFTTYP_data:
            outdata = filedata.replace('GBASIS=N31 NGAUSS=6 NDFUNC=1', l).replace('BHHLYP', k)
            outp = inp+k+'-'+j+'-DK'
            out = inp+k+'-'+j+'-DK.inp'
            kegms.append( ikegms+out )
            fout = open(out,'w')
            fout.write(outdata)
            fout.close()
        ii+=1

for k in kegms:
    print(k, sep='\n')

