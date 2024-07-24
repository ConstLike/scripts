#!/usr/bin/env python3

# Developed by Konstantin Komarov.
import os

class ConfigurationGenerator:
    def __init__(self, methods, basis_sets, functionals, scftypes, tddfttypes, xyz_file, include_hf=True):
        self.methods = methods
        self.basis_sets = basis_sets
        self.functionals = functionals
        self.scftypes = scftypes
        self.tddfttypes = tddfttypes
        self.system_geometry = self.read_xyz_file(xyz_file)
        self.include_hf = include_hf

    def read_xyz_file(self, xyz_file):
        if not os.path.exists(xyz_file):
            raise FileNotFoundError(f"XYZ file not found: {xyz_file}")

        atom_numbers = {'H': 1, 'He': 2, 'Li': 3, 'Be': 4, 'B': 5, 'C': 6, 'N': 7, 'O': 8, 'F': 9, 'Ne': 10}
        geometry = []

        with open(xyz_file, 'r') as file:
            lines = file.readlines()[2:]  # Skip the first two lines
            for line in lines:
                parts = line.split()
                if len(parts) == 4:
                    atom, x, y, z = parts
                    atom_number = atom_numbers.get(atom, 0)
                    geometry.append(f"{atom_number:2d} {float(x):14.9f} {float(y):14.9f} {float(z):14.9f}")

        return "\n".join(geometry)

    def generate_input_configurations(self):
        input_configurations = []

        for method in self.methods:
            for basis in self.basis_sets:
                for functional in self.functionals:
                    for scftype in self.scftypes:
                        scf_mult = 1 if scftype in ('rhf', 'uhf-s') else 3
                        scf = scftype.split('-')[0]
                        if method == "hf" and self.include_hf:
                            configuration = self.build_configuration(scf, scf_mult, method, basis, functional, None, f"h2o_{scftype}_{basis}_{functional}.inp")
                            input_configurations.append(configuration)
                        elif method == "tdhf":
                            for tddft in self.tddfttypes:
                                if self.is_valid_tddft_scf_combination(scf, tddft):
                                    file_name = f"h2o_{scftype}_{tddft}_{basis}_{functional}.inp"
                                    configuration = self.build_configuration(scf, scf_mult, method, basis, functional, tddft, file_name)
                                    input_configurations.append(configuration)

#                       tddft_options = []
#                       if method == "tdhf":
#                           if scf == 'rhf':
#                               tddft_options = ["rpa-s", "rpa-t", "tda-s", "tda-t"]
#                           elif scf == 'rohf':
#                               tddft_options = ["mrsf-s", "mrsf-t", "mrsf-q", "sf"]

#                       if not tddft_options and method == "tdhf":
#                           continue

#                       tddft_options = [None] if not tddft_options else tddft_options

#                       for tddft in tddft_options:
#                           file_name = f"h2o_{scftype}_{basis}_{functional}.inp" if tddft is None else f"h2o_{scftype}_{tddft}_{basis}_{functional}.inp"
#                           configuration = self.build_configuration(scf, scf_mult, method, basis, functional, tddft, file_name)
#                           input_configurations.append(configuration)

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
                "maxit": 30,
                "maxdiis": 5,
                "multiplicity": scf_mult,
                "conv": "1.0e-8",
                "save_molden": False,
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
                "maxit": 15,
                "multiplicity": tddft_mult,
                "conv": "1.0e-10",
                "nstate": 6,
                "zvconv": "1.0e-10"
            }
        return configuration

    def __str__(self):
        return f"ConfigurationGenerator with {len(self.methods)} methods, {len(self.basis_sets)} basis sets, {len(self.functionals)} functionals, {len(self.scftypes)} SCF types, and {len(self.tddfttypes)} TDDFT types."


if __name__ == '__main__':
    generator = ConfigurationGenerator(
        methods=["hf", "tdhf"],
        basis_sets=["6-31g"],
#       functionals=["slater", "pbe", "bhhlyp", "b3lypv5", "m06-2x", "cam-b3lyp"],
        functionals=["dtcam-aee", "dtcam-vee", "dtcam-xi", "dtcam-xiv", "dtcam-vaee", "dtcam-tune"],
#       scftypes=["rhf", "rohf", "uhf-s", "uhf-t"]
        scftypes=["rohf", ],
#       tddfttypes=["rpa-s", "rpa-t", "tda-s", "tda-t", "mrsf-s", "mrsf-t", "mrsf-q", "sf"],
        tddfttypes=["mrsf-s", "mrsf-q"],
        xyz_file="h2o.xyz",
        include_hf=False
    )

    # Generate the configurations
    configurations = generator.generate_input_configurations()

    output_dir = 'input_files'
    os.makedirs(output_dir, exist_ok=True)

    for config in configurations:
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
    # Print configurations
    for config in configurations:
        print(f"File Name: {config['file_name']}")
        print(f"Method: {config['input']['method']}")
        if 'tdhf' in config:
            print("TDHF Section:")
            for key, value in config['tdhf'].items():
                print(f"  {key}: {value}")
        print("-" * 30)

