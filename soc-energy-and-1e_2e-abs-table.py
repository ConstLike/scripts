#!/usr/bin/env python3.6

# Developed by Konstantin Komarov.

import fileinput
import os
import sys
import numpy as np
import argparse


def Extract_SOC_1e_2e(file):
    global energy_and_order, soc_energy_and_order, SOC_val, E_ref, GS
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

        if "SUMMARY OF MRSF-DFT RESULTS" in l:
            k = 0
            iS = 0
            iT = 1
            while k <= nstate*2:
                if int(out[il+7+k].split()[0]) == 0:
                    E_ref = float(out[il+7+k].split()[2])
                    if k==nstate*2:
                        break
                    else:
                        k+=1
                if float(out[il+7+k].split()[4])==0.0:
                    row = ( 'S'+str(iS)+' ',
                             float(out[il+7+k].split()[2]),
                             float(out[il+7+k].split()[8]),
                             str(out[il+7+k].split()[1]),
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
                          )
                    Order_of_states.append(     'T'+str(iT)+'(Ms=0)')
                    SOC_Order_of_states.append( 'T'+str(iT)+'{1}(Ms=-1)')
                    SOC_Order_of_states.append( 'T'+str(iT)+'{2}(Ms=0).')
                    SOC_Order_of_states.append( 'T'+str(iT)+'{3}(Ms=+1)')
                    iT += 1
                energy_and_order.append( row )
                k+=1
            Right_order_of_states = sorted(energy_and_order, key=lambda x: x[0])

        if 'SOC COUPLINGS (OFF DIAGONAL ELEMENT)' in l:
            Right_order_soc = sorted(SOC_Order_of_states)
            ij = 0
            bla = 0
            for i in range(1,nstate*4+1):
                bra = Right_order_soc[i-1]
                for j in range(i+1,nstate*4+1):
                    ket = Right_order_soc[j-i+bla]
                    soc_value_real_1e = float(out[il+1+ij].split()[9])
                    soc_value_imag_1e = float(out[il+1+ij].split()[11])
                    soc_value_real_2e = float(out[il+2+ij].split()[9])
                    soc_value_imag_2e = float(out[il+2+ij].split()[11])
                    soc_sum_real_1e_2e = soc_value_real_1e+soc_value_real_2e
                    soc_sum_imag_1e_2e = soc_value_imag_1e+soc_value_imag_2e
                    soc_value_abs = np.sqrt(soc_sum_real_1e_2e**2+soc_sum_imag_1e_2e**2)
                    soc_value_abs_1e = np.sqrt(soc_value_real_1e**2+soc_value_imag_1e**2)
                    row = (bra, ket, soc_value_real_1e, soc_value_imag_1e,
                                     soc_value_real_2e, soc_value_imag_2e,
                                     soc_sum_real_1e_2e, soc_sum_imag_1e_2e,
                                     soc_value_abs, soc_value_abs_1e)
                    SOC_val.append( row )
                    ij+=2
                bla +=1
            k=0
            while k <= ij*2-1:
                k+=1

        if "THE ROHF/DFT SCF ENERGY IS AT 0 HARTREE" in l:
            k=0
            while k <= nstate*4-1:
                row = (SOC_Order_of_states[k],
                       float(out[il+k+3].split()[1]),
                       float(out[il+k+3].split()[2]))
                soc_energy_and_order.append( row )
                k+=1
            my_o_soc = sorted(soc_energy_and_order, key=lambda x: x[0])

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

def ECP_checking(file):
    global beep, sbkjc, check
    check = 0
    beep = 0
    sbkjc = 0
    f = open(file, 'r')
    filedata = f.readlines()
    f.close()
    for il, l in enumerate(filedata):
        if "SBKJC" in l:
            sbkjc = 1
        if "ECP POTENTIALS" in l:
            check = 1
        if "OPERR" in l:
            operr = filedata[il].split()[2]
            if check==1 and ("2" in operr):
                beep = 1
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

    ECP_checking(file)
    if beep == 1:
        print(' ')
        os.system('echo " Hi" $USER"!"')
        print(' I checked your',file,'file\n')
        print(' You used Effective Core Potential (ECP) BASIS set')
        print(' Since it removes some core electrons, contribution from 2-electrons will be false')
        if sbkjc == 1:
            print(' You must to add OPERAT=HSO1 and ZEFTYP=SBKJC to $TRANST group\n')
        else:
            print(' You must to add OPERAT=HSO1 and ZEFF(1)=... with the effective nuclear charges\n')
        print(' Please, recalculate with the correct input data, and I will give you what you want!\n')
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
    fout.write('State'+' '*7+'Symmetry'+' '*6+'Hartree     eV.exited.rel.ROHF  eV.exited.rel.S0  Oscillator.Strength\n')
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
        wout = state+' '*4\
             + symm+' '*4\
             + str('%10.10f' % E_ev0)+' '*4\
             + str(newline % E_ev1)+' '*10\
             + str(newline % E_ev2)+' '*10\
             + str('%10.4f' % OscStr)
        fout.write(wout+'\n')

    fout.write('\n')
    fout.write('SOC.corrected.ENERGY.Hartree.is.relatively.MRSF.S0:\n')
    fout.write('State'+' '*8+'Hartree.with.SOC  eV.with.SOC.rel.ROHF  eV.with.SOC.rel.S0'+' '*7+'cm_1\n')
    for i in enumerate(soc_energy_and_order):
        E_soc1 = round(GS+(i[1][1])*4.55633e-6,10) # in hartree + GS
        E_soc2 = round((i[1][1])*1.23981e-4,rounding) # in ev
        E_soc0 = round((i[1][1]),4)
        E_scr3 = round((i[1][2])*27.2107,rounding)
        state_in = str(i[1][0])
        state= state_in.replace('{1}','').replace('{2}','').replace('{3}','').replace('(Ms=0).','(Ms=0)')
        state_line = len(state)
        norm1_line = 10
        if state_line<=norm1_line:
            state = state+' '*(norm1_line-state_line)
        wout = state+' '*4\
             + str('%10.10f' % E_soc1)+' '*4\
             + str(newline % E_scr3)+' '*10\
             + str(newline % E_soc2)+' '*10\
             + str('%10.4f' % E_soc0)
        fout.write(wout+'\n')

    fout.write('\n')
    fout.write('Spin.Orbit.Coupling.table.in.cm_1:\n')
    if check == 0:
        fout.write('State'+' '*15+'1e.Real  '+\
                   '1e.Imag  2e.Real  2e.Imag  sum.1e_2e.Real  '+\
                   'sum.1e_2e.Imag  1e_2e.ABS.value\n')
        for i in enumerate(SOC_val):
            soc_states_in = str(i[1][0])+'/'+str(i[1][1])
            if '/S' in soc_states_in:
                continue
            soc_states= soc_states_in.replace('{1}','').replace('{2}','').replace('{3}','').replace('(Ms=0).','(Ms=0)')
            soc_Re1e = str('%7.1f' % i[1][2])+" "
            soc_Im1e = str('%7.1f' % i[1][3])+" "
            soc_Re2e = str('%7.1f' % i[1][4])+" "
            soc_Im2e = str('%7.1f' % i[1][5])+" "
            soc_RI1e = str('%7.1f' % i[1][6])+" "
            soc_RI2e = str('%7.1f' % i[1][7])+" "
            soc_ABS = str('%7.1f' % i[1][8])
            state_line = len(soc_states)
            norm1_line = 20
            if state_line<=norm1_line:
                soc_states = soc_states+' '*(norm1_line-state_line)

            wout = soc_states+soc_Re1e+' '+soc_Im1e+' '+soc_Re2e+' '+soc_Im2e\
                   +' '*4+soc_RI1e+' '*8+soc_RI2e+' '*8+soc_ABS
            fout.write(wout+'\n')

    if check == 1:
        fout.write('State'+' '*15+'1e.Real  1e.Imag  1e.ABS.value\n')
        for i in enumerate(SOC_val):
            soc_states_in = str(i[1][0])+'/'+str(i[1][1])
            if '/S' in soc_states_in:
                continue
            soc_states= soc_states_in.replace('{1}','').replace('{2}','').replace('{3}','').replace('(Ms=0).','(Ms=0)')
            soc_Re1e = str('%7.1f' % i[1][2])+" "
            soc_Im1e = str('%7.1f' % i[1][3])+" "
            soc_ABS = str('%7.1f' % i[1][9])
            state_line = len(soc_states)
            norm1_line = 20
            if state_line<=norm1_line:
                soc_states = soc_states+' '*(norm1_line-state_line)
            wout = soc_states+soc_Re1e+' '+soc_Im1e+' '+soc_ABS
            fout.write(wout+'\n')
    fout.close()

