#!/usr/bin/env python3

import argparse
import json
import os
import re
from collections import defaultdict


def extract_info_from_filename(filename):
    parts = filename.split('_')
    molecule_and_distance = parts[0]
    molecule = '-'.join(molecule_and_distance.split('-')[:-1])
    distance = float(molecule_and_distance.split('-')[-1])
    basis = parts[-3]
    functional = parts[-2]
    pseudopotential = parts[-1].replace('.log', '')
    return molecule, distance, basis, functional, pseudopotential


def extract_cp2k_total_energy(content):
    match = re.search(
        r'ENERGY\| Total FORCE_EVAL \( QS \) energy \[a\.u\.\]:\s+([-\d.]+)',
        content
    )
    return float(match.group(1)) if match else None


def process_file(file_path):
    filename = os.path.basename(file_path)
    molecule, distance, basis, functional, pseudopotential = extract_info_from_filename(filename)

    with open(file_path, 'r', encoding="utf-8") as file:
        content = file.read()
        total_energy = extract_cp2k_total_energy(content)

    return molecule, {
        "distance": distance,
        "total_energy": total_energy,
        "basis": basis,
        "functional": functional,
        "pseudopotential": pseudopotential
    }


def process_directory(directory):
    results = defaultdict(list)
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.log'):
                file_path = os.path.join(root, file)
                molecule, data = process_file(file_path)
                results[molecule].append(data)
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Extract CP2K energy information from log files."
    )
    parser.add_argument(
        "input",
        help="Input directory with log files or subdirectories"
    )
    parser.add_argument(
        "method",
        default='default',
        help="Input directory with log files or subdirectories"
    )
    args = parser.parse_args()

    if not os.path.isdir(args.input):
        print(f"Error: {args.input} is not a valid directory.")
        return

    results = process_directory(args.input)

    method = args.method

    for molecule, data in results.items():
        output_filename = f"{molecule}_{method}_results.json"
        with open(output_filename, 'w', encoding="utf-8") as outfile:
            json.dump({
                "molecule": molecule,
                method: sorted(data, key=lambda x: x['distance'])
            }, outfile, indent=2)
        print(f"Results for {molecule} saved to {output_filename}")


if __name__ == "__main__":
    main()
