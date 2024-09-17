#!/usr/bin/env python3

""" Developed by Konstantin Komarov. """
import argparse
import os
import sys


class MolcasInputGenerator:
    """ x """
    def __init__(self, config):
        self.xyz_file = config['xyz_file']
        self.config = config
        self.num_electrons = 0

    @staticmethod
    def get_num_electrons(element):
        """ x """
        element_dict = {
            'H': 1, 'He': 2, 'Li': 3, 'Be': 4, 'B': 5, 'C': 6, 'N': 7, 'O': 8,
            'F': 9, 'Ne': 10, 'Na': 11, 'Mg': 12, 'Al': 13, 'Si': 14, 'P': 15,
            'S': 16, 'Cl': 17, 'Ar': 18, 'K': 19, 'Ca': 20, 'Sc': 21, 'Ti': 22,
            'V': 23, 'Cr': 24, 'Mn': 25, 'Fe': 26, 'Co': 27, 'Ni': 28,
            'Cu': 29, 'Zn': 30, 'Ga': 31, 'Ge': 32, 'As': 33, 'Se': 34,
            'Br': 35, 'Kr': 36, 'Rb': 37, 'Sr': 38, 'Y': 39, 'Zr': 40,
            'Nb': 41, 'Mo': 42, 'Tc': 43, 'Ru': 44, 'Rh': 45, 'Pd': 46,
            'Ag': 47, 'Cd': 48, 'In': 49, 'Sn': 50, 'Sb': 51, 'Te': 52,
            'I': 53, 'Xe': 54, 'Cs': 55, 'Ba': 56, 'La': 57, 'Ce': 58,
            'Pr': 59, 'Nd': 60, 'Pm': 61, 'Sm': 62, 'Eu': 63, 'Gd': 64,
            'Tb': 65, 'Dy': 66, 'Ho': 67, 'Er': 68, 'Tm': 69, 'Yb': 70,
            'Lu': 71, 'Hf': 72, 'Ta': 73, 'W': 74, 'Re': 75, 'Os': 76,
            'Ir': 77, 'Pt': 78, 'Au': 79, 'Hg': 80, 'Tl': 81, 'Pb': 82,
            'Bi': 83, 'Po': 84, 'At': 85, 'Rn': 86, 'Fr': 87, 'Ra': 88,
            'Ac': 89, 'Th': 90, 'Pa': 91, 'U': 92, 'Np': 93, 'Pu': 94,
            'Am': 95, 'Cm': 96, 'Bk': 97, 'Cf': 98, 'Es': 99, 'Fm': 100,
            'Md': 101, 'No': 102, 'Lr': 103, 'Rf': 104, 'Db': 105, 'Sg': 106,
            'Bh': 107, 'Hs': 108, 'Mt': 109, 'Ds': 110, 'Rg': 111, 'Cn': 112,
            'Nh': 113, 'Fl': 114, 'Mc': 115, 'Lv': 116, 'Ts': 117, 'Og': 118
        }
        return element_dict.get(element, 0)

    def generate_input_lda(self):
        """ x """
        content = f"""
&GATEway
  COORd = {self.config['project']}.xyz
  BASIs = {self.config['basis set']}

&SEWArd

&SCF
  CHARge = 0
  SPIN = 1

&SCF
  CHARge = 0
  SPIN = 1
  KSDFt = lda
"""
        return content

    def generate_input_casscf(self):
        """ x """
        content = f"""
&GATEway
  COORd = {self.config['project']}.xyz
  BASIs = {self.config['basis set']}

&SEWArd

&SCF
  CHARge = 0
  SPIN = 1

&RASSCF
  Spin = 1
  Symmetry = 1
  nActEl = 0 0 0 0
  Inactive = 0 0 0 0
  RAS1 = 0 0 0 0
  RAS2 = 7 1 4 0
  RAS3 = 0 0 0 0
  CIRoot = 1 1 1
  LevShift = 0.5
"""
        return content

    def generate_input_caspt2(self):
        """ x """
        content = f"""
&GATEway
  COORd = {self.config['project']}.xyz
  BASIs = {self.config['basis set']}

&SEWArd

&SCF
  CHARge = 0
  SPIN = 1

&RASScf
  SPIN = 1
  SYMMetry = 1
  Inactive = 0 0 0 0
  RAS1 = 0 0 0 0
  RAS2 = 7 1 4 0
  RAS3 = 0 0 0 0
  CIRoot = 1 1 1
  LevShift = 0.5

&CASPt2
  PROP
"""
        # &RASSI
        #   NrOfJobIphs = 1 1
        #   {' '.join(str(i) for i in range(1, n_roots + 1))}
        #   XVES
        #   MEES
        #   PROP
        #   3
        #   'MLTPL  1' 1
        #   'MLTPL  1' 2
        #   'MLTPL  1' 3
        return content

    def generate_input_file(self):
        """ x """
        output_dir = os.path.dirname(self.xyz_file)
        input_content = self.generate_input_lda()
        filename = f"{self.config['project']}.inp"
        try:
            with open(os.path.join(output_dir, filename),
                      'w',
                      encoding='utf-8') as f:
                f.write(input_content)
            print(f"Generated: {os.path.join(output_dir, filename)}")
        except IOError as e:
            print(f"Error writing input file: {e}")
            sys.exit(1)


def process_xyz_file(xyz_file, config):
    """ x """
    config['xyz file'] = xyz_file
    base_name = os.path.basename(xyz_file)
    config['project'] = os.path.splitext(base_name)[0]
    generator = MolcasInputGenerator(config)
    generator.generate_input_file()


def process_directory(directory, config):
    """ x """
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.xyz'):
                xyz_file = os.path.join(root, file)
                process_xyz_file(xyz_file, config)


def parse_args():
    """ x """
    parser = argparse.ArgumentParser(description="Generate OpenMolcas input files for XYZ files in directories")
    parser.add_argument("input_path", help="Path to XYZ file, directory with XYZ files, or directory with subdirectories containing XYZ files")
    parser.add_argument("--basis", default="ANO-S", help="Basis set to use (default: ANO-S)")
    return parser.parse_args()


def main():
    """ main """
    args = parse_args()

    config = {
        'basis_set': args.basis,
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
            raise ValueError(f"{args.input_path} is not a valid arg.")
    except (OSError, ValueError) as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
