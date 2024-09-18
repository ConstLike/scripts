#!/usr/bin/python3

""" Developed by Konstantin Komarov. """

import argparse
import json
import os
import re
from typing import Dict, List, Optional, Union


class ResultExtractor:
    """Extracts and structures Molcas calculation results from log files."""

    def __init__(self, config: Dict):
        """Initialize the ResultExtractor with configuration settings."""
        self.config = config
        self.results: Dict[str, Dict[str, List[Dict[str, float]]]] = {
            "calculations": {}
        }

    def extract_distance(self, xyz_content: str) -> Optional[float]:
        """Extract distance value in Bohr from XYZ file content."""
        match = re.search(r'= ([\d.]+) Bboohhrr', xyz_content)
        return float(match.group(1)) if match else None

    def extract_energy(self, log_content: str, calc_type: str) -> Optional[float]:
        """Extract energy value for a specific calculation type."""
        patterns = {
            'hf': r'::    Total SCF energy\s+([-\d.]+)',
            'dft': r'::    Total KS-DFT energy\s+([-\d.]+)',
            'casscf': r'::    RASSCF root number  1 Total energy:\s+([-\d.]+)',
            'caspt2': r'::    CASPT2 Root  1     Total energy:\s+([-\d.]+)'
        }
        match = re.search(patterns[calc_type], log_content)
        return float(match.group(1)) if match else None

    def process_log_file(self, log_file_path: str) -> Dict[str, Optional[float]]:
        """Process a single log file and extract energies."""
        result: Dict[str, Union[float, str, None]] = {
            "logfile": os.path.abspath(log_file_path)
        }
        with open(log_file_path, 'r', encoding="utf-8") as f:
            log_content = f.read()
        for calc_type in ['hf', 'dft', 'casscf', 'caspt2']:
            energy = self.extract_energy(log_content, calc_type)
            if energy is not None:
                result[f"total energy {calc_type}"] = energy
        return result

    def process_directory(self, root_dir: str):
        """Process the directory structure to extract calculation results."""
        for dirpath, dirnames, filenames in os.walk(root_dir):
            xyz_file = next((f for f in filenames if f.endswith('.xyz')), None)
            if xyz_file:
                with open(os.path.join(dirpath, xyz_file), 'r', encoding="utf-8") as f:
                    xyz_content = f.read()
                distance = self.extract_distance(xyz_content)
                mol_name = os.path.splitext(xyz_file)[0]
                mol_name = '-'.join(mol_name.split('-')[:-1])

                for subdir in dirnames:
                    subfolder_path = os.path.join(dirpath, subdir)
                    log_files = [f for f in os.listdir(subfolder_path)
                                 if f.endswith('.log')]
                    
                    for log_file in log_files:
                        log_file_path = os.path.join(subfolder_path, log_file)
                        result = self.process_log_file(log_file_path)
                        result["distance"] = distance

                        key = f"{mol_name}_{subdir}"
                        if key not in self.results["calculations"]:
                            self.results["calculations"][key] = []
                        self.results["calculations"][key].append(result)

    def save_results(self, output_file: str):
        """Save extracted results to a JSON file."""
        with open(output_file, 'w', encoding="utf-8") as f:
            json.dump(self.results, f, indent=2)


def parse_args():
    parser = argparse.ArgumentParser(description="Extract CP2K energy information from log files.")
    parser.add_argument("input", help="Input directory with log files or subdirectories")
    return parser.parse_args()


def main_molcas(config):
    """Main function to run the result extraction process for molcas."""
    extractor = ResultExtractor(config)
    extractor.process_directory(config["root_dir"])
    extractor.save_results(config["output_file"])


def main():
    """Main function to run the result extraction process."""
    args = parse_args()

    if not os.path.isdir(args.input):
        print(f"Error: {args.input} is not a valid directory.")
        return

    config = {
        "root_dir": args.input,
        "output_file": "molcas_results.json"
    }
    main_molcas(config)


if __name__ == "__main__":
    main()
