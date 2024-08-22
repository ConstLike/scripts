#!/usr/bin/env python3

# Developed by Konstantin Komarov.
import os
import csv
import re

class ReferenceData:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.energies = {}
        self.dipoles = {}
        self.parse_reference_data()

    def parse_reference_data(self):
        with open(self.file_path, 'r') as file:
            summary_table_found = False
            it_is_rhf_calculation = False
            state = 0
            energy = 0.0
            for line in file:
                if "SCF type = RHF" in line:
                    it_is_rhf_calculation = True
                    state = 1
                    continue
                if it_is_rhf_calculation and "TOTAL energy =" in line:
                    energy_match = re.search(r"TOTAL energy =\s+(-\d+\.\d+)", line)
                    if energy_match:
                        energy = float(energy_match.group(1))
                if it_is_rhf_calculation and "electric dipole (Debye):" in line:
                    next(file)
                    next_line = next(file)
                    dipole_match = re.findall(r"[-+]?\d*\.\d+|\d+", next_line)
                    if len(dipole_match) >= 3:
                        dipole_x = float(dipole_match[0])
                        dipole_y = float(dipole_match[1])
                        dipole_z = float(dipole_match[2])

                        self.energies[state] = energy
                        self.dipoles[state] = (dipole_x, dipole_y, dipole_z)

                if "Summary table" in line:
                    summary_table_found = True
                    continue
                if summary_table_found:
                    match = re.match(r'\s*(\d+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+E[+-]\d+)\s+(-?\d+\.\d+E[+-]\d+)\s+(-?\d+\.\d+E[+-]\d+)', line)

                    if match:
                        state = int(match.group(1))
                        energy = float(match.group(2))
                        dipole_x = float(match.group(6))
                        dipole_y = float(match.group(7))
                        dipole_z = float(match.group(8))

                        self.energies[state] = energy
                        self.dipoles[state] = (dipole_x, dipole_y, dipole_z)

    def get_dipole_magnitude(self, state: int) -> float:
        if state in self.dipoles:
            x, y, z = self.dipoles[state]
            return (x**2 + y**2 + z**2)**0.5
        return 0.0

    def write_csv_files(self, output_dir: str, molecule_name: str):
        os.makedirs(output_dir, exist_ok=True)

        # Write ground state dipole
        ground_state_file = os.path.join(output_dir, f"{molecule_name}_ground_state_dipole.csv")
        with open(ground_state_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Ground_State_Dipole'])
            writer.writerow([self.get_dipole_magnitude(1)])  # State 1 is ground state

        # Write excited states dipoles
        if self.dipoles.keys():
            excited_state_file = os.path.join(output_dir, f"{molecule_name}_excited_state_dipole.csv")
            for state in range(2, max(self.dipoles.keys()) + 1):
                with open(excited_state_file, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Excited_State_Dipole'])
                    writer.writerow([self.get_dipole_magnitude(state)])

def process_directory(directory: str):
    import glob
    output_dir = 'Dipole_moments_reference_data'
    os.makedirs(output_dir, exist_ok=True)

    log_files = glob.glob(os.path.join(directory, '*.log'))

    if log_files:
        log_file = log_files[0]  # Take the first log file if multiple exist
        molecule_name = os.path.basename(directory).split('_')[1]
        extractor = ReferenceData(log_file)
        extractor.write_csv_files(output_dir, molecule_name)
        print(f"Processed {molecule_name}")
        return True
    else:
        print(f"No log file found in {directory}")
        return False

def main():
    import argparse
    import sys
    parser = argparse.ArgumentParser(description='Generate CSV files with dipole moments for a molecule.')
    parser.add_argument('directory', type=str, help='Path to the directory containing the log file.')
    args = parser.parse_args()

    if not os.path.isdir(args.directory):
        print(f"Error: {args.directory} is not a valid directory.")
        sys.exit(1)

    if process_directory(args.directory):
        print(f"Dipole moment CSV files have been written to Dipole_moments_reference_data")
    else:
        print("Failed to process the directory.")


if __name__ == '__main__':
    main()
