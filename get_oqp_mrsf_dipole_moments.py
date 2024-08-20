#!/usr/bin/env python3

# Developed by Konstantin Komarov.
import os
import csv


class ReferenceData:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.energies = {}
        self.dipoles = {}
        self.parse_reference_data()

    def parse_reference_data(self):
        with open(self.file_path, 'r') as f:
            lines = f.readlines()

        for line in lines:
            if line.strip().startswith("State"):
                continue
            parts = line.split()
            if len(parts) >= 11:
                state = int(parts[0])
                energy = float(parts[1])
                dipole_x, dipole_y, dipole_z = map(float, parts[6:9])
                self.energies[state] = energy
                self.dipoles[state] = (dipole_x, dipole_y, dipole_z)

    def get_dipole_magnitude(self, state: int) -> float:
        if state in self.dipoles:
            x, y, z = self.dipoles[state]
            return (x**2 + y**2 + z**2)**0.5
        return 0.0

    def write_csv_files(self, output_dir: str):
        os.makedirs(output_dir, exist_ok=True)

        # Write ground state dipole
        with open(os.path.join(output_dir, 'ground_state_dipole.csv'), 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Ground_State_Dipole'])
            writer.writerow([self.get_dipole_magnitude(1)])  # Assuming state 1 is ground state

        # Write excited states dipoles
        for state in range(2, max(self.dipoles.keys()) + 1):
            with open(os.path.join(output_dir, f'excited_state_{state-1}_dipole.csv'), 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Excited_State_Dipole'])
                writer.writerow([self.get_dipole_magnitude(state)])


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Generate csv file with dipole moment.')
    parser.add_argument('path', type=str, help='Path to the directory containing log file.')
    args = parser.parse_args()

    path = args.path
    if not os.path.isdir(xyz_dir):
        print(f"Error: {xyz_dir} is not a valid directory.")
        exit(1)
    extractor_dipole =ReferenceData(path)

if __name__ == '__main__':
    main()
