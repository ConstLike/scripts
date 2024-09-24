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

    def extract_cp2k_energies(self, log_content: str) -> Dict[str, float]:
        """Extract energy components from CP2K log content."""
        energy_patterns = {
            "Overlap energy": r"Overlap energy of the core charge distribution:\s+([-\d.]+)",
            "Self energy": r"Self energy of the core charge distribution:\s+([-\d.]+)",
            "Core hamiltonian energy": r"Core Hamiltonian energy:\s+([-\d.]+)",
            "Hartree energy": r"Hartree energy:\s+([-\d.]+)",
            "XC energy": r"Exchange-correlation energy:\s+([-\d.]+)",
            "Total energy": r"Total energy:\s+([-\d.]+)",
        }
        energies = {}
        for key, pattern in energy_patterns.items():
            match = re.search(pattern, log_content)
            if match:
                energies[key] = float(match.group(1))
        return energies

    def extract_fragment_scf_data(self, log_content: str) -> Dict[str, List[Dict[str, float]]]:
        fragment_scf_data = {}
        patterns = {
            'Steps': r'\*\*\* SCF run converged in\s+(\d+) steps \*\*\*',
            'Overlap energy': r'Overlap energy of the core charge distribution:\s+([-\d.]+)',
            'Self energy': r'Self energy of the core charge distribution:\s+([-\d.]+)',
            'Core Hamiltonian energy': r'Core Hamiltonian energy:\s+([-\d.]+)',
            'Hartree energy': r'Hartree energy:\s+([-\d.]+)',
            'XC energy': r'Exchange-correlation energy:\s+([-\d.]+)',
            'Total energy': r'Total energy:\s+([-\d.]+)',
            'Cube file': r'The electron density is written in cube file format to the file:\s*([\w.-]+)'
        }

        scf_block_pattern = re.compile(
            r'\*\*\* SCF run converged.*?'
            r'(Mulliken Population Analysis)',
            re.DOTALL
        )

        for scf_block in scf_block_pattern.finditer(log_content):
            scf_data = {}
            block_content = scf_block.group(0)

            for key, pattern in patterns.items():
                match = re.search(pattern, block_content)
                if match:
                    if key == 'Steps':
                        scf_data[key] = int(match.group(1))
                    elif key == 'Cube file':
                        scf_data[key] = match.group(1)
                        frag_num = re.search(r'frag(\d+)', match.group(1)).group(1)
                    else:
                        scf_data[key] = float(match.group(1))

            if 'Cube file' in scf_data:
                frag_key = f"SCFs frag {frag_num}"
                if frag_key not in fragment_scf_data:
                    fragment_scf_data[frag_key] = []
                fragment_scf_data[frag_key].append(scf_data)

        return fragment_scf_data

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

    def extract_fragment_energies_after_scf(self, scf_data: List[Dict[str, float]]) -> Dict[str, float]:
        """
        Extracts fragment energies from the latest iteration of the FAT SCF.
        """
        last_iteration = max(scf_data, key=lambda x: x['i_iter'])
        frag_energies = {}
        for entry in scf_data:
            if entry['i_iter'] == last_iteration['i_iter']:
                frag_energies[f"tot energy frag {entry['i_frag']}"] = entry['tot']
        return frag_energies

    def extract_fat_energy_contributions(self, log_content: str) -> Dict[str, Union[float, List[float]]]:
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

    def process_cp2k_fat_log(self, log_file_path: str) -> Dict[str, Any]:
        """Processes CP2K FAT log file and extracts data."""
        result: Dict[str, Any] = {
            "logfile": os.path.abspath(log_file_path)
        }
        with open(log_file_path, 'r', encoding="utf-8") as f:
            log_content = f.read()

        energy = self.extract_energy_cp2k(log_content)
        if energy is not None:
            result["fat total energy"] = energy

        scf_data = self.extract_scf_data(log_content)
        result["fat scf data"] = scf_data
        result.update(self.extract_fat_energy_contributions(log_content))
        result.update(self.extract_fragment_energies_after_scf(scf_data))
        result.update(self.extract_fragment_scf_data(log_content))

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

    def process_cp2k_log(self, log_file_path: str) -> Dict[str, Any]:
        """Processes CP2K log file and extracts energy data."""
        result: Dict[str, Any] = {
            "logfile": os.path.abspath(log_file_path)
        }
        with open(log_file_path, 'r', encoding="utf-8") as f:
            log_content = f.read()

        energy_patterns = {
            "overlap energy": r"Overlap energy of the core charge distribution:\s+([-\d.]+)",
            "self energy": r"Self energy of the core charge distribution:\s+([-\d.]+)",
            "core hamiltonian energy": r"Core Hamiltonian energy:\s+([-\d.]+)",
            "hartree energy": r"Hartree energy:\s+([-\d.]+)",
            "exchange correlation energy": r"Exchange-correlation energy:\s+([-\d.]+)",
            "total energy": r"Total energy:\s+([-\d.]+)",
        }

        for key, pattern in energy_patterns.items():
            match = re.search(pattern, log_content)
            if match:
                result[key] = float(match.group(1))

        return result

    def process_cp2k_fat_directory(self, config: Dict):
        """Processes a directory with CP2K calculations."""
        root_dir = config['root dir']
#       spec = config['spec']
        for dirpath, _, _ in os.walk(root_dir):
            xyz_dir = os.path.join(dirpath, f"{os.path.basename(dirpath)}_xyz")
            if os.path.exists(xyz_dir):
                xyz_file = next(
                    (f for f in os.listdir(xyz_dir) if f == 'tot.xyz'),
                    None
                )
                if xyz_file:
                    with open(os.path.join(xyz_dir, xyz_file),
                              'r',
                              encoding="utf-8") as f:
                        xyz_content = f.read()
                    distance = self.extract_distance(xyz_content)

                    for root, _, files in os.walk(dirpath):
                        log_files = [f for f in files if f.endswith('.log')]
                        log_files = [f for f in files if (f.endswith('.log') and not f.startswith("dft1_"))]
                        for log_file in log_files:
                            log_file_path = os.path.join(root, log_file)
                            result = self.process_cp2k_fat_log(log_file_path)
                            result["distance"] = distance

                            calc_type = os.path.basename(root)
                            if calc_type not in self.results["calculations"]:
                                self.results["calculations"][calc_type] = []
                            self.results["calculations"][calc_type].append(result)

    def process_cp2k_directory(self, config: Dict):
        """Processes a directory with CP2K calculations."""
        root_dir = config['root dir']
        spec = config['spec']
        for dirpath, _, filenames in os.walk(root_dir):
            base_dir = os.path.basename(dirpath)
            xyz_dir = os.path.join(dirpath, f"{base_dir}_xyz")
            if os.path.exists(xyz_dir):
                xyz_file = next(
                    (f for f in os.listdir(xyz_dir) if f == 'tot.xyz'),
                    None
                )
                if xyz_file:
                    with open(os.path.join(xyz_dir, xyz_file),
                              'r',
                              encoding="utf-8") as f:
                        xyz_content = f.read()
                    distance = self.extract_distance(xyz_content)

                    for root, _, files in os.walk(dirpath):
                        log_files = [f for f in files if f.endswith('.log')]
                        if spec is not None:
                            log_files = [f for f in files if (f.endswith('.log') and f.startswith(spec))]
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
    """ args parser."""
    parser = argparse.ArgumentParser(
        description="Extract energy information from log files."
    )
    parser.add_argument(
        "input",
        help="Input directory with log files or subdirectories"
    )
    parser.add_argument(
        "--type",
        choices=['molcas', 'fat', 'cp2k'],
        required=True,
        help="type of calculation"
    )
    parser.add_argument(
        "--spec",
        type=str,
        default=None,
        help="specific folder of calculation"
    )
    return parser.parse_args()


def main():
    """Main function to run the result extraction process."""
    args = parse_args()

    if not os.path.isdir(args.input):
        print(f"Error: {args.input} is not a valid directory.")
        return

    config = {
        "root dir": args.input,
        "output file": f"{args.type}_results.json",
        "spec": args.spec
    }
    extractor = ResultExtractor(config)

    if args.type == 'molcas':
        extractor.process_molcas_directory(config["root dir"])
    elif args.type == 'fat':
        extractor.process_cp2k_fat_directory(config)
    elif args.type == 'cp2k':
        extractor.process_cp2k_directory(config)

    extractor.save_results(config["output file"])


if __name__ == "__main__":
    main()
