#!/usr/bin/env python3.6

# Developed by Konstantin Komarov.

import re
import numpy as np
import argparse

def parse(dat):

    data = dat

    info_sections = data.split('$UMSTEP')
    info_data = {}

    for section in info_sections:

        step_match = re.search(r'=\s+(\d+)', section)
#       if not step_match:
#           continue
        step_number = int(step_match.group(1))

        info = parse_blocks_wrf(section)

        info_data[step_number] = info

    return info_data

def parse_blocks_wrf(dat):
    info = {}
    data = dat

    if '$VEC' in data:

        block = data.split('$VEC\n')[1].split('$END\n')[0]
        lines = block.split('\n')

        orbitals = []
        energies = []

        pattern = re.compile(r'[-+]?\d+\.\d*(?:E[-+]?\d+)?|\d+')

        for line in lines:
            parts = pattern.findall(line)

            if not parts: # skip if line empty. sometime need
                continue

            # Reminder about GAMESS
            # Orbital starts from two integer, but energy starts from float point value.
            if parts[0].isdigit() and parts[1].isdigit():
                orbital_parts = [float(i) for i in parts[2:]]
                if len(orbitals) > int(parts[0]) - 1:
                    orbitals[int(parts[0]) - 1].extend(orbital_parts)
                else:
                    orbitals.append(orbital_parts)
            else:
                energies.extend([float(i) for i in parts])

        info['MO_orbitals'] = orbitals
        info['MO_energies'] = energies

    if '$DATA' in data:

        block = data.split('$DATA\n')[1].split('$END\n')[0]
        lines = block.split('\n')

        geometry = []

#       pattern = re.compile(r'[-+]?\d*\.\d+|\d+')            # get with atomic number as float point
        pattern = re.compile(r'[A-Za-z]+|[-+]?\d*\.\d+|\d+')  # get as previous and also symbol of element.

        for line in lines:

            parts = pattern.findall(line)
            print(parts)

            if not parts:
                continue

#           parts[1] = int(float(parts[1]))
            parts[1] = float(parts[1])
            parts[2] = float(parts[2])
            parts[3] = float(parts[3])
            parts[4] = float(parts[4])

            geometry.append(parts)

        info['Geometry'] = geometry

    if '$XVEC' in data:

        block = data.split('$XVEC\n')[1].split('$END\n')[0]
        lines = block.strip().split('\n')

        excited_state_vector = []
        state_info_list = []

        state_pattern = re.compile(r'STATE #\s+(\d+)\s+ENERGY =\s+([-+]?\d+\.\d*(?:E[-+]?\d+)?)')
        vector_pattern = re.compile(r'[-+]?\d+\.\d*(?:E[-+]?\d+)?')

        for line in lines:
            state_match = state_pattern.search(line)
            if state_match:
                if excited_state_vector:  # save previous state's vector before starting a new one
                    state_info_list[-1]['excited_state_vector'] = excited_state_vector
                    excited_state_vector = []
                state_number = int(state_match.group(1))
                state_energy = float(state_match.group(2))
                state_info_list.append({'excited_state_num': state_number, 'excited_state_energy': state_energy})
            else:
                vector_parts = vector_pattern.findall(line)
                excited_state_vector.extend([float(i) for i in vector_parts])

            if excited_state_vector:  # save last state's vector
                state_info_list[-1]['excited_state_vector'] = excited_state_vector

        info['Xvector'] = state_info_list

    if '$GRAD' in data:
        block = data.split('$GRAD  \n')[1].split('$END\n')[0]
        lines = block.split('\n')

        gradient = []

        pattern = re.compile(r'[A-Za-z]+|[-+]?\d*\.\d+|\d+')

        for line in lines:
            parts = pattern.findall(line)

            if not parts:
                continue

            parts[1] = float(parts[1])
            parts[2] = float(parts[2])
            parts[3] = float(parts[3])

            gradient.append(parts)

        info['Gradient'] = gradient

    if '$NACT' in data:
        block = data.split('$NACT\n')[1].split('$END\n')[0]
        lines = block.split('\n')

        nact = []

        pattern = re.compile(r'[-+]?\d*\.\d+|\d+')

        for line in lines:
            parts = pattern.findall(line)

            if not parts:
                continue

            parts[0] = int(parts[0])
            parts[1] = float(parts[1])
            parts[2] = float(parts[2])
            parts[3] = float(parts[3])

            nact.append(parts)

        info['NACT'] = nact

    if 'TOTAL ENERGY' in data:

        pattern = re.compile(r"TOTAL ENERGY\s*=\s*(-?\d+\.\d+)")
        match = pattern.search(data)

        if match:
            print("Match found:", match.group(1))
            info['Total_energy'] = float(match.group(1))


    return info

def command_line_args():

    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input',
                        type=str,
                        help='Provide the list of files')
    return parser.parse_args()

def main():

    arg = command_line_args()
    fls = arg.input

    files = open(fls,"r").read().splitlines()

    for file in files:

        file_dat = file+"."+arg.extension
        dat = open(file_dat,'r').read()
        info = parse_blocks_wrf(dat)

#       matrix1 = np.array(info[0]['MO_orbitals'])
#       matrix2 = np.array(info[1]['MO_orbitals'])
#       matrix = matrix1-matrix2
#       print(matrix)

        #state=1
        #mat1 = np.array(info[0]['Xvector'][state]['excited_state_vector'])
        #mat2 = np.array(info[1]['Xvector'][state]['excited_state_vector'])
#   print(mat1-mat2)

def from_jin_geo_files_to_my():

    arg = command_line_args()

    files = open(arg.input,"r").read().splitlines()

    j = 0
    with open("y_new_filelist", 'w') as finp:

        for  file in files:
            j += 1

            data = open(file,'r').read()
            if '$DATA' in data:
                block = data.split('$DATA\n')[1].split('$END\n')[0]

            block_data = []
            block_data.append(" $data\n")
            for i in block:
                block_data.append(i)
            block_data.append(" $end")

            inp = open('/bighome/k.komarov/scripts/inp_folder/gms_namd-soc.inc','r').read().splitlines()

            fname = f"rohf_mrsf-soc-namd_631gd_bhhlyp_traj{j:03}a.inp"

            with open(fname, 'w') as fout:
                for i in inp:
                    fout.write(i+"\n")
                for i in block_data:
                    fout.write(i)

            sub = "gms_sbatch2 -i fname -p \"r630,ryzn\" -s \`pwd\` -v namd\n"
            finp.write(sub)

def next_letter(name):

    pattern = r"([a-zA-Z]+)(\d+)([a-zA-Z]+)"

    letter = re.match(pattern,name.split('.')[0].split('_')[4])[3]
    if letter.isalpha():
        if letter == 'z':
            return 'a'
        elif letter == 'Z':
            return 'A'
        else:
            return chr(ord(letter) + 1)
    else:
        raise ValueError("Input is not an alphabetical character")

def resubmit_namd():

    arg = command_line_args()

    files = open(arg.input,"r").read().splitlines()

    j = 0
    with open("y_new_filelist", 'w') as finp:

        for f in files:

            letter = next_letter(f)

            file = f.split('.')[0]+".ndrst"

            j += 1

            data = open(file,'r').read()

            block_data = []


            if '$TDDFT' in data:
                block = data.split('$TDDFT\n')[1].split(' $END\n')[0]
            block_data.append(" $tddft\n")
            for i in block:
                block_data.append(i)
            block_data.append(" $end\n")

            if '$MD GROUP' in data:
                block = data.split('$MD GROUP -----\n')[1].split(' $END\n')[0]
            for i in block:
                block_data.append(i)
            block_data.append(" $end\n")

            if '$DATA' in data:
                block = data.split('$DATA GROUP -----\n')[1].split(' $EFRAG\n')[0]

            block_data.append(" $data\n\nC1\n")
            for i in block:
                block_data.append(i)
            block_data.append(" $end\n")

            if '$TDC' in data:
                block = data.split('$TDC   \n')[1].split(' $END   \n')[0]
            block_data.append(" $TDC   \n")
            for i in block:
                block_data.append(i)
            block_data.append(" $END   \n")

            if '$RND' in data:
                block = data.split('$RND   \n')[1].split(' $END   \n')[0]
            block_data.append(" $RND   \n")
            for i in block:
                block_data.append(i)
            block_data.append(" $END   \n")

            if '$CDO' in data:
                block = data.split('$CDO   \n')[1].split(' $END   \n')[0]
            block_data.append(" $CDO   \n")
            for i in block:
                block_data.append(i)
            block_data.append(" $END   ")


            inp = open('/bighome/k.komarov/scripts/inp_folder/gms_namd-soc-re.inc','r').readlines()

            fname = f"rohf_mrsf-soc-namd_631gd_bhhlyp_traj{j:03}{letter}.inp"
            print(fname)

            with open(fname, 'w') as fout:
                for i in inp:
                    fout.write(i)
                for i in block_data:
                    fout.write(i)

            sub = f"gms_sbatch2 -i {fname} -p \"r630,r631,ryzn\" -n28  -s `pwd` -v namd -N1 -c1 --exclusive\n"
            finp.write(sub)

if __name__ == "__main__":
#   from_jin_geo_files_to_my()
    resubmit_namd()
#   main()

