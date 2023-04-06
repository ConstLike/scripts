#!/usr/bin/env python3.6

# Developed by Konstantin Komarov.

import fileinput
import os
import sys
import numpy as np
import argparse


def Extract_SOC_1e_2e(file):
    global energy_and_order,SOC_val, E_ref, GS
    filedata = None
    f = open(file, 'r')
    filedata = f.read()
    f.close()
    out = filedata.replace('I. Abs. value =', ' I. Abs. value =')
    out = out.splitlines()
    Order_of_states = []
    SOC_Order_of_states = []
    energy_and_order = []
    SOC_val = []
    soc_energy_and_order = []
    nstate=0
    for il, l in enumerate(out):
        if "TDDFT INPUT PARAMETERS" in l:
            nstate = int(out[il+2].split()[1])

        if "SUMMARY" in l:
            k = 0
            iS = 0
            iT = 1
            while k <= nstate:
                if int(out[il+7+k].split()[0]) == 0:
                    E_ref = float(out[il+7+k].split()[2])
                    if k==nstate:
                        break
                    else:
                        k+=1
                if float(out[il+7+k].split()[4])==0.0:
                    row = ( 'S'+str(iS)+' ',
                             float(out[il+7+k].split()[2]),
                             float(out[il+7+k].split()[8]),
                             str(out[il+7+k].split()[1]),
                            float(out[il+7+k].split()[5]),
                            float(out[il+7+k].split()[6]),
                            float(out[il+7+k].split()[7]),
                           )
                    if row[0]=='S0 ':
                        GS = float(out[il+7+k].split()[2])
                    Order_of_states.append( 'S'+str(iS))
                    SOC_Order_of_states.append( 'S'+str(iS))
                    iS += 1
                if float(out[il+7+k].split()[4])==2.0:
                    row = ( 'T'+str(iT)+'(Ms=0)'+' ',
                            float(out[il+7+k].split()[2]),
                            float(out[il+7+k].split()[8]),
                            str(out[il+7+k].split()[1]),
                            float(out[il+7+k].split()[5]),
                            float(out[il+7+k].split()[6]),
                            float(out[il+7+k].split()[7]),
                          )
                    if row[0]=='T1(Ms=0) ':
                        GS = float(out[il+7+k].split()[2])
                    iT += 1
                if float(out[il+7+k].split()[4])==6.0:
                    row = ( 'Q'+str(iT)+' '*7,
                            float(out[il+7+k].split()[2]),
                            float(out[il+7+k].split()[8]),
                            str(out[il+7+k].split()[1]),
                            float(out[il+7+k].split()[5]),
                            float(out[il+7+k].split()[6]),
                            float(out[il+7+k].split()[7]),
                          )
                    if row[0]=='Q1 ':
                        GS = float(out[il+7+k].split()[2])
                    Order_of_states.append(     'T'+str(iT)+'(Ms=1)')
                    iT += 1
                energy_and_order.append( row )
                k+=1
            Right_order_of_states = sorted(energy_and_order, key=lambda x: x[0])

def Check_file(file):
    global status
    f = open(file, 'r')#  >>>>>>>> TRY >>>>>>>>>> TO >>>>>>>>>>>>> USE LIKE >>>>>>>>>>>> THIS >>>>>>>>>>>>>>>>    script-SOC-table-1e-2e-abs.py -i log_file.log
    filedata = f.readlines()
    f.close()
    status = 0
    for il, l in enumerate(filedata):
        if "error" in l:
           status = 1
           return

def command_line_args():
    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-i', '--input',
        type=str,
        help='Provide the input.log file')

    parser.add_argument(
        '-r','--rounding_energy',
        default=3,
        type=int,
        help="Rounding of excited energy 1=0.0, 2=0.00, 3=0.000 and so om")

    return parser.parse_args()

if __name__ == '__main__':

    arg = command_line_args()
    file = arg.input
    rounding = arg.rounding_energy

    Check_file(file)#  >>>>>>>> TRY >>>>>>>>>> TO >>>>>>>>>>>>> USE LIKE >>>>>>>>>>>> THIS >>>>>>>>>>>>>>>>    script-SOC-table-1e-2e-abs.py -i log_file.log
    if status == 1:
        print(' ')
        os.system('echo " Hi" $USER"!"')
        print(' I checked your',file,'file. There is ERROR!','\n')
        sys.exit()

    Extract_SOC_1e_2e(file)

    f = file.replace('.log','.out')
    fout = open(f, 'w')
    print(' ')
    os.system('echo " Hi" $USER"!"')
    print(' Output file has been created ->>',f,'<<- Please, have a look!','\n')

    newline = '%10.'+str(rounding)+'f'

    fout.write('\n')
    fout.write('Input.file: '+file+'\n')
    fout.write('NON.SOC.MRSF.ENERGY:\n')
    fout.write('State'+' '*7+'Symmetry'+' '*6+'Hartree     eV.exited.rel.ROHF  eV.exited.rel.S0  Oscillator.Strength  Trans.Dipole.Vec       X             Y             Z\n')
    for i in enumerate(energy_and_order):
        state = str(i[1][0])
        symm = str(i[1][3])
        state_line = len(state)+len(symm)
        norm1_line = 13
        if state_line<=norm1_line:
            state = state+' '*(norm1_line-state_line)
        E_ev0 = round((i[1][1]),10)
        E_ev1 = round((i[1][1]-E_ref)*27.2107,rounding)
        E_ev2 = round((i[1][1]-GS)*27.2107,rounding)
        OscStr = round(i[1][2],4)
        TransDipoleX = round((i[1][4]),5)
        TransDipoleY = round((i[1][5]),5)
        TransDipoleZ = round((i[1][6]),5)
        TransDipoleVec = round(np.sqrt(TransDipoleX**2+TransDipoleY**2+TransDipoleZ**2),5)
        wout = state+' '*4\
             + symm+' '*4\
             + str('%10.10f' % E_ev0)+' '*4\
             + str(newline % E_ev1)+' '*10\
             + str(newline % E_ev2)+' '*10\
             + str('%10.4f' % OscStr)+' '*10\
             + str('%10.4f' % TransDipoleVec)+' '*4\
             + str('%10.4f' % TransDipoleX)+' '*4\
             + str('%10.4f' % TransDipoleY)+' '*4\
             + str('%10.4f' % TransDipoleZ)
        fout.write(wout+'\n')

    fout.close()

