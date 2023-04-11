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
            energy = np.zeros(n_bf)
        if "NUMBER OF ELECTRONS" in l:
            n_homo=int(file_data[il].split()[4])/2-1

        if "EIGENVECTORS" in l:
            shift_Ca = 6 # see log file
            shift_energy = 4 # see log file
            matrix_range = []
            for i in range(n_bf//5):
                matrix_range.append(5)
            matrix_range.append(n_bf%5)
            imain = 0
            for isection in range(np.size(matrix_range)):
                section_line_Ca = il+shift_Ca+isection*(n_bf+shift_Ca-2) # Ca start line of section in log file
                section_line_E = il+shift_energy+isection*(n_bf+shift_Ca-2) # Energy start line of section in log file
                for icolumn in range(matrix_range[isection]):
                    energy[imain] = file_data[section_line_E].split()[icolumn]
                    iline = 0
                    while iline < n_bf:
                        Ca[iline][imain] = file_data[iline+section_line_Ca].split()[icolumn+4] # 4 is a shift, see log file
                        iline+=1
                    imain += 1

    return Ca, energy, n_homo

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

    n_orb = 48

    for i in range(np.size(files)-1):
        file_a = files[i]+".log"
        file_b = files[i+1]+".log"
        print('A:',file_a)
        print('B:',file_b)
        print('   A <- B    A, eV     B, eV  Max Overlap')
        c_a, energy_a, n_homo = Extract_data(file_a)
        c_b, energy_b, n_homo = Extract_data(file_b)
        energy_a*= 27.2114 # Hartree to Ev.
        energy_b*= 27.2114
        overlap = get_overlap(c_a, c_b)

#       print_overlap(c_a, c_b)

        n_bf = np.size(overlap,1)
        pr = np.zeros(n_bf, dtype=bool)
        locs = np.zeros(n_bf, dtype=int)
        abs_overlap = abs(overlap)
        for i, val in enumerate(abs_overlap):
            maxval = np.amax(val)
            maxloc = val.argmax()

            pr[maxloc] = True
            locs[i] = maxloc

            print('%4i' % (i+1),
                  '%4i' %  (maxloc+1),
                  '%9.3f' % energy_a[i],
                  '%9.3f' % energy_b[i],
                  '%6.3f' % maxval,
                  end='')
            if (i == n_homo):
                print(" homo", end='')
            if (i == n_homo+1):
                print(" lumo", end='')
            if ((i != maxloc) and (maxval < 0.9)):
                print(" rearranged, WARNING", end='')
            elif ((i == maxloc) and (maxval < 0.9)):
                print(" WARNING", end='')
            elif ((i !=maxloc) and (maxval >= 0.9)):
                print(" rearranged", end='')
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
