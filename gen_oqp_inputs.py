#!/usr/bin/env python3

# Developed by Konstantin Komarov.
import os
import numpy as np


class OpenQPInputGenerator:
    def __init__(self, methods, basis_sets, functionals, scftypes, tddfttypes, xyz_file, include_hf=True):
        self.methods = methods
        self.basis_sets = basis_sets
        self.functionals = functionals
        self.scftypes = scftypes
        self.tddfttypes = tddfttypes
        self.system_geometry = self.read_xyz_file(xyz_file)
        self.name_xyz = self.extract_xyz_name(xyz_file)
        self.include_hf = include_hf

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

        for method in self.methods:
            for basis in self.basis_sets:
                for functional in self.functionals:
                    for scftype in self.scftypes:
                        scf_mult = 1 if scftype in ('rhf', 'uhf-s') else 3
                        scf = scftype.split('-')[0]
                        if method == "hf" and self.include_hf:
                            configuration = self.build_configuration(scf, scf_mult, method, basis, functional, None, f"{self.name_xyz}_{scftype}_{basis}_{functional}.inp")
                            input_configurations.append(configuration)
                        elif method == "tdhf":
                            for tddft in self.tddfttypes:
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

    def __str__(self):
        return f"OpenQPInputGenerator with {len(self.methods)} methods, {len(self.basis_sets)} basis sets, {len(self.functionals)} functionals, {len(self.scftypes)} SCF types, and {len(self.tddfttypes)} TDDFT types."



def main():
    import os
    import argparse
    parser = argparse.ArgumentParser(description='Generate OpenQP input file.')
    parser.add_argument('xyz_dir', type=str, help='Path to the directory containing XYZ files')
    args = parser.parse_args()

    xyz_dir = args.xyz_dir

    if not os.path.isdir(xyz_dir):
        print(f"Error: {xyz_dir} is not a valid directory.")
        exit(1)

    xyz_files = [file for file in os.listdir(xyz_dir) if file.endswith('.xyz')]

    if not xyz_files:
        print(f"Error: No XYZ files found in {xyz_dir}.")
        exit(1)

    for xyz_file in xyz_files:
        project_name = os.path.splitext(os.path.basename(xyz_file))[0]
        with open(os.path.join(xyz_dir,xyz_file), 'r') as file:
            lines = file.readlines()[2:]  # Skip the first two lines
#           if np.size(lines)>11:
#               file.close()
#               continue
        file.close()
        print(f"Processing {xyz_file}...")
        methods=["tdhf",]
#       methods=["hf", "tdhf"]
        basis_sets=["cc-pVDZ"]
        functionals=["slater","bhhlyp","dtcam-aee"]
#       functionals=["dtcam-aee", "dtcam-vee", "dtcam-xi", "dtcam-xiv", "dtcam-vaee", "dtcam-tune"]
#       scftypes=["rhf", "rohf", "uhf-s", "uhf-t"]
        scftypes=["rohf"]
#       tddfttypes=["rpa-s", "rpa-t", "tda-s", "tda-t", "mrsf-s", "mrsf-t", "mrsf-q", "sf"]
        tddfttypes=["mrsf-s"]

        generator = OpenQPInputGenerator(
            methods=methods,
            basis_sets=basis_sets,
            functionals=functionals,
            scftypes=scftypes,
            tddfttypes=tddfttypes,
            xyz_file=os.path.join(xyz_dir, xyz_file),
            include_hf=False
        )

        # Generate the inputs
        inputs = generator.generate_input_configurations()

#       if "tdhf" in methods:
#           output_dir = f"OQP_{project_name}_{scftypes[0]}_{tddfttypes[0]}_{basis_sets[0]}_{functionals[0]}"
#       else:
#           output_dir = f"OQP_{project_name}_{scftypes[0]}_{basis_sets[0]}_{functionals[0]}"
        output_dir = xyz_dir
        os.makedirs(output_dir, exist_ok=True)

        for config in inputs:
            file_path = os.path.join(output_dir, config['file_name'])
            with open(file_path, 'w') as file:
                for section, section_content in config.items():
                    if section == 'file_name':
                        continue
                    file.write(f"[{section}]\n")
                    if isinstance(section_content, dict):
                        for key, value in section_content.items():
                            file.write(f"{key}={value}\n")
                    elif isinstance(section_content, str):
                        file.write(f"{section_content}\n")
                    file.write("\n")
        # Print inputs
        for config in inputs:
            print(f"File Name: {config['file_name']}")
            print(f"Method: {config['input']['method']}")
            if 'tdhf' in config:
                print("TDHF Section:")
                for key, value in config['tdhf'].items():
                    print(f"  {key}: {value}")
            print("-" * 30)


if __name__ == '__main__':
    main()
