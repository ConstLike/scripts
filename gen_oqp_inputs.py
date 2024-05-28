#!/usr/bin/env python3

# Developed by Konstantin Komarov.

class ConfigurationGenerator:
    def __init__(self, methods, basis_sets, functionals, scftypes):
        self.methods = methods
        self.basis_sets = basis_sets
        self.functionals = functionals
        self.scftypes = scftypes
        self.system_geometry = """8   0.000000000   0.000000000  -0.041061554
 1  -0.533194329   0.533194329  -0.614469223
 1   0.533194329  -0.533194329  -0.614469223
""".strip()

    def generate_input_configurations(self):
        input_configurations = []

        for method in self.methods:
            for basis in self.basis_sets:
                for functional in self.functionals:
                    for scftype in self.scftypes:
                        scf_mult = 1 if scftype in ('rhf', 'uhf-s') else 3
                        scf = scftype.split('-')[0]

                        tddft_options = []
                        if method == "tdhf":
                            if scf == 'rhf':
                                tddft_options = ["rpa-s", "rpa-t", "tda-s", "tda-t"]
                            elif scf == 'rohf':
                                tddft_options = ["mrsf-s", "mrsf-t", "mrsf-q", "sf"]

                        if not tddft_options and method == "tdhf":
                            continue

                        tddft_options = [None] if not tddft_options else tddft_options

                        for tddft in tddft_options:
                            file_name = f"h2o_{scftype}_{basis}_{functional}.inp" if tddft is None else f"h2o_{scftype}_{tddft}_{basis}_{functional}.inp"
                            configuration = self.build_configuration(scf, scf_mult, method, basis, functional, tddft, file_name)
                            input_configurations.append(configuration)

        return input_configurations

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
                "conv": "1.0e-10",
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
        return f"ConfigurationGenerator with {len(self.methods)} methods, {len(self.basis_sets)} basis sets, {len(self.functionals)} functionals, and {len(self.scftypes)} SCF types."


if __name__ == '__main__':
    generator = ConfigurationGenerator(
        methods=["hf", "tdhf"],
        basis_sets=["6-31g"],
        functionals=["slater", "pbe", "bhhlyp", "b3lypv5", "m06-2x", "cam-b3lyp"],
        scftypes=["rhf", "rohf", "uhf-s", "uhf-t"]
    )

    # Generate the configurations
    configurations = generator.generate_input_configurations()
    import os

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

#   # Print each configuration
#   for config in configurations:
#       print(f"File Name: {config['file_name']}")
#       if 'tdhf' in config:  # Check if 'tdhf' section exists
#           print("TDHF Section:")
#           for key, value in config['tdhf'].items():
#               print(f"  {key}: {value}")
#       else:
#           print("No TDHF Section")
#       print("-" * 30)
