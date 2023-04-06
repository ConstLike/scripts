#!/usr/bin/env python3.6

# Developed by Konstantin Komarov.

import fileinput
import os
import sys
import numpy as np
import argparse
import csv

def Extract_data(file_name):
    f = open(file_name, 'r')
    file_data = f.read().splitlines()
    f.close()

    tddft, scftype, molecule, basis, dfttype_inp, ref_S1_energy, ref_S2_energy, option = extract_basis(file)

    l_mrsf = False
    l_sf = False
    l_td = False
    if tddft.lower() == 'mrsf':
        l_mrsf = True
    elif tddft.lower() == 'sf':
        l_sf = True
    elif tddft.lower() == 'td':
        l_td = True

    scftype = ""
    dfttype = ""
#   tddft = ''
#   basis = ''
#   molecule = ''
    state_spin_type = ""
    number_of_states = 0
    total_energy_Hartree = 0.0
    state_energy_Hartree = 0.0
    state_energy_eV_GS = 0.0
#   ref_S1_energy = 0.0
#   ref_S2_energy = 0.0
    spcp_HFscal = 0.0
    spcp_MRSFscal = 0.0
    spcp_CC = 0.0
    spcp_VV = 0.0
    spcp_CV = 0.0
    state_symmetry = ""
    mol_symmetry = ""
    nstate = 0
    number_of_atom = 0
    number_of_bf = 0
    coord_system = ""
    state_energy_eV_ref = 0.0
    state_squared_S = 0.0
    state_transition_dipole_x = 0.0
    state_transition_dipole_y = 0.0
    state_transition_dipole_z = 0.0
    state_oscillator_strength = 0.0
    state_transt_dominant = []
    state_transt = []

    state_location_in_log = []
    range_of_transitions = []
    summary_table = []

    for il, l in enumerate(file_data):

        if "$CONTRL OPTIONS" in l:
            scftype = str(file_data[il+2].split()[0].split('=')[1])
            dfttype = str(file_data[il+4].split()[0].split('=')[1])
            if dfttype=='USELIBXC':
                dfttype = dfttype_inp
            spher_coord = int(file_data[il+7].split()[1])
            if spher_coord==1:
                coord_system = "Spherical"
            else:
                coord_system = "Cartesian"


        if "TDDFT INPUT PARAMETERS" in l:
            nstate = int(file_data[il+2].split()[1])

        if l_mrsf:
            if "SPIN-PAIRING COUPLINGS" in l:
                spcp_HFscal = float(file_data[il+2].split()[0])
                spcp_MRSFscal = float(file_data[il+2].split()[1])
                spcp_CC = float(file_data[il+2].split()[2])
                spcp_VV = float(file_data[il+2].split()[3])
                spcp_CV = float(file_data[il+2].split()[4])
        if "input card> $data" in l.lower():
            mol_symmetry = str(file_data[il+2].split()[2])

        if "NUMBER OF CARTESIAN GAUSSIAN BASIS FUNCTIONS" in l:
            number_of_bf = int(file_data[il].split()[7])
        elif "TOTAL NUMBER OF MOS IN VARIATION" in l:
            number_of_bf = int(file_data[il].split()[7])

        if "TOTAL NUMBER OF ATOMS" in l:
            number_of_atom = int(file_data[il].split()[5])

        states = range(1,nstate+1)
        for i in states:
            length = 4
            step = int(length-len(str(i)))
            if "STATE #"+' '*step+str(i)+"  ENERGY" in l:
                state_location_in_log.append(int(il))

        if "SUMMARY OF" in l:
            for i in [*range(nstate-1)]:
                step = state_location_in_log[i+1]-state_location_in_log[i]-6
                range_of_transitions.append(int(step))
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

            if l_mrsf:
                step = il+7

                check_line = int(file_data[step].split()[0])
                add_to_step = 0
                if check_line==0:
                    add_to_step = 1
                S2_line = float(file_data[step+add_to_step].split()[4])

                if S2_line==0.0:
                    state_spin_type = 'Singlet'
                if S2_line==2.0:
                    state_spin_type = 'Triplet'
                if S2_line==6.0:
                    state_spin_type = 'Quintet'
            else:
                step = il+6
                state_spin_type = 'Spin-Contamination'

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
                number_of_states = iStmp
                if number_of_states==1:
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

                number_of_states = iS
                state_symmetry = str(file_data[step+k].split()[1])
                state_energy_Hartree = float(file_data[step+k].split()[2])

                state_energy_eV_ref = (state_energy_Hartree-total_energy_Hartree)*27.2107
                state_energy_eV_GS = (state_energy_Hartree-GS)*27.2107
                state_squared_S = float(file_data[step+k].split()[4])
                if l_mrsf:
                    state_transition_dipole_x = float(file_data[step+k].split()[5])
                    state_transition_dipole_y = float(file_data[step+k].split()[6])
                    state_transition_dipole_z = float(file_data[step+k].split()[7])
                    state_oscillator_strength = float(file_data[step+k].split()[8])
                else:
                    state_transition_dipole_x = ''
                    state_transition_dipole_y = ''
                    state_transition_dipole_z = ''
                    state_oscillator_strength = ''

                row = (scftype,
                       dfttype,
                       option,
                       tddft.upper(),
                       basis,
                       molecule,
                       state_spin_type,
                       number_of_states,
                       state_energy_Hartree,
                       state_energy_eV_GS,
                       ref_S1_energy,
                       ref_S2_energy,
                       spcp_HFscal,
                       spcp_MRSFscal,
                       spcp_CC,
                       spcp_VV,
                       spcp_CV,
                       state_symmetry,
                       mol_symmetry,
                       nstate,
                       number_of_atom,
                       number_of_bf,
                       coord_system,
                       total_energy_Hartree,
                       state_energy_eV_ref,
                       state_squared_S,
                       state_transition_dipole_x,
                       state_transition_dipole_y,
                       state_transition_dipole_z,
                       state_oscillator_strength,
                       str("\""+str(state_transt_dominant[j])+"\""),
                       str("\""+str(state_transt[j])+"\""),
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
    num_opt = np.size( file.split("_"))
    option = ""
    if num_opt==5:
        dfttype = str(file.split("_")[4].split(".")[0]).upper()
        option = "mr_default"
    elif num_opt==7:
        dfttype = str(file.split("_")[4]).upper()
        option = "mr_mrscal"
    elif num_opt==9:
        dfttype = str(file.split("_")[4]).upper()
        option = "mr_mrscal_spc"

    ref_mol = [['acetamide',         5.8,7.27],
               ['acetone',           4.4,9.4],
               ['adenine',           5.12,5.25],
               ['benzoquinone',      2.8,2.78],
               ['butadiene',         6.18,6.55],
               ['cyclopentadiene',   5.55,6.31],
               ['cyclopropene',      6.76,7.06],
               ['cytosine',          4.87,4.66],
               ['ethene',            7.8, 8.5],
               ['formaldehyde',      3.88,9.1],
               ['formamide',         5.63,7.44],
               ['furan',             6.57,6.32],
               ['hexatriene',        5.10,5.09],
               ['imidazole',         6.81,6.19],
               ['naphthalene',       4.24,4.77],
               ['norbornadiene',     5.34,6.11],
               ['octatetraene',      4.47,4.66],
               ['propanamide',       5.72,7.20],
               ['pyrazine',          4.64,4,81],
               ['pyridazine',        3.78,4.32],
               ['pyridine',          4.59,4.85],
               ['pyrimidine',        4.55,4.91],
               ['pyrrole',           6.37,6.57],
               ['tetrazine',         2.24,3.48],
               ['thymine',           4.82,5.20],
               ['uracil',            4.8,5.35]]



    ref_S1_energy = 0.0
    for i in ref_mol:
        if i[0]==molecule:
            ref_S1_energy = i[1]
            ref_S2_energy = i[2]

    return tddft, scftype, molecule, basis, dfttype, ref_S1_energy, ref_S2_energy, option

def Check_file(file):
    f = open(file, 'r')
    filedata = f.readlines()
    f.close()
    status = False
    for il, l in enumerate(filedata):
        if "error" in l:
           status = True
        if "TOO MANY ITERATIONS" in l:
           status = True
    return status

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
              "MR_option",
              "tddft",
              "Basis",
              "Molecule",
              "State_spin_type",
              "Number_of_states",
              "State_energy_Hartree",
              "State_energy_eV_GS",
              'Ref_S1_mol',
              'Ref_S2_mol',
              "spcp_HFscal",
              "spcp_MRSFscal",
              "spcp_CC",
              "spcp_VV",
              "spcp_CV",
              "State_symmetry",
              "Mol_symmetry",
              "nstate",
              "Number_of_atom",
              "Number_of_bf",
              "Coord_system",
              "Total_energy_Hartree",
              "State_energy_eV_ref",
              "State_squared_S",
              "State_transition_dipole_x",
              "State_transition_dipole_y",
              "State_transition_dipole_z",
              "State_oscillator_strength",
              "State_Excitation_Dominant_Occ_Vir_Coef",
              "State_Excitation_All_Occ_Vir_Coef",
              "Log_file_name"]

    data = []

    with open(output_file, 'w', newline='', encoding='UTF8') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(header)
        for file in files:
            print(file)
            status = Check_file(file)
            if status:
                print(' ERROR in ',file)
            else:
                summary_rows =  Extract_data(file)
                for j in summary_rows:
                    writer.writerow(j)

