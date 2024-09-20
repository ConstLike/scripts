#!/usr/bin/python3
""" Developed by Konstantin Komarov. """

import argparse
import json
import os
import re
from typing import Any, Dict, List, Optional, Union


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
        print(match)
        return float(match.group(1)) if match else None

    def extract_energy_molcas(self, log_content: str, calc_type: str) -> Optional[float]:
        """Extract energy value for a specific calculation type."""
        patterns = {
            'hf': r'::    Total SCF energy\s+([-\d.]+)',
            'dft': r'::    Total KS-DFT energy\s+([-\d.]+)',
            'casscf': r'::    RASSCF root number  1 Total energy:\s+([-\d.]+)',
            'caspt2': r'::    CASPT2 Root  1     Total energy:\s+([-\d.]+)'
        }
        match = re.search(patterns[calc_type], log_content)
        return float(match.group(1)) if match else None

    def find_molcas_log(self, directory: str) -> Optional[str]:
        """Find Molcas log file in the given directory."""
        for file in os.listdir(directory):
            if file.startswith("extern") and file.endswith(".out"):
                return os.path.join(directory, file)
        return None

    def extract_scf_data(self, log_content: str) -> List[Dict[str, float]]:
        """Extract SCF data for FAT calculations."""
        scf_data = []
        pattern = r'FAT\|\s+(\d+),\s+(\d+),\s+(\d+),\s+(\d+),\s+([-\d.]+),\s+([-\d.]+),\s+([-\d.]+),\s+([-\d.]+),\s+([-\d.]+),\s+([-\d.]+),\s+([-\d.]+),\s+([-\d.]+),\s+([-\d.]+),\s+([-\d.]+)'
        matches = re.finditer(pattern, log_content)
        for match in matches:
            scf_data.append({
                'i_iter': int(match.group(1)),
                'n_iter': int(match.group(2)),
                'i_frag': int(match.group(3)),
                'n_frag': int(match.group(4)),
                'self': float(match.group(5)),
                'emb': float(match.group(6)),
                'kin_ref': float(match.group(7)),
                'kin_frag': float(match.group(8)),
                'xc_ref': float(match.group(9)),
                'xc_frag': float(match.group(10)),
                'ee': float(match.group(11)),
                'ne': float(match.group(12)),
                'nn': float(match.group(13)),
                'tot': float(match.group(14))
            })
        return scf_data

    def extract_energy_contributions(self, log_content: str) -> Dict[str, Union[float, List[float]]]:
        """Extract energy contributions for FAT calculations."""
        contributions: Dict[str, Union[float, List[float]]] = {}
        patterns = {
            'self energy': r'FAT\| self energy fragment\s+(\d+):\s+([-\d.]+)',
            'emb energy': r'FAT\| emb energy fragment\s+(\d+):\s+([-\d.]+)',
            'kin energy': r'FAT\| kin energy (reference\s*|fragment\s+\d+):\s+([-\d.]+)',
            'xc energy': r'FAT\| xc energy (reference\s*|fragment\s+\d+):\s+([-\d.]+)',
            'ee energy': r'FAT\| ee energy fragments\s+(\d+)\s+(\d+):\s+([-\d.]+)',
            'ne energy': r'FAT\| ne energy fragments\s+(\d+)\s+(\d+):\s+([-\d.]+)',
            'nn energy': r'FAT\| nn energy fragments\s+(\d+)\s+(\d+):\s+([-\d.]+)'
        }

        for energy_type, pattern in patterns.items():
            matches = re.finditer(pattern, log_content)
            for match in matches:
                if energy_type in ['self energy', 'emb energy']:
                    key = f"{energy_type} frag {match.group(1)}"
                    contributions[key] = float(match.group(2))
                elif energy_type in ['kin energy', 'xc energy']:
                    print(match)
                    key = f"{energy_type} fat"
                    if key not in contributions:
                        contributions[key] = []
                    if match.group(1) == 'reference':
                        contributions[key].insert(0, float(match.group(2)))
                    else:
                        contributions[key].append(float(match.group(2)))
                else:
                    key = f"{energy_type} frag {match.group(1)}"
                    contributions[key] = float(match.group(3))

        # Calculate NAD energies
        for energy_type in ['kin energy', 'xc energy']:
            fat_key = f"{energy_type} fat"
            if fat_key in contributions:
                fat_values = contributions[fat_key]
                print(fat_values)
                if isinstance(fat_values, list) and len(fat_values) == 3:
                    nad_key = f"{energy_type} nad"
                    contributions[nad_key] = (
                        fat_values[0] - sum(fat_values[1:])
                    )

        return contributions

    def extract_energy_cp2k(self, log_content: str) -> Optional[float]:
        """Extract energy value for a specific calculation type."""
        pattern = r'ENERGY\| Total FORCE_EVAL \( FAT \) energy \[a\.u\.\]:\s+([-\d.]+)'
        match = re.search(pattern, log_content)
        return float(match.group(1)) if match else None

    def process_molcas_log(self, log_file_path: str) -> Dict[str, Optional[float]]:
        """Process a single log file and extract energies."""
        result: Dict[str, Union[float, str, None]] = {
            "logfile": os.path.abspath(log_file_path)
        }
        with open(log_file_path, 'r', encoding="utf-8") as f:
            log_content = f.read()
        for calc_type in ['hf', 'dft', 'casscf', 'caspt2']:
            energy = self.extract_energy_molcas(log_content, calc_type)
            if energy is not None:
                result[f"total energy {calc_type}"] = energy
        return result

    def process_cp2k_log(self, log_file_path: str) -> Dict[str, Any]:
        """ x """
        result: Dict[str, Any] = {
            "logfile": os.path.abspath(log_file_path)
        }
        with open(log_file_path, 'r', encoding="utf-8") as f:
            log_content = f.read()

        energy = self.extract_energy_cp2k(log_content)
        if energy is not None:
            result["total energy fat"] = energy

        result["scf data"] = self.extract_scf_data(log_content)
        result.update(self.extract_energy_contributions(log_content))

        # Process Molcas log file if it exists
        molcas_log_path = self.find_molcas_log(os.path.dirname(log_file_path))
        if molcas_log_path:
            with open(molcas_log_path, 'r', encoding="utf-8") as f:
                molcas_log_content = f.read()
            for calc_type in ['hf', 'dft', 'casscf', 'caspt2']:
                energy = self.extract_energy_molcas(molcas_log_content, calc_type)
                if energy is not None:
                    result[f"wf total energy {calc_type}"] = energy

        return result

    def process_directory(self, root_dir: str):
        """Process the directory structure to extract calculation results."""
        for dirpath, dirnames, filenames in os.walk(root_dir):
            xyz_file = next((f for f in filenames if f.endswith('.xyz')), None)
            if xyz_file:
                with open(os.path.join(dirpath, xyz_file),
                          'r',
                          encoding="utf-8") as f:
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
                        result = self.process_molcas_log(log_file_path)
                        result["distance"] = distance

                        key = f"{mol_name}_{subdir}"
                        if key not in self.results["calculations"]:
                            self.results["calculations"][key] = []
                        self.results["calculations"][key].append(result)

    def process_cp2k_directory(self, root_dir: str):
        for dirpath, _, filenames in os.walk(root_dir):
            xyz_dir = os.path.join(dirpath, f"{os.path.basename(dirpath)}_xyz")
            if os.path.exists(xyz_dir):
                xyz_file = next((f for f in os.listdir(xyz_dir) if f == 'tot.xyz'), None)
                if xyz_file:
                    with open(os.path.join(xyz_dir, xyz_file), 'r', encoding="utf-8") as f:
                        xyz_content = f.read()
                    distance = self.extract_distance(xyz_content)

                    for root, _, files in os.walk(dirpath):
                        log_files = [f for f in files if f.endswith('.log')]
                        for log_file in log_files:
                            log_file_path = os.path.join(root, log_file)
                            result = self.process_cp2k_log(log_file_path)
                            result["distance"] = distance

                            calc_type = os.path.basename(root)
                            if calc_type not in self.results["calculations"]:
                                self.results["calculations"][calc_type] = []
                            self.results["calculations"][calc_type].append(result)

    def save_results(self, output_file: str):
        """Save extracted results to a JSON file."""
        with open(output_file, 'w', encoding="utf-8") as f:
            json.dump(self.results, f, indent=2)


def parse_args():
    parser = argparse.ArgumentParser(description="Extract energy information from log files.")
    parser.add_argument("input", help="Input directory with log files or subdirectories")
    parser.add_argument("--type", choices=['molcas', 'cp2k'], required=True, help="Type of calculation")
    return parser.parse_args()


def main():
    """Main function to run the result extraction process."""
    args = parse_args()

    if not os.path.isdir(args.input):
        print(f"Error: {args.input} is not a valid directory.")
        return

    config = {
        "root_dir": args.input,
        "output_file": f"{args.type}_results.json"
    }
    extractor = ResultExtractor(config)

    if args.type == 'molcas':
        extractor.process_molcas_directory(config["root_dir"])
    elif args.type == 'cp2k':
        extractor.process_cp2k_directory(config["root_dir"])

    extractor.save_results(config["output_file"])


if __name__ == "__main__":
    main()
