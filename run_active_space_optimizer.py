#!/usr/bin/env python3

# Developed by Konstantin Komarov.
import os
import subprocess
import argparse
import json
import io
import sys
from contextlib import redirect_stdout
from typing import List, Tuple, Optional
from active_space_chooser import main as active_space_chooser_main
from gen_molcas_inputs import MolcasInputGenerator


class ActiveSpaceOptimizer:
    def __init__(self, xyz_file: str, num_states: int, initial_active_space: Tuple[int, int], max_iterations: int, error_threshold: float):
        self.xyz_file = xyz_file
        self.num_states = num_states
        self.initial_active_space = initial_active_space
        self.current_active_space = initial_active_space
        self.max_iterations = max_iterations
        self.error_threshold = error_threshold
        self.molecule_name = os.path.splitext(os.path.basename(xyz_file))[0]
        self.basis_set = "ANO-L-VDZP"  # Default basis set
        self.reference_dipoles = [0.0000, 1.1826, 0.0463, 1.6553]

    def run_optimization(self) -> Optional[Tuple[int, int]]:
        best_error = float('inf')
        best_active_space = self.initial_active_space

        for iteration in range(self.max_iterations):
            print(f"Iteration {iteration + 1}: Testing active space {self.current_active_space}")

            generator = MolcasInputGenerator(self.xyz_file, self.basis_set,
                                             self.current_active_space[0], self.current_active_space[1])
            generator.read_xyz()
            generator.generate_input_file()

            log_file = self.run_molcas_calculation(generator.general_name)

            if log_file is None:
                print(f"Molcas calculation failed for {self.current_active_space}")
                self.current_active_space = (self.current_active_space[0] + 2, self.current_active_space[1] + 2)
                continue

            new_active_space, error, calculated_dipoles = self.run_active_space_chooser(log_file)

            if error < best_error:
                best_error = error
                best_active_space = new_active_space

            print(f"Current error: {error}, Best error: {best_error}")
            print(f"Reference dipoles: {self.reference_dipoles[1:]}")
            print(f"Calculated dipoles: {calculated_dipoles}")

            if error <= self.error_threshold:
                print(f"Error below threshold. Best active space: {best_active_space}")
                return best_active_space

            if new_active_space == self.current_active_space:
                self.current_active_space = (self.current_active_space[0] + 2, self.current_active_space[1] + 2)
            else:
                self.current_active_space = new_active_space

        print(f"Maximum iterations reached. Best active space found: {best_active_space}")
        return best_active_space

    def run_molcas_calculation(self, input_name: str) -> str:
        input_dir = os.path.join(os.getcwd(), input_name)
        input_file = f"{input_name}.input"
        log_file = f"{input_name}.log"

        current_dir = os.getcwd()
        os.chdir(input_dir)

        try:
            subprocess.run(['pymolcas', input_file], stdout=open(log_file, 'w'), stderr=subprocess.STDOUT, check=True)
        except subprocess.CalledProcessError:
            print(f"Molcas calculation failed for {input_name}")
            os.chdir(current_dir)
            return None

        os.chdir(current_dir)
        return os.path.join(input_dir, log_file)

    def run_active_space_chooser(self, log_file: str) -> Tuple[Tuple[int, int], float, List[float]]:
        print(f"Running active_space_chooser for log file: {log_file}")

        ref_dir = 'reference_data'
        os.makedirs(ref_dir, exist_ok=True)
        ref_files = []
        for i, dipole in enumerate(self.reference_dipoles[1:], start=1):
            ref_file = os.path.join(ref_dir, f'excited_state_{i}_dipole.csv')
            with open(ref_file, 'w') as f:
                f.write("Excited_State_Dipole\n")
                f.write(f"{dipole}\n")
            ref_files.append(ref_file)

        args = ['edm-as', '-m', log_file, '-r'] + ref_files + ['-S'] + [str(i) for i in range(1, len(self.reference_dipoles))]
        print(f"active_space_chooser arguments: {args}")

        f = io.StringIO()
        with redirect_stdout(f):
            active_space_chooser_main(args)
        output = f.getvalue()
        print(f"active_space_chooser output: {output}")

        for file in ref_files:
            os.remove(file)
        os.rmdir(ref_dir)

        try:
            # Parse the output to extract calculated dipoles
            calculated_dipoles = []
            for line in output.split('\n'):
                if line.startswith(os.path.basename(log_file)):
                    dipoles = line.split('->')[1].split('err')[0].strip()
                    calculated_dipoles = [float(d) for d in dipoles.split()]

            result_dict = json.loads(output.strip().split('\n')[-1])
            new_active_space = (result_dict['num_electrons'], result_dict['num_orbitals'])

            # Calculate error as the maximum absolute difference
            error = max(abs(calc - ref) for calc, ref in zip(calculated_dipoles, self.reference_dipoles[1:]))

            print(f"New active space suggested: {new_active_space}, Error: {error}")
            return new_active_space, error, calculated_dipoles
        except Exception as e:
            print(f"Error parsing active_space_chooser output: {e}")
            print(f"Returning current active space: {self.current_active_space}")
            return self.current_active_space, float('inf'), []


def main():
    parser = argparse.ArgumentParser(description="Optimize active space for a molecule")
    parser.add_argument("xyz_file", help="Path to the XYZ file")
    parser.add_argument("--num_states", type=int, default=4, help="Number of states to consider (including ground state)")
    parser.add_argument("--initial_active_space", nargs=2, type=int, default=[6, 6],
                        help="Initial active space (e.g., --initial_active_space 6 6)")
    parser.add_argument("--max_iterations", type=int, default=15, help="Maximum number of iterations")
    parser.add_argument("--error_threshold", type=float, default=0.1, help="Error threshold for convergence")

    args = parser.parse_args()

    optimizer = ActiveSpaceOptimizer(args.xyz_file, args.num_states, tuple(args.initial_active_space),
                                     args.max_iterations, args.error_threshold)
    best_active_space = optimizer.run_optimization()
    if best_active_space:
        print(f"Optimization completed. Best active space: {best_active_space}")
    else:
        print("Optimization failed to find a valid active space.")


if __name__ == "__main__":
    main()
