#!/usr/bin/env python3.6

# Developed by Konstantin Komarov.

import fileinput
import os
import sys
import scipy
from scipy.linalg import blas
from numpy import linalg
import numpy as np
import argparse
import csv

def Extract_data(file_name):
    f = open(file_name, 'r')
    file_data = f.readlines()
    f.close()

    Ca, energy = [], []
    n_bf = 0
    for il, l in enumerate(file_data):
        if "NUMBER OF CARTESIAN GAUSSIAN BASIS FUNCTIONS" in l:
            n_bf=int(file_data[il].split()[7])
            Ca = np.zeros((n_bf,n_bf))
            Cb = np.zeros((n_bf,n_bf))
            energy_a = np.zeros(n_bf)
            energy_b = np.zeros(n_bf)
        if "NUMBER OF ELECTRONS" in l:
            n_homo=int(file_data[il].split()[4])/2-1

        if "- ALPHA SET" in l:
            shift_Ca = 9 # see log file
            shift_energy_a = 7 # see log file
            matrix_range = []
            for i in range(n_bf//5):
                matrix_range.append(5)
            matrix_range.append(n_bf%5)
            imain = 0
            for isection in range(np.size(matrix_range)):
                section_line_Ca = il+shift_Ca+isection*(n_bf+shift_Ca-5) # Ca start line of section in log file
                section_line_Ea = il+shift_energy_a+isection*(n_bf+shift_Ca-5) # Energy start line of section in log file
                for icolumn in range(matrix_range[isection]):
                    energy_a[imain] = file_data[section_line_Ea].split()[icolumn]
                    iline = 0
                    while iline < n_bf:
                        Ca[iline][imain] = file_data[iline+section_line_Ca].split()[icolumn+4] # 4 is a shift, see log file
                        iline+=1
                    imain += 1
        if "- BETA SET" in l:
            shift_Cb = 9 # see log file
            shift_energy_b = 7 # see log file
            matrix_range = []
            for i in range(n_bf//5):
                matrix_range.append(5)
            matrix_range.append(n_bf%5)
            imain = 0
            for isection in range(np.size(matrix_range)):
                section_line_Cb = il+shift_Cb+isection*(n_bf+shift_Cb-5) # Ca start line of section in log file
                section_line_Eb = il+shift_energy_b+isection*(n_bf+shift_Cb-5) # Energy start line of section in log file
                print(file_data[section_line_Cb])
                print(file_data[section_line_Eb])
                for icolumn in range(matrix_range[isection]):
                    energy_b[imain] = file_data[section_line_Eb].split()[icolumn]
                    iline = 0
                    while iline < n_bf:
                        Cb[iline][imain] = file_data[iline+section_line_Cb].split()[icolumn+4] # 4 is a shift, see log file
                        iline+=1
                    imain += 1

    return Ca, Cb, energy_a, energy_b, n_homo

def get_overlap(C_a, C_b):
        Ca = C_a.T
        for i, c in enumerate(Ca):
            Ca[i] /= np.sqrt(np.dot(Ca[i], Ca[i]))
        Cb = C_b.T
        for i, c in enumerate(Cb):
            Cb[i] /= np.sqrt(np.dot(Cb[i], Cb[i]))

        overlap = Cb @ Ca.T
        return overlap

def command_line_args():

    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input',
                        type=str,
                        help='Provide the list of input.log files')
    return parser.parse_args()

if __name__ == '__main__':

    arg = command_line_args()
    files = open(arg.input,"r").read().splitlines()

    n_orb = 1000

    for i in range(np.size(files)-1):
        file_a = files[i]
        file_b = files[i+1]
        print('A:',file_a)
        print('B:',file_b)
        print('   A <- B    A, eV     B, eV  Max Overlap')
        c_a1, c_b1, energy_a1, energy_b1, n_homo = Extract_data(file_a)
        c_a2, c_b2, energy_a2, energy_b2, n_homo = Extract_data(file_b)
        energy_a1*= 27.2114 # Hartree to Ev.
        energy_b1*= 27.2114
        energy_a2*= 27.2114 # Hartree to Ev.
        energy_b2*= 27.2114
        overlap_beta_alpha1 = get_overlap(c_a1, c_b1)
        overlap_beta_alpha2 = get_overlap(c_a2, c_b2)
        overlap12 = get_overlap(c_a1, c_a2)


#       print_overlap(c_a, c_b)

        n_bf = np.size(overlap12,1)
        pr = np.zeros(n_bf, dtype=bool)
        pr1 = np.zeros(n_bf, dtype=bool)
        pr2 = np.zeros(n_bf, dtype=bool)
        locs = np.zeros(n_bf, dtype=int)
        locs1 = np.zeros(n_bf, dtype=int)
        locs2 = np.zeros(n_bf, dtype=int)
        vals1 = np.zeros(n_bf, dtype=float)
        vals2 = np.zeros(n_bf, dtype=float)
        abs_overlap12 = abs(overlap12)
        abs_overlap_beta_alpha1 = abs(overlap_beta_alpha1)
        abs_overlap_beta_alpha2 = abs(overlap_beta_alpha2)
        for i, val in enumerate(abs_overlap_beta_alpha1):
            maxval1 = np.amax(val)
            maxloc1 = val.argmax()

            pr1[maxloc1] = True
            locs1[i] = maxloc1
            vals1[i] = maxval1
        for i, val in enumerate(abs_overlap_beta_alpha2):
            maxval2 = np.amax(val)
            maxloc2 = val.argmax()

            pr2[maxloc2] = True
            locs2[i] = maxloc2
            vals2[i] = maxval2
        for i, val in enumerate(abs_overlap12):
            maxval = np.amax(val)
            maxloc = val.argmax()

            pr[maxloc] = True
            locs[i] = maxloc

            print('%6.3f' % vals1[i],
                  '%4i' %  (locs1[i]+1),
                  '%4i' % (i+1),
                  '%9.2f' % energy_b1[i],
                  '%9.2f' % energy_a1[i],
                  '%4i' % (i+1),
                  '%9.5f' % maxval,
                  '%4i' % (maxloc+1),
                  '%9.2f' % energy_a2[i],
                  '%9.2f' % energy_b2[i],
                  '%4i' % (i+1),
                  '%4i' %  (locs2[i]+1),
                  '%6.3f' % vals2[i],
                  end='')
            if (i == n_homo):
                print(" homo", end='')
            if (i == n_homo+1):
                print(" lumo", end='')

            case1 = (i != maxloc) and (maxval < 0.9)
            pr1 = " rearr B->A, WARN"
            case2 = (i == maxloc) and (maxval < 0.9)
            case3 = (i != maxloc) and (maxval >= 0.9)

            case1a = (i != locs1[i]) and (vals1[i] < 0.9)
            case2a = (i == locs1[i]) and (vals1[i] < 0.9)
            case3a = (i != locs1[i]) and (vals1[i] >= 0.9)

            case1b = (i != locs2[i]) and (vals2[i] < 0.9)
            case2b = (i == locs2[i]) and (vals2[i] < 0.9)
            case3b = (i != locs2[i]) and (vals2[i] >= 0.9)

            if case1:
                print(" rearr B->A, WARN", end='')
            elif case2:
                print(" WARN", end='')
            elif case3:
                print(" rearr B->A", end='')
            elif case1a:
                print(" rearr in A, WARN", end='')
            elif case2a:
                print(" WARN", end='')
            elif case3a:
                print(" rearr in A", end='')
            elif case1b:
                print(" rearr in B, WARN", end='')
            elif case2b:
                print(" WARN", end='')
            elif case3b:
                print(" rearr in B", end='')

            print(end='\n')

            if i == n_orb:
                break

        if (not pr.all()):
            print('\n', "Warning", end='\n')
            print(" Some orbitals are missing in reordering", end='\n')
            print(" Their indices are:", end='')
            for i in range(n_bf):
                if (not pr[i]):
                    print(" "+str(i+1)+",", end='')
                if i == n_orb:
                    break
            print(end='\n')
        print(end='\n')
        if False:
            print('\n',"Orbitals rearrange recommendation", end='\n')
            print(" $scf rstrct=.t. $end", end='\n')
            print(" $guess guess=moread norb=",n_bf,"norder=1", end='\n')
            print(" iorder(1)=",end='')
            for i in range(n_bf):
                if i < n_bf-1:
                    print(" "+str(locs[i]+1)+",", end='')
                    if ((i+1) % 10 == 0):
                        print(end='\n')
                else:
                    print(" "+str(locs[i]+1), end='')
                    if ((i+1) % 10 == 0):
                        print(end='\n')
            print(" $end", end='\n')
