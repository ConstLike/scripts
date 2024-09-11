#!/usr/bin/env python3

import os
import re
import json
import argparse
from collections import defaultdict

def extract_info_from_filename(filename):
    parts = filename.split('_')
    molecule_and_distance = parts[0]
    molecule = '-'.join(molecule_and_distance.split('-')[:-1])
    distance = float(molecule_and_distance.split('-')[-1])
    active_electrons = parts[-2]
    active_orbitals = parts[-1].replace('.log', '')
    return molecule, distance, active_electrons, active_orbitals

def extract_molcas_rasscf_1_energy(content):
    match = re.search(r'::    RASSCF root number  1 Total energy:\s+([-\d.]+)', content)
    return float(match.group(1)) if match else None

def extract_molcas_scf_energy(content):
    match = re.search(r'::    Total SCF energy\s+([-\d.]+)', content)
    return float(match.group(1)) if match else None

def process_file(file_path):
    filename = os.path.basename(file_path)
    molecule, distance, active_electrons, active_orbitals = extract_info_from_filename(filename)

    with open(file_path, 'r') as file:
        content = file.read()
        total_energy = extract_molcas_rasscf_1_energy(content)
#       total_energy = extract_molcas_scf_energy(content)

    basis = "dzvp-gth"
    functional = "lda"
    pseudopotential = "gth-lda"

    return molecule, {
        "distance": distance,
        "total_energy": total_energy,
        "basis": basis,
        "functional": functional,
        "pseudopotential": pseudopotential,
        "logfile": os.path.abspath(file_path)
    }

def process_directory(directory):
    results = defaultdict(list)
    for root, _, files in os.walk(directory):
        filtered_files = [f for f in files if "extern" not in f]
        for file in filtered_files:
            if file.endswith('.log'):
                file_path = os.path.join(root, file)
                molecule, data = process_file(file_path)
                results[molecule].append(data)
    return results

def main():
    parser = argparse.ArgumentParser(description="Extract CP2K energy information from log files.")
    parser.add_argument("input", help="Input directory with log files or subdirectories")
    parser.add_argument("method", default='default', help="Input directory with log files or subdirectories")
    args = parser.parse_args()

    if not os.path.isdir(args.input):
        print(f"Error: {args.input} is not a valid directory.")
        return

    results = process_directory(args.input)

    method = args.method

    for molecule, data in results.items():
        output_filename = f"{molecule}_{method}_results.json"
        with open(output_filename, 'w') as outfile:
            json.dump({
                "molecule": molecule,
                method: sorted(data, key=lambda x: x['distance'])
            }, outfile, indent=2)
        print(f"Results for {molecule} saved to {output_filename}")

if __name__ == "__main__":
    main()
