#!/usr/bin/python3
""" Developed by Konstantin Komarov. """
import argparse
import os
import sys
from typing import Dict

from cp2k_fat import CP2KFATInputGenerator
from gen_cp2k_input import CP2KInputGenerator
from molcas import MolcasInputGenerator
from utils import InputUtils


def process_xyz_file(xyz_file: str, config: Dict) -> None:
    """Process a single XYZ file and generate Molcas input."""
    config = InputUtils.get_mol_info(xyz_file, config)
    xyz_dir = os.path.dirname(os.path.abspath(xyz_file))
    dir_name = os.path.dirname(os.path.abspath(xyz_file))
    config['mol name'] = os.path.basename(xyz_dir).split('_')[0]

    if config['calc type'] == 'caspt2-in-dft':
        a1, a2 = config['symm a1'], config['symm a2']
        b1, b2 = config['symm b1'], config['symm b2']
        active_e, active_o = config['active space']
        generator = CP2KFATInputGenerator(config)
        subfolder = (
            f"{config['calc type']}_"
            f"{config['basis set'].lower()}_"
            f"{config['functional'].lower()}_"
            f"{config['pseudo'].lower()}_"
            f"{config['kinetic'].lower()}_"
            f"{config['wf basis set'].lower()}_"
            f"{a1}-{b2}-{b1}-{a2}_{active_e}-{active_o}"
        )
        output_dir = os.path.join(os.path.dirname(dir_name), subfolder)

    elif config['calc type'] == 'dft-in-dft':
        generator = CP2KFATInputGenerator(config)
        subfolder = (
            f"{config['calc type']}_"
            f"{config['basis set'].lower()}_"
            f"{config['functional'].lower()}_"
            f"{config['pseudo'].lower()}_"
            f"{config['kinetic'].lower()}_"
            f"{config['wf basis set'].lower()}_"
            f"wf-{config['wf functional']}"
        )
        output_dir = os.path.join(os.path.dirname(dir_name), subfolder)

    elif config['calc type'] == 'cp2k':
        generator = CP2KInputGenerator(config)
        subfolder = (
            f"{config['calc type']}_"
            f"{config['basis set'].lower()}_"
            f"{config['functional'].lower()}_"
            f"{config['pseudo'].lower()}"
        )
        output_dir = os.path.join(os.path.dirname(dir_name), subfolder)
    else:
        generator = MolcasInputGenerator(config)
        calc_type = config['calc type'].lower()
        basis_set = config['basis set'].lower()
        if calc_type in ['hf', 'dft']:
            functional = config['functional'].lower()
            subfolder = f"molcas_{basis_set}_{calc_type}_{functional}"
        else:
            a1, a2 = config['symm a1'], config['symm a2']
            b1, b2 = config['symm b1'], config['symm b2']
            active_e, active_o = config['active space']
            subfolder = f"molcas_{basis_set}_{calc_type}_{a1}-{b2}-{b1}-{a2}_{active_e}-{active_o}"
        output_dir = os.path.join(dir_name, subfolder)

    os.makedirs(output_dir, exist_ok=True)
    generator.save_input(output_dir)


def process_directory(directory: str, config: Dict) -> None:
    """Process all XYZ files in a directory and its subdirectories."""
    for root, _, files in os.walk(directory):
        if not root.endswith('_xyz'):
            continue
        for xyz_file in files:
            if xyz_file.endswith('.xyz'):
                config['xyz file'] = xyz_file
                xyz_path = os.path.join(root, xyz_file)
                config.update({"xyz dir": os.path.dirname(xyz_path)})

                process_xyz_file(xyz_path, config)


def parse_args():
    """ Parser cmd line. """
    parser = argparse.ArgumentParser(description="Generate Molcas input files")
    parser.add_argument("input_path", help="Path to XYZ file or directory")
    return parser.parse_args()


def main_molcas(args, config):
    """ molcas generator."""

    if config['calc type'].lower() == 'hf':
        config.update({"functional": 'hf'})

    try:
        if os.path.isfile(args.input_path):
            if args.input_path.endswith('.xyz'):
                process_xyz_file(args.input_path, config)
            else:
                print(f"Error: {args.input_path} is not an XYZ file.")
        elif os.path.isdir(args.input_path):
            process_directory(args.input_path, config)
        else:
            print(f"Error: {args.input_path} - not a valid file or directory.")
    except (OSError, ValueError) as e:
        print(f"Error: {e}")
        sys.exit(1)


def main_cp2k_fat(args, config):
    """ CP2K FAT generator."""

    try:
        if os.path.isfile(args.input_path):
            if args.input_path.endswith('.xyz'):
                config.update({"xyz dir": args.input_path})
                process_xyz_file(args.input_path, config)
            else:
                print(f"Error: {args.input_path} is not an XYZ file.")
        elif os.path.isdir(args.input_path):
            process_directory(args.input_path, config)
        else:
            print(f"Error: {args.input_path} - not a valid file or directory.")
    except (OSError, ValueError) as e:
        print(f"Error: {e}")
        sys.exit(1)


def main_cp2k(args, config):
    """ CP2K generator."""

    try:
        if os.path.isfile(args.input_path):
            if args.input_path.endswith('.xyz'):
                config.update({"xyz dir": args.input_path})
                process_xyz_file(args.input_path, config)
            else:
                print(f"Error: {args.input_path} is not an XYZ file.")
        elif os.path.isdir(args.input_path):
            process_directory(args.input_path, config)
        else:
            print(f"Error: {args.input_path} - not a valid file or directory.")
    except (OSError, ValueError) as e:
        print(f"Error: {e}")
        sys.exit(1)


def main():
    """ main. """
    args = parse_args()

    config = {
        "OpenMolcas": {
            "calc type": 'dft',
            "basis set": 'ANO-S',
            "functional": 'lda',
            "active space": [12, 14],
            "symm a1": 8,
            "symm b1": 2,
            "symm a2": 0,
            "symm b2": 4,
            "num roots": 1
        },
        "CP2K WF-in-DFT": {
            "calc type": "caspt2-in-dft",
            "basis set file": "GTH_BASIS_SETS",
            "basis set": "DZVP-GTH",
            "functional": 'LDA',
            "kinetic": 'LDA_K_TF',
            "pseudo file": 'GTH_POTENTIALS',
            "pseudo": 'GTH-LDA',
            "cell": [10.0, 10.0, 10.0],
            "wf basis set": 'cc-pVDZ',
            "wf functional": 'lda',
            "active space": [4, 12],
            'symm a1': 7,
            'symm b1': 5,
            'symm b2': 0,
            'symm a2': 0,
            "num roots": 1
        },
        "CP2K DFT": {
            "calc type": "dft1",
            "basis set file": "GTH_BASIS_SETS",
            "basis set": "DZVP-GTH",
            "functional": 'LDA',
            "pseudo file": 'GTH_POTENTIALS',
            "pseudo": 'GTH-LDA',
            "cell": [10.0, 10.0, 10.0],
            "cutoff": 210,
            "rel cutoff": 30
        }
    }

#   basis_sets = ['CC-PVDZ',]
#   calc_types = ['caspt2',]
#   functionals = ['lda',]
#   for basis in basis_sets:
#       for calc_type in calc_types:
#           for functional in functionals:
#               config['OpenMolcas'].update({"basis set": basis})
#               config['OpenMolcas'].update({"calc type": calc_type})
#               config['OpenMolcas'].update({"functional": functional})
#               main_molcas(args, config['OpenMolcas'])

#   basis_sets = ['DZVP-GTH',]
#   kinetics = ['LDA_K_TF',]
#   functionals = ['LDA',]
#   for basis in basis_sets:
#       for kinetic in kinetics:
#           for functional in functionals:
#               config['CP2K WF-in-DFT'].update({"basis set": basis})
#               config['CP2K WF-in-DFT'].update({"kinetic": kinetic})
#               config['CP2K WF-in-DFT'].update({"functional": functional})
#               main_cp2k_fat(args, config['CP2K WF-in-DFT'])

    basis_sets = ['DZVP-GTH',]
    kinetics = ['LDA_K_TF',]
    functionals = ['LDA',]
    for basis in basis_sets:
        for kinetic in kinetics:
            for functional in functionals:
                config['CP2K WF-in-DFT'].update({"basis set": basis})
                config['CP2K WF-in-DFT'].update({"kinetic": kinetic})
                config['CP2K WF-in-DFT'].update({"functional": functional})
                main_cp2k(args, config['CP2K DFT'])


if __name__ == "__main__":
    main()
