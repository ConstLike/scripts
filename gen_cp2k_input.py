#!/usr/bin/env python3

import os
import argparse
from typing import List, Dict

class CP2KInputGenerator:
    def __init__(self, config: Dict):
        self.xyz_dir = config['xyz dir']
        self.basis_set = config['cp2k']['basis set']
        self.dft_functional = config['cp2k']['functional']
        self.pseudopotential = config['cp2k']['pseudo']
        self.cutoff = config['cp2k']['cutoff']
        self.rel_cutoff = config['cp2k']['rel_cutoff']
        self.cell_size = config['cell']

    def generate_input(self, molecule_name: str, xyz_filename: str) -> str:
        input_content = f"""&GLOBAL
  PROJECT {molecule_name}
  RUN_TYPE ENERGY
  PRINT_LEVEL MEDIUM
&END GLOBAL

&FORCE_EVAL
  METHOD Quickstep
  &DFT
    BASIS_SET_FILE_NAME GTH_BASIS_SETS
    POTENTIAL_FILE_NAME GTH_POTENTIALS
    &MGRID
      CUTOFF {self.cutoff}
      REL_CUTOFF {self.rel_cutoff}
    &END MGRID
    &QS
      METHOD GPW
      EPS_DEFAULT 1.0E-10
#     EXTRAPOLATION ASPC
#     EXTRAPOLATION_ORDER 3
    &END QS
    &SCF
      SCF_GUESS ATOMIC
      EPS_SCF 1.0E-8
      MAX_SCF 100
#     &MIXING
#       METHOD BROYDEN_MIXING
#       ALPHA 0.4
#       NBROYDEN 8
#     &END MIXING
      &OUTER_SCF
        EPS_SCF 1.0E-8
        MAX_SCF 10
      &END
      &OT
        MINIMIZER DIIS
        PRECONDITIONER FULL_SINGLE_INVERSE
      &END
    &END SCF
    &XC
      &XC_FUNCTIONAL {self.dft_functional}
      &END XC_FUNCTIONAL
    &END XC
  &END DFT
  &SUBSYS
    &CELL
      ABC {self.cell_size[0]} {self.cell_size[1]} {self.cell_size[2]}
    &END CELL
    &TOPOLOGY
      COORD_FILE_NAME {xyz_filename}
      COORD_FILE_FORMAT XYZ
    &END TOPOLOGY
    &KIND DEFAULT
      BASIS_SET {self.basis_set}
      POTENTIAL {self.pseudopotential}
    &END KIND
  &END SUBSYS
&END FORCE_EVAL
"""
        return input_content

def process_input(input_path: str, config: Dict):
    generator = CP2KInputGenerator(config)

    def save_input(xyz_path: str):
        molecule_name = os.path.splitext(os.path.basename(xyz_path))[0]
        xyz_filename = os.path.basename(xyz_path)
        input_content = generator.generate_input(molecule_name, xyz_filename)
        output_dir = os.path.dirname(xyz_path)
        file_name = f"{molecule_name}_{config['cp2k']['basis set'].lower()}_{config['cp2k']['functional'].lower()}_{config['cp2k']['pseudo'].lower()}.inp"
        with open(os.path.join(output_dir, file_name), 'w') as f:
            f.write(input_content)
        print(f"Generated: {os.path.join(output_dir, file_name)}")

    if os.path.isfile(input_path) and input_path.endswith('.xyz'):
        save_input(input_path)
    elif os.path.isdir(input_path):
        for root, dirs, files in os.walk(input_path):
            for file in files:
                if file.endswith('.xyz'):
                    save_input(os.path.join(root, file))

def parse_args():
    parser = argparse.ArgumentParser(description="Generate CP2K input file")
    parser.add_argument("input", help="Path to XYZ file, directory with XYZ files, or directory with subdirectories containing XYZ files")
    parser.add_argument("--cell", nargs=3, type=float, default=[10, 10, 10], help="Cell size in Angstroms (e.g. --cell 20 20 20)")
    return parser.parse_args()

def main():
    args = parse_args()

    config = {
        'xyz dir': args.input,
        'cell': args.cell,
        'cp2k': {
            'basis set': 'dzvp-gth',
            'functional': 'lda',
            'pseudo': 'gth-lda',
            'cutoff': 210,
            'rel_cutoff': 30
        }
    }

    process_input(args.input, config)

if __name__ == "__main__":
    main()
