#!/usr/bin/env python3

# Developed by Konstantin Komarov.
import os
import argparse
import sys


class MolcasInputGenerator:
    def __init__(self, xyz_file, basis_set, active_electrons, active_orbitals):
        self.xyz_file = xyz_file
        self.basis_set = basis_set
        self.active_electrons = active_electrons
        self.active_orbitals = active_orbitals
        self.molecule_name = os.path.splitext(os.path.basename(xyz_file))[0]
        self.num_atoms = 0
        self.num_electrons = 0

    def read_xyz(self):
        with open(self.xyz_file, 'r') as f:
            lines = f.readlines()
        self.num_atoms = int(lines[0].strip())
        self.xyz_content = ''.join(lines[2:])

        # Calculate number of electrons
        elements = [line.split()[0] for line in lines[2:]]
        self.num_electrons = sum(self.get_num_electrons(elem) for elem in elements)

    @staticmethod
    def get_num_electrons(element):
        element_dict = {'H': 1, 'He': 2, 'Li': 3, 'Be': 4, 'B': 5, 'C': 6, 'N': 7, 'O': 8, 'F': 9, 'Ne': 10,
                        'Na': 11, 'Mg': 12, 'Al': 13, 'Si': 14, 'P': 15, 'S': 16, 'Cl': 17, 'Ar': 18}
        return element_dict.get(element, 0)

    def generate_input(self):
        inactive = (self.num_electrons - self.active_electrons) // 2
        n_roots = min(7, self.active_electrons * self.active_orbitals)  # Adjust number of roots based on active space

        input_content = f"""&GATEWAY
  Coord = {self.molecule_name}.xyz
  Basis = {self.basis_set}
  Group = C1

&SEWARD

&SCF

&RASSCF
  Spin = 1
  Symmetry = 1
  nActEl = {self.active_electrons} 0 0
  Inactive = {inactive}
  RAS2 = {self.active_orbitals}
  CIRoot = {n_roots} {n_roots} 1
  LevShift = 0.5

&RASSI
  NrOfJobIphs = 1 {n_roots}
  {' '.join(str(i) for i in range(1, n_roots + 1))}
  XVES
  MEES
  PROP
  3
  'MLTPL  1' 1
  'MLTPL  1' 2
  'MLTPL  1' 3
"""
        return input_content

    def generate_input_file(self):
        output_dir = os.path.join(os.getcwd(), self.molecule_name)
        os.makedirs(output_dir, exist_ok=True)

        # Copy XYZ file to output directory
        with open(self.xyz_file, 'r') as src, open(os.path.join(output_dir, f"{self.molecule_name}.xyz"), 'w') as dst:
            dst.write(src.read())

        input_content = self.generate_input()
        filename = f"{self.molecule_name}_e{self.active_electrons}_o{self.active_orbitals}.input"
        with open(os.path.join(output_dir, filename), 'w') as f:
            f.write(input_content)
        print(f"Generated: {filename}")


def parse_args():
    parser = argparse.ArgumentParser(description="Generate OpenMolcas input file for a specific active space")
    parser.add_argument("xyz_file", help="Path to the XYZ file")
    parser.add_argument("--basis", default="ANO-L-VDZP", help="Basis set to use (default: ANO-L-VDZP)")
    parser.add_argument("--active_space", nargs=2, type=int, default=[2, 2],
                        help="Number of active electrons and orbitals (e.g., --active_space 2 2)")
    return parser.parse_args()


def main():
    args = parse_args()

    if not os.path.exists(args.xyz_file):
        print(f"Error: XYZ file '{args.xyz_file}' not found.")
        sys.exit(1)

    generator = MolcasInputGenerator(args.xyz_file, args.basis, args.active_space[0], args.active_space[1])
    generator.read_xyz()
    generator.generate_input_file()


if __name__ == "__main__":
    main()
