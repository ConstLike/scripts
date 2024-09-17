#!/usr/bin/python3

""" Developed by Konstantin Komarov. """
import argparse
import os
import sys
from typing import Dict

from molcas import MolcasInputGenerator
from utils import InputUtils


def process_xyz_file(xyz_file: str, config: Dict) -> None:
    """Process a single XYZ file and generate Molcas input."""
    config = InputUtils.get_mol_info(xyz_file, config)
    generator = MolcasInputGenerator(config)
    dir_name = os.path.dirname(os.path.abspath(xyz_file))
    generator.save_input(dir_name)


def process_directory(directory: str, config: Dict) -> None:
    """Process all XYZ files in a directory and its subdirectories."""
    for root, _, files in os.walk(directory):
        for xyz_file in files:
            if xyz_file.endswith('.xyz'):
                config['xyz file'] = xyz_file
                xyz_path = os.path.join(root, xyz_file)

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


def main():
    """ main. """
    args = parse_args()

    config = {
        "OpenMolcas": {
            "basis set": 'ANO-S',
            "functional": 'lda',
            "calc type": 'caspt2',
            "active space": [12, 12],
            "symm a1": 7,
            "symm b2": 1,
            "symm b1": 4,
            "symm a2": 0,
            "num roots": 1
        },
        "CP2K_DFT": {
            "basis set": 'DZVP-GTH',
        },
        "CP2K_DFT-in-DFT": {
            "basis set": 'DZVP-GTH',
        },
        "CP2K_WF-in-DFT": {
            "basis set": 'DZVP-GTH',
            "wf basis set": 'ANO-S',
            "calc type": 'caspt2',
            "active space": [12, 12],
            "symm a1": 7,
            "symm b2": 1,
            "symm b1": 4,
            "symm a2": 0,
            "num roots": 1
        },
    }

    main_molcas(args, config['OpenMolcas'])


if __name__ == "__main__":
    main()
