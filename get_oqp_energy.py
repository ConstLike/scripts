import os
import re
import csv
import argparse


class GroundEnergyExtractor:
    def __init__(self, log_dir):
        self.log_dir = log_dir

    def extract_energy(self, log_file):
        with open(log_file, 'r') as file:
            for line in file:
                if "TOTAL energy =" in line:
                    energy = float(re.search(r"TOTAL energy =\s+(-?\d+\.\d+)", line).group(1))
                    return energy
        return None

    def process_files(self):
        output_csv = f"energy_{self.log_dir}.csv"
        with open(output_csv, 'w', newline='', encoding="utf-8") as csvfile:
            fieldnames = ['Distance (A)', 'Total Energy (a.u.)']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for log_file in sorted(os.listdir(self.log_dir)):
                if log_file.endswith(".log"):
                    distance = float(re.search(r"h2-h10_(\d+\.\d+)", log_file).group(1))
                    energy_hartree = self.extract_energy(os.path.join(self.log_dir, log_file))
                    if energy_hartree is not None:
                        writer.writerow({'Distance (A)': distance, 'Total Energy (a.u.)': energy_hartree})

        print(f"Data has been extracted and saved to {output_csv}")

class ExcitedEnergyExtractor:
    def __init__(self, log_dir):
        self.log_dir = log_dir

    def extract_energy(self, log_file):
        energies = []
        with open(log_file, 'r') as file:
            summary_table_found = False
            for line in file:
                if "Summary table" in line:
                    summary_table_found = True
                    continue

                if summary_table_found:
                    match = re.match(r'\s*(\d+)\s+(-\d+\.\d+)', line)
                    if match:
                        state_number = int(match.group(1))
                        if state_number != 0:
                            energies.append(float(match.group(2)))
        return energies

    def process_files(self):
        output_csv = f"energy_{self.log_dir}.csv"
        with open(output_csv, 'w', newline='', encoding="utf-8") as csvfile:
            fieldnames = ['Distance (A)', 'Total Energy (a.u.)']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for log_file in sorted(os.listdir(self.log_dir)):
                if log_file.endswith(".log"):
                    distance = float(re.search(r"h2h10-(\d+\.\d+)", log_file).group(1))
                    energy_hartree = self.extract_energy(os.path.join(self.log_dir, log_file))
                    if energy_hartree is not None:
                        writer.writerow({'Distance (A)': distance, 'Total Energy (a.u.)': energy_hartree})

        print(f"Data has been extracted and saved to {output_csv}")

def main():
    parser = argparse.ArgumentParser(description="Extract energy data from log files.")
    parser.add_argument("log_dir", help="Directory containing the log files")
    parser.add_argument("--excited", action="store_true", help="Process excited state (default is ground state)")
    args = parser.parse_args()

    extractor = GroundEnergyExtractor(args.log_dir)

    if not args.excited:
        extractor.process_files()
    else:
        print("Processing excited state is not implemented yet.")

if __name__ == "__main__":
    main()
