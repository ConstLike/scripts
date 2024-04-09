import re
import numpy as np

def parse(dat):

    data = dat

    info_sections = data.split('$UMSTEP')
    info_data = {}

    for section in info_sections:

        step_match = re.search(r'=\s+(\d+)', section)
#       if not step_match:
#           continue
        step_number = int(step_match.group(1))

        print(section)
        info = parse_blocks(section)

        info_data[step_number] = info

    return info_data

def parse_blocks(dat):
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

        print('checl')
        pattern = re.compile(r"TOTAL ENERGY\s*=\s*(-?\d+\.\d+)")
        match = pattern.search(data)

        if match:
            print("Match found:", match.group(1))
            info['Total_energy'] = float(match.group(1))


    print('checl1')
    return info

def command_line_args():

    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input',
                        type=str,
                        help='Provide the list of files')
    parser.add_argument('-e', '--extension',
                        type=str,
                        help='Provide the extension of files')
    return parser.parse_args()

def main():

    arg = command_line_args()
    fls = arg.input.split('.')[0]

    with open(geo.data, 'w') as out:

        files = open(fls,"r").read().splitlines()

        for file in files:

            file_dat = file+"."+arg.extension
            dat = open(file_dat,'r').read()
            info = parse_blocks(dat)

            for i in  info['Geometry']:
                print(i)
#       matrix1 = np.array(info[0]['MO_orbitals'])
#       matrix2 = np.array(info[1]['MO_orbitals'])
#       matrix = matrix1-matrix2
#       print(matrix)

        #state=1
        #mat1 = np.array(info[0]['Xvector'][state]['excited_state_vector'])
        #mat2 = np.array(info[1]['Xvector'][state]['excited_state_vector'])
#   print(mat1-mat2)


if __name__ == "__main__":
    main()

