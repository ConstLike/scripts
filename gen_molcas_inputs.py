#!/usr/bin/env python3

# Developed by Konstantin Komarov.
import os
import argparse
import sys


class MolcasInputGenerator:
    def __init__(self, config):
        self.xyz_file = config['xyz_file']
        self.basis_set = config['basis_set']
        self.active_electrons = config['active_electrons']
        self.active_orbitals = config['active_orbitals']
        self.molecule_name = os.path.splitext(os.path.basename(self.xyz_file))[0]
        self.num_atoms = 0
        self.num_electrons = 0

    def read_xyz(self):
        try:
            with open(self.xyz_file, 'r') as f:
                lines = f.readlines()
            self.num_atoms = int(lines[0].strip())
            self.xyz_content = ''.join(lines[2:])

            elements = [line.split()[0] for line in lines[2:]]
            self.num_electrons = sum(self.get_num_electrons(elem) for elem in elements)

            if self.active_electrons is None or self.active_orbitals is None:
                self.determine_active_space()

        except IOError as e:
            print(f"Error reading XYZ file: {e}")
            sys.exit(1)
        except ValueError as e:
            print(f"Error parsing XYZ file: {e}")
            sys.exit(1)

    @staticmethod
    def get_num_electrons(element):
        element_dict = {
            'H': 1, 'He': 2, 'Li': 3, 'Be': 4, 'B': 5, 'C': 6, 'N': 7, 'O': 8, 'F': 9, 'Ne': 10,
            'Na': 11, 'Mg': 12, 'Al': 13, 'Si': 14, 'P': 15, 'S': 16, 'Cl': 17, 'Ar': 18,
            'K': 19, 'Ca': 20, 'Sc': 21, 'Ti': 22, 'V': 23, 'Cr': 24, 'Mn': 25, 'Fe': 26, 'Co': 27, 'Ni': 28,
            'Cu': 29, 'Zn': 30, 'Ga': 31, 'Ge': 32, 'As': 33, 'Se': 34, 'Br': 35, 'Kr': 36,
            'Rb': 37, 'Sr': 38, 'Y': 39, 'Zr': 40, 'Nb': 41, 'Mo': 42, 'Tc': 43, 'Ru': 44, 'Rh': 45, 'Pd': 46,
            'Ag': 47, 'Cd': 48, 'In': 49, 'Sn': 50, 'Sb': 51, 'Te': 52, 'I': 53, 'Xe': 54,
            'Cs': 55, 'Ba': 56, 'La': 57, 'Ce': 58, 'Pr': 59, 'Nd': 60, 'Pm': 61, 'Sm': 62, 'Eu': 63, 'Gd': 64,
            'Tb': 65, 'Dy': 66, 'Ho': 67, 'Er': 68, 'Tm': 69, 'Yb': 70, 'Lu': 71,
            'Hf': 72, 'Ta': 73, 'W': 74, 'Re': 75, 'Os': 76, 'Ir': 77, 'Pt': 78, 'Au': 79, 'Hg': 80,
            'Tl': 81, 'Pb': 82, 'Bi': 83, 'Po': 84, 'At': 85, 'Rn': 86,
            'Fr': 87, 'Ra': 88, 'Ac': 89, 'Th': 90, 'Pa': 91, 'U': 92, 'Np': 93, 'Pu': 94, 'Am': 95, 'Cm': 96,
            'Bk': 97, 'Cf': 98, 'Es': 99, 'Fm': 100, 'Md': 101, 'No': 102, 'Lr': 103,
            'Rf': 104, 'Db': 105, 'Sg': 106, 'Bh': 107, 'Hs': 108, 'Mt': 109, 'Ds': 110, 'Rg': 111, 'Cn': 112,
            'Nh': 113, 'Fl': 114, 'Mc': 115, 'Lv': 116, 'Ts': 117, 'Og': 118
        }
        return element_dict.get(element, 0)

    def determine_active_space(self):
        valence_electrons = min(self.num_electrons, 14)
        self.active_electrons = max(2, valence_electrons // 2)
        self.active_orbitals = max(2, self.active_electrons)

    def generate_input(self):
        inactive = (self.num_electrons - self.active_electrons) // 2
        n_roots = min(7, self.active_electrons * self.active_orbitals)

        input_content = f"""
&GATEWAY
  Coord = {self.molecule_name}.xyz
  Basis = {self.basis_set}
  Group = C1

&SEWARD

&SCF

&RASSCF
  Spin = 1
  Symmetry = 1
  nActEl = {self.active_electrons} 0 0
  Inactive = {inactive}
  RAS2 = {self.active_orbitals}
  CIRoot = {n_roots} {n_roots} 1
  LevShift = 0.5

&RASSI
  NrOfJobIphs = 1 {n_roots}
  {' '.join(str(i) for i in range(1, n_roots + 1))}
  XVES
  MEES
  PROP
  3
  'MLTPL  1' 1
  'MLTPL  1' 2
  'MLTPL  1' 3
"""
        return input_content

    def generate_input_file(self):
        output_dir = os.path.dirname(self.xyz_file)

        self.general_name = f"{self.molecule_name}_{self.active_electrons}-{self.active_orbitals}"
        input_content = self.generate_input()
        filename = f"{self.general_name}.inp"
        try:
            with open(os.path.join(output_dir, filename), 'w') as f:
                f.write(input_content)
            print(f"Generated: {os.path.join(output_dir, filename)}")
        except IOError as e:
            print(f"Error writing input file: {e}")
            sys.exit(1)


def process_xyz_file(xyz_file, config):
    config['xyz_file'] = xyz_file
    generator = MolcasInputGenerator(config)
    generator.read_xyz()
    generator.generate_input_file()

def process_directory(directory, config):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.xyz'):
                xyz_file = os.path.join(root, file)
                process_xyz_file(xyz_file, config)

def parse_args():
    parser = argparse.ArgumentParser(description="Generate OpenMolcas input files for XYZ files in directories")
    parser.add_argument("input_path", help="Path to XYZ file, directory with XYZ files, or directory with subdirectories containing XYZ files")
    parser.add_argument("--basis", default="ANO-S", help="Basis set to use (default: ANO-S)")
    parser.add_argument("--active_space", nargs=2, type=int, default=[None, None],
                        help="Active space: number of active electrons and orbitals")
    return parser.parse_args()


def main():
    args = parse_args()

    config = {
        'basis_set': args.basis,
        'active_electrons': args.active_space[0],
        'active_orbitals': args.active_space[1]
    }

    try:
        if os.path.isfile(args.input_path):
            if args.input_path.endswith('.xyz'):
                process_xyz_file(args.input_path, config)
            else:
                raise ValueError(f"{args.input_path} is not an XYZ file.")
        elif os.path.isdir(args.input_path):
            process_directory(args.input_path, config)
        else:
            raise ValueError(f"{args.input_path} is not a valid file or directory.")
    except (OSError, ValueError) as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
