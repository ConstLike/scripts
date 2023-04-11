#!/usr/bin/env python3.6

# Developed by Konstantin Komarov.

import fileinput
import os
import sys
import numpy as np
import argparse
import csv

def Extract_data(file_name):
    f = open(file_name, 'r', encoding='ISO-8859-1')
    file_data = f.read().splitlines()
    f.close()

    scftype = ''
    dfttype = ''
    tddft_out = ''
    basis_out = ''
    molecule = ''
    number_of_state = 0
    state_energy_eV_GS = 0.0
    state_symmetry = ''
    state_squared_S = 0.0
    state_transition_dipole_x = 0.0
    state_transition_dipole_y = 0.0
    state_transition_dipole_z = 0.0
    state_oscillator_strength = 0.0
    mol_symmetry = ''
    number_of_bf = 0
#   file_name = ''

    summary_table = []

    scftype, tddft, molecule, basis_out, dfttype  = extract_basis(file)

    l_mrsfs = False
    l_mrsft = False
    l_sf = False
    l_tds = False
    l_tdt = False
    if tddft.lower() == 'mrsfs':
        tddft_out = "MRSF_singlet"
        l_mrsfs = True
    elif tddft.lower() == 'mrsft':
        tddft_out = "MRSF_triplet"
        l_mrsft = True
    elif tddft.lower() == 'sf':
        tddft_out = "Spin_Flip"
        l_sf = True
    elif tddft.lower() == 'tddfts':
        tddft_out = "TDDFT_singlet"
        l_tds = True
    elif tddft.lower() == 'tddftt':
        tddft_out = "TDDFT_triplet"
        l_tdt = True

    total_energy_Hartree = 0.0
    state_energy_Hartree = 0.0
    state_location_in_log = []
    range_of_transitions = []
    for il, l in enumerate(file_data):

        if "TDDFT INPUT PARAMETERS" in l:
            nstate = int(file_data[il+2].split()[1])

        if "INPUT CARD> $DATA" in l.lower():
            mol_symmetry = str(file_data[il+2].split()[2])

        if "NUMBER OF CARTESIAN GAUSSIAN BASIS FUNCTIONS" in l:
            number_of_bf = int(file_data[il].split()[7])

        elif "TOTAL NUMBER OF MOS IN VARIATION" in l:
            number_of_bf = int(file_data[il].split()[7])

        if "SUMMARY OF" in l:
            step = 0; mrs = False
            if l_mrsfs or l_mrsft:
                step = il+7; mrs = True
            elif l_sf:
                step = il+6
            elif l_tds or l_tdt:
                step = il+4; mrs = True

            k = 0
            iS = 1
            iStmp = iS
            while k <= nstate:
                if int(file_data[step+k].split()[0]) == 0:
                    total_energy_Hartree = float(file_data[step+k].split()[2])
                    if k==nstate:
                        break
                    else:
                        k+=1
                number_of_state = iStmp
                if number_of_state==1:
                    GS = float(file_data[step+k].split()[2])
                k+=1
                iStmp += 1

            k = 0
            j = 0
            while k <= nstate:
                if int(file_data[step+k].split()[0]) == 0:
                    if k==nstate:
                        break
                    else:
                        k+=1

                number_of_state = iS
                state_symmetry = str(file_data[step+k].split()[1])
                state_energy_Hartree = float(file_data[step+k].split()[2])

                if l_mrsfs or l_mrsft:
                    state_energy_eV_GS = (state_energy_Hartree-GS)*27.2107
                    state_squared_S = float(file_data[step+k].split()[4])
                    state_transition_dipole_x = float(file_data[step+k].split()[5])
                    state_transition_dipole_y = float(file_data[step+k].split()[6])
                    state_transition_dipole_z = float(file_data[step+k].split()[7])
                    state_oscillator_strength = float(file_data[step+k].split()[8])
                elif l_tds or l_tdt:
                    if l_tds: state_squared_S = 0.0
                    if l_tdt: state_squared_S = 2.0
                    state_energy_eV_GS = (state_energy_Hartree-total_energy_Hartree)*27.2107
                    state_transition_dipole_x = float(file_data[step+k].split()[4])
                    state_transition_dipole_y = float(file_data[step+k].split()[5])
                    state_transition_dipole_z = float(file_data[step+k].split()[6])
                    state_oscillator_strength = float(file_data[step+k].split()[7])
                elif l_sf:
                    state_energy_eV_GS = (state_energy_Hartree-GS)*27.2107
                    state_squared_S = float(file_data[step+k].split()[4])
                    state_transition_dipole_x = ''
                    state_transition_dipole_y = ''
                    state_transition_dipole_z = ''
                    state_oscillator_strength = ''

                row = (scftype.upper(),
                       dfttype.upper(),
                       tddft_out,
                       basis_out,
                       molecule,
                       number_of_state,
                       state_energy_eV_GS,
                       state_symmetry,
                       state_squared_S,
                       state_transition_dipole_x,
                       state_transition_dipole_y,
                       state_transition_dipole_z,
                       state_oscillator_strength,
                       number_of_bf,
                       mol_symmetry,
                       file_name,
                       )

                summary_table.append( row )
                iS += 1
                k += 1
                j += 1
    return summary_table

def extract_basis(file):
#    uhf_mrsf_thymine_acct_bhhlyp.log
#    '[0]__[1]___[2]___[3]___[4]__.log

    scftype = str(file.split("_")[0])
    tddft = str(file.split("_")[1])
    molecule = str(file.split("_")[2])
    basis = str(file.split("_")[3])
    dfttype = str(file.split("_")[4].split('.')[0])

    if basis=="631gd":
        basis_out = "6-31G(d)"
    elif basis=="631gss":
        basis_out = "6-31G(d,p)"
    elif basis=="ccd":
        basis_out = "cc-pVDZ"
    elif basis=="cct":
        basis_out = "cc-pVTZ"
    elif basis=="accd":
        basis_out = "aug-cc-pVDZ"
    elif basis=="acct":
        basis_out = "aug-cc-pVTZ"
    return scftype, tddft, molecule, basis_out, dfttype

def Check_file(file):
    f = open(file, 'r', encoding = "ISO-8859-1")
    filedata = f.readlines()
    f.close()
    status = False
    for il, l in enumerate(filedata):
        if "error" in l:
           status = True
           return status
        if "TOO MANY ITERATIONS" in l:
           status = True
           return status
#       if "STATE SYMMETRY LABELS MAY NOT BE CORRECTLY" in l:
#          status = True
#          return status

def command_line_args():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input',
                        type=str,
                        help='Provide the input.log file')
    return parser.parse_args()


if __name__ == '__main__':

    arg = command_line_args()
    files = open(arg.input,"r").read().splitlines()
    output_file = 'x'+arg.input+'.csv'

    print(output_file)

    header = ["scftype",
              "dfttype",
              "tddft",
              "basis",
              "molecule",
              "number_of_state",
              "state_energy_eV_GS",
              "state_symmetry",
              "state_squared_S",
              "state_transition_dipole_x",
              "state_transition_dipole_y",
              "state_transition_dipole_z",
              "state_oscillator_strength",
              "Number_of_bf",
              "Mol_symmetry",
              "Log_file"]

    data = []

    ii = 0
    with open(output_file, 'w', newline='', encoding='ISO-8859-1') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(header)
        for file in files:
            status = Check_file(file)
            if status:
                print(' ERROR in ',file)
            else:
                ii += 1
                print(ii, file)
                summary_rows =  Extract_data(file)
                for j in summary_rows:
                    writer.writerow(j)

