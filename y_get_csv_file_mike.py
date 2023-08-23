#!/usr/bin/env python3.6

# Developed by Konstantin Komarov.

import fileinput
import os
import sys
import numpy as np
import argparse
import csv

def Extract_data(file_name,index):
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
    mrsf_betac = 0.0
    mrsf_hf = 0.0
    mrsf_aee = 0.0
    mrsf_beta = 0.0
    mrsf_spc = 0.0
    number_of_bf = 0
#   file_name = ''

    summary_table = []

    scftype, tddft, molecule, basis_out, dfttype = extract_basis(file)

    l_mrsfs = False
    l_mrsft = False
    l_sf = False
    l_tds = False
    l_tdt = False
    if tddft.lower() == 'mrsfs':
        tddft_out = "MRSF"
        l_mrsfs = True
    if tddft.lower() == 'mrsfs-momoo':
        tddft_out = "MRSF-MOMOO"
        l_mrsfs = True
    if tddft.lower() == 'mrsft-momoo':
        tddft_out = "MRSF-t-MOMOO"
        l_mrsfs = True
    if tddft.lower() == 'mrsfs-aee-momoo':
        tddft_out = "MRSF-MOMOO"
        dfttype = "DTCAM-AEE"
        l_mrsfs = True
    if tddft.lower() == 'mrsfs-vee-momoo':
        tddft_out = "MRSF-MOMOO"
        dfttype = "DTCAM-VEE"
        l_mrsfs = True
    if tddft.lower() == 'mrsfs-mramo':
        tddft_out = "MRSF-AAMO"
        l_mrsfs = True
    if tddft.lower() == 'mrsfs-mrscal':
        tddft_out = "AEE"
        l_mrsfs = True
    if tddft.lower() == 'mrsfs-mrscal-spc':
        tddft_out = "MRSF_singlet_mrscal_spc"
        l_mrsfs = True
    if tddft.lower() == 'mrsfs-mrscal-nospc':
        tddft_out = "MRSF_singlet_mrscal_nospc"
        l_mrsfs = True
    if tddft.lower() == 'mrsfs-spc-cc-vv':
        tddft_out = "MRSF_singlet_spc_cc_vv"
        l_mrsfs = True
    elif tddft.lower() == 'mrsf':
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
    state_transt_dominant = []
    state_transt = []
    nstate = 0
    non_abel = False
    camflag = False
    flagsoc = False
    for il, l in enumerate(file_data):

        if "mrsoc=.t." in l:
            flagsoc = True

        if "TDDFT INPUT PARAMETERS" in l:
            nstate = int(file_data[il+2].split()[1])
            if flagsoc:
                nstate = nstate*2

        if "INPUT CARD> $DATA" in l.lower():
            mol_symmetry = str(file_data[il+2].split()[2])

        if "NUMBER OF CARTESIAN GAUSSIAN BASIS FUNCTIONS" in l:
            number_of_bf = int(file_data[il].split()[7])

        elif "TOTAL NUMBER OF MOS IN VARIATION" in l:
            number_of_bf = int(file_data[il].split()[7])

        elif "SOME STATE SYMMETRY LABELS MAY NOT BE CORRECTLY PRINTED BELOW" in l:
            non_abel = True
        if "CAM-MRSF" in l:
            camflag = True

        states = range(1,nstate+1)
        for i in states:
            length = 4
            step = int(length-len(str(i)))
            if "STATE #"+' '*step+str(i)+"  ENERGY" in l:
                state_location_in_log.append(int(il))

#        if l_mrsfs or l_mrsft:
#            if "SPIN-PAIRING COUPLINGS" in l:
#                mrsf_hf = float(file_data[il+2].split()[0])
#                mrsf_aee = float(file_data[il+2].split()[1])
#                mrsf_spc = float(file_data[il+2].split()[2])

        if l_mrsfs or l_mrsft:
            if "FITTING PARAMETERS OF MRSF RESPONSE CALCULATION" in l:
                if camflag:
                    mrsf_aee = float(file_data[il+2].split()[1])
                    mrsf_beta = float(file_data[il+2].split()[2])
                    mrsf_hf = float(file_data[il+8].split()[1])
                    mrsf_betac = float(file_data[il+8].split()[2])
                    mrsf_spc = float(file_data[il+5].split()[2])
                else:
                    mrsf_aee = float(file_data[il+2].split()[0])
                    mrsf_spc = float(file_data[il+5].split()[2])
                    mrsf_hf = float(file_data[il+8].split()[0])

        if "SUMMARY OF" in l:
            step = 0; mrs = False
            if l_mrsfs or l_mrsft:
                for i in [*range(nstate-1)]:
                    step = state_location_in_log[i+1]-state_location_in_log[i]-6
                    range_of_transitions.append(int(step))
                if non_abel:
                    range_of_transitions.append(int(il-state_location_in_log[nstate-1]-11))
                else:
                    range_of_transitions.append(int(il-state_location_in_log[nstate-1]-7))
                for i in [*range(nstate)]:
                    tmp = []
                    for j in [*range(range_of_transitions[i])]:
                        state_excite_Occ = int(file_data[state_location_in_log[i]+j+5].split()[2])
                        state_excited_Vir = int(file_data[state_location_in_log[i]+j+5].split()[4])
                        state_excite_Coeff = float(file_data[state_location_in_log[i]+j+5].split()[1])
                        row = (state_excite_Occ,state_excited_Vir,state_excite_Coeff)
                        tmp.append(row)
                    tmp = sorted(tmp, key=lambda term: (abs(term[2]), term[2]), reverse=True)
                    state_transt.append(tmp)
                    state_transt_dominant.append(tmp[0])
                step = il+7; mrs = True
            elif l_sf:
                for i in [*range(nstate-1)]:
                    step = state_location_in_log[i+1]-state_location_in_log[i]-6
                    range_of_transitions.append(int(step))
                if non_abel:
                    range_of_transitions.append(int(il-state_location_in_log[nstate-1]-11))
                else:
                    range_of_transitions.append(int(il-state_location_in_log[nstate-1]-7))
                for i in [*range(nstate)]:
                    tmp = []
                    for j in [*range(range_of_transitions[i])]:
                        state_excite_Occ = int(file_data[state_location_in_log[i]+j+5].split()[2])
                        state_excited_Vir = int(file_data[state_location_in_log[i]+j+5].split()[4])
                        state_excite_Coeff = float(file_data[state_location_in_log[i]+j+5].split()[1])
                        row = (state_excite_Occ,state_excited_Vir,state_excite_Coeff)
                        tmp.append(row)
                    tmp = sorted(tmp, key=lambda term: (abs(term[2]), term[2]), reverse=True)
                    state_transt.append(tmp)
                    state_transt_dominant.append(tmp[0])
                step = il+6
            elif l_tds or l_tdt:
                for i in [*range(nstate)]:
                    tmp = 0
                    state_transt.append(tmp)
                    state_transt_dominant.append(tmp)
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

                if l_mrsfs or l_mrsft:
                    state_symmetry = str(file_data[step+k].split()[1])
                    state_energy_Hartree = float(file_data[step+k].split()[2])
                    state_energy_eV_GS = (state_energy_Hartree-GS)*27.2107
                    state_squared_S = float(file_data[step+k].split()[4])
                    state_transition_dipole_x = float(file_data[step+k].split()[5])
                    state_transition_dipole_y = float(file_data[step+k].split()[6])
                    state_transition_dipole_z = float(file_data[step+k].split()[7])
                    state_oscillator_strength = float(file_data[step+k].split()[8])
                elif l_tds or l_tdt:
                    if l_tds: state_squared_S = 0.0
                    if l_tdt: state_squared_S = 2.0
                    kk = k-1
                    state_symmetry = str(file_data[step+kk].split()[1])
                    state_energy_Hartree = float(file_data[step+kk].split()[2])
                    state_energy_eV_GS = (state_energy_Hartree-total_energy_Hartree)*27.2107
                    if int(file_data[step+kk].split()[0]) == 0:
                        state_transition_dipole_x = 0.0
                        state_transition_dipole_y = 0.0
                        state_transition_dipole_z = 0.0
                        state_oscillator_strength = 0.0
                    else:
                        state_transition_dipole_x = float(file_data[step+kk].split()[4])
                        state_transition_dipole_y = float(file_data[step+kk].split()[5])
                        state_transition_dipole_z = float(file_data[step+kk].split()[6])
                        state_oscillator_strength = float(file_data[step+kk].split()[7])
                elif l_sf:
                    state_symmetry = str(file_data[step+k].split()[1])
                    state_energy_Hartree = float(file_data[step+k].split()[2])
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
                       state_energy_Hartree,
                       state_symmetry,
                       str(state_transt_dominant[j]),
                       state_squared_S,
                       str(state_transt[j]),
                       state_transition_dipole_x,
                       state_transition_dipole_y,
                       state_transition_dipole_z,
                       state_oscillator_strength,
                       number_of_bf,
                       mol_symmetry,
                       total_energy_Hartree,
                       index,
                       mrsf_hf,
                       mrsf_betac,
                       mrsf_aee,
                       mrsf_beta,
                       mrsf_spc,
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
    point = file.split("_")[4].count(".")
    if point == 0:
        dfttype = str(file.split("_")[4])
    else:
        dfttype = str(file.split("_")[4].split('.')[0])

    if basis=="631gd":
        basis_out = "6-31G(d)"
    elif basis=="631g":
        basis_out = "6-31G"
    elif basis=="631gss":
        basis_out = "6-31G(d,p)"
    elif basis=="631gdp":
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
              "state_energy_Hartree",
              "state_symmetry",
              "state_dominant_trans",
              "state_squared_S",
              "state_transition",
              "state_transition_dipole_x",
              "state_transition_dipole_y",
              "state_transition_dipole_z",
              "state_oscillator_strength",
              "Number_of_bf",
              "Mol_symmetry",
              "total_energy_Hartree",
              "log_index",
              "mrsf_hf",
              "mrsf_betac",
              "mrsf_aee",
              "mrsf_beta",
              "mrsf_spc",
              "Log_file"]

    data = []

    ii = 0
    with open(output_file, 'w', newline='', encoding='ISO-8859-1') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(header)
        index = 0
        for file in files:
            status = Check_file(file)
            if status:
                print(' ERROR in ',file)
            else:
                ii += 1
                print(ii, file)
                index+=1
                summary_rows =  Extract_data(file,index)
                for j in summary_rows:
                    writer.writerow(j)

