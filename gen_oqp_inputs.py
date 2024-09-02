#!/usr/bin/env python3

# Developed by Konstantin Komarov.
import os
import argparse
from typing import Dict, Any


class OpenQPInputGenerator:
    def __init__(self, config: Dict[str, Any], xyz_file: str):
        self.config = config
        self.xyz_file = xyz_file
        self.system_geometry = self.read_xyz_file(xyz_file)
        self.name_xyz = self.extract_xyz_name(xyz_file)

    def read_xyz_file(self, xyz_file):
        if not os.path.exists(xyz_file):
            raise FileNotFoundError(f"XYZ file not found: {xyz_file}")

        atom_numbers= {
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
        number_to_symbol = {v: k for k, v in atom_numbers.items()}

        geometry = []

        with open(xyz_file, 'r') as file:
            lines = file.readlines()[2:]  # Skip the first two lines
            for line in lines:
                parts = line.split()
                if len(parts) == 4:
                    atom, x, y, z = parts
                    if atom.isdigit():
                        atom_number = int(atom)
                        atom_symbol = number_to_symbol.get(atom_number, str(atom_number))
                    else:
                        atom_symbol = atom.capitalize()
                    geometry.append(f" {atom_symbol} {float(x):14.9f} {float(y):14.9f} {float(z):14.9f}")

        return "\n".join(geometry)


    def extract_xyz_name(self, xyz_file):
        return os.path.splitext(os.path.basename(xyz_file))[0]

    def generate_input_configurations(self):
        input_configurations = []

        for method in self.config['methods']:
            for basis in self.config['basis_sets']:
                for functional in self.config['functionals']:
                    for scftype in self.config['scftypes']:
                        scf_mult = 1 if scftype in ('rhf', 'uhf-s') else 3
                        scf = scftype.split('-')[0]
                        if method == "hf" and self.config.get('include_hf', True):
                            configuration = self.build_configuration(scf, scf_mult, method, basis, functional, None, f"{self.name_xyz}_{scftype}_{basis}_{functional}.inp")
                            input_configurations.append(configuration)
                        elif method == "tdhf":
                            for tddft in self.config['tddfttypes']:
                                if self.is_valid_tddft_scf_combination(scf, tddft):
                                    file_name = f"{self.name_xyz}_{scftype}_{tddft}_{basis}_{functional}.inp"
                                    configuration = self.build_configuration(scf, scf_mult, method, basis, functional, tddft, file_name)
                                    input_configurations.append(configuration)

        return input_configurations

    def is_valid_tddft_scf_combination(self, scf, tddft):
        if scf == 'rhf':
            return tddft in ["rpa-s", "rpa-t", "tda-s", "tda-t"]
        elif scf == 'rohf':
            return tddft in ["mrsf-s", "mrsf-t", "mrsf-q", "sf"]
        return False

    def determine_tddft_multiplicity(self, tddft):
        if tddft is None:
            return None
        elif '-s' in tddft:
            return 1
        elif '-t' in tddft:
            return 3
        elif '-q' in tddft:
            return 5
        else:
            return 1


    def build_configuration(self, scf, scf_mult, method, basis, functional, tddft, file_name):
        tddft_mult = self.determine_tddft_multiplicity(tddft)

        configuration = {
            "file_name": file_name,
            "input": {
                "system": "\n "+self.system_geometry,
                "charge": 0,
                "method": method,
                "basis": basis,
                "runtype": "grad",
                "functional": functional,
                "d4": False,
            },
            "guess": {
                "type": "huckel",
                "save_mol": True,
            },
            "scf": {
                "type": scf,
                "maxit": 100,
                "maxdiis": 5,
                "multiplicity": scf_mult,
                "conv": "1.0e-7",
                "save_molden": True,
            },
            "dftgrid": {
                "rad_npts": 96,
                "ang_npts": 302,
                "pruned": "",
                "hfscale": 1.0,
            },
            "properties": {
                "grad": 0 if tddft is None else 3,
            }
        }
        if tddft:
            configuration["tdhf"] = {
                "type": tddft.split('-')[0],
                "maxit": 30,
                "multiplicity": tddft_mult,
                "conv": "1.0e-10",
                "nstate": 10,
                "zvconv": "1.0e-10",
            }
        return configuration

def process_directory(directory: str, config: Dict[str, Any]):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.xyz'):
                xyz_file = os.path.join(root, file)
                process_xyz_file(xyz_file, config)

def process_xyz_file(xyz_file: str, config: Dict[str, Any]):
    print(f"Processing {xyz_file}...")
    generator = OpenQPInputGenerator(config, xyz_file)

    # Generate the inputs
    inputs = generator.generate_input_configurations()

    output_dir = os.path.dirname(xyz_file)

    for input_config in inputs:
        file_path = os.path.join(output_dir, input_config['file_name'])
        with open(file_path, 'w') as file:
            for section, section_content in input_config.items():
                if section == 'file_name':
                    continue
                file.write(f"[{section}]\n")
                if isinstance(section_content, dict):
                    for key, value in section_content.items():
                        file.write(f"{key}={value}\n")
                elif isinstance(section_content, str):
                    file.write(f"{section_content}\n")
                file.write("\n")
        print(f"Generated: {file_path}")

def parse_args():
    parser = argparse.ArgumentParser(description='Generate OpenQP input files.')
    parser.add_argument('input_path', type=str, help='Path to the directory containing XYZ files or subdirectories with XYZ files')
    return parser.parse_args()


def main():
    args = parse_args()

    if not os.path.exists(args.input_path):
        print(f"Error: {args.input_path} does not exist.")
        exit(1)

    config = {
        'methods': ["hf"],
        'basis_sets': ["cc-pVDZ"],
        'functionals': [""],
        'scftypes': ["rhf"],
        'tddfttypes': ["mrsf-s"],
        'include_hf': True,
    }

    if os.path.isfile(args.input_path) and args.input_path.endswith('.xyz'):
        process_xyz_file(args.input_path, config)
    elif os.path.isdir(args.input_path):
        process_directory(args.input_path, config)
    else:
        print(f"Error: {args.input_path} is neither a valid XYZ file nor a directory.")
        exit(1)


if __name__ == '__main__':
    main()
