#!/usr/bin/env python3

# Developed by Konstantin Komarov.
import argparse
import json
import subprocess
import time
from typing import List, Tuple

import numpy as np


class CP2KInputGenerator:
    def __init__(self, xyz_file: str, basis_set: str, functional: str, pseudo: str):
        self.xyz_file = xyz_file
        self.basis_set = basis_set
        self.functional = functional
        self.pseudo = pseudo

    def generate_input(self, cutoff: float, rel_cutoff: float) -> str:

        input_content = f"""&GLOBAL
  PROJECT cutoff_optimization
  RUN_TYPE ENERGY
  PRINT_LEVEL MEDIUM
&END GLOBAL
&FORCE_EVAL
  METHOD Quickstep
  &DFT
    BASIS_SET_FILE_NAME GTH_BASIS_SETS
    POTENTIAL_FILE_NAME GTH_POTENTIALS
    &MGRID
      NGRIDS 4
      CUTOFF {cutoff}
      REL_CUTOFF {rel_cutoff}
    &END MGRID
    &QS
      METHOD GPW
      EPS_DEFAULT 1.0E-10
    &END QS
    &SCF
      SCF_GUESS ATOMIC
      EPS_SCF 1.0E-8
      MAX_SCF 30
#     ADDED_MOS 10
#     CHOLESKY INVERSE
#     IGNORE_CONVERGENCE_FAILURE TRUE
      &MIXING
        METHOD PULAY_MIXING
        ALPHA 0.3
      &END MIXING
      &DIAGONALIZATION
        ALGORITHM STANDARD
      &END DIAGONALIZATION
    &END SCF
    &XC
      &XC_FUNCTIONAL {self.functional}
      &END XC_FUNCTIONAL
    &END XC
  &END DFT
  &SUBSYS
    &CELL
      ABC 10.0 10.0 10.0
    &END CELL
    &TOPOLOGY
      COORD_FILE_NAME {self.xyz_file}
      COORD_FILE_FORMAT XYZ
    &END TOPOLOGY
    &KIND DEFAULT
      BASIS_SET {self.basis_set}
      POTENTIAL {self.pseudo}
    &END KIND
  &END SUBSYS
&END FORCE_EVAL
"""
        return input_content


def run_cp2k(input_file: str) -> Tuple[float, List[int]]:
#   print(f"Running CP2K with input file: {input_file}")
    time.sleep(1)
    result = subprocess.run(['cp2k.sdbg', '-i', input_file], capture_output=True, text=True)
    time.sleep(1)

    output = result.stdout
    error = result.stderr

#   print("CP2K Output:")
#   print(output)

    if error:
        print("CP2K Error:")
        print(error)

    energy_line = next((line for line in output.splitlines() if "ENERGY| Total FORCE_EVAL" in line), None)
    if energy_line is None:
        print("Error: Could not find energy in CP2K output")
        return None, []

    energy = float(energy_line.split()[-1])

    grid_distribution = []
    for line in output.splitlines():
        if "count for grid" in line:
            grid_distribution.append(int(line.split()[4]))

    return energy, grid_distribution


def optimize_cutoff(xyz_file: str, basis_set: str, functional: str, pseudo: str, rel_cutoff: float = 60, convergence_threshold: float = 1e-5):
    input_gen = CP2KInputGenerator(xyz_file, basis_set, functional, pseudo)
    print(f"Convergence threshold in optimization CATOFF: {convergence_threshold:.3E}")

    cutoffs = np.arange(50, 1001, 20)  # Extended range
    results = []
    prev_energy = None

    for cutoff in cutoffs:
        input_content = input_gen.generate_input(cutoff, rel_cutoff)
        time.sleep(1)
        with open('input.inp', 'w', encoding="utf-8") as f:
            f.write(input_content)

        energy, grid_distribution = run_cp2k('input.inp')
        results.append({
            'cutoff': float(cutoff),
            'energy': float(energy),
            'grid_distribution': [int(x) for x in grid_distribution]
        })

        print(f"CUTOFF: {cutoff}, Energy: {energy}")
        print(f"Grid distribution: {grid_distribution}")

        if prev_energy is not None:
            energy_diff = abs(energy - prev_energy)
            if energy_diff < convergence_threshold:
                print(f"Convergence reached at CUTOFF = {cutoff}")
                return results, cutoff

        prev_energy = energy

    print("Warning: Convergence not reached within the given CUTOFF range")
    return results, cutoffs[-1]

def optimize_rel_cutoff(xyz_file: str, basis_set: str, functional: str, pseudo: str,  cutoff: float, convergence_threshold: float = 1e-4):
    input_gen = CP2KInputGenerator(xyz_file, basis_set, functional, pseudo)
    print(f"Convergence threshold in optimization REL_CATOFF: {convergence_threshold:.3E}")

    rel_cutoffs = np.arange(10, 201, 10)  # Extended range just in case
    results = []
    prev_energy = None

    for rel_cutoff in rel_cutoffs:
        input_content = input_gen.generate_input(cutoff, rel_cutoff)
        with open('input.inp', 'w', encoding="utf-8") as f:
            f.write(input_content)

        energy, grid_distribution = run_cp2k('input.inp')
        results.append({
            'rel_cutoff': float(rel_cutoff),
            'energy': float(energy),
            'grid_distribution': [int(x) for x in grid_distribution]
        })

        print(f"REL_CUTOFF: {rel_cutoff}, Energy: {energy}")
        print(f"Grid distribution: {grid_distribution}")

        if prev_energy is not None:
            energy_diff = abs(energy - prev_energy)
            if energy_diff < convergence_threshold:
                print(f"Convergence reached at REL_CUTOFF = {rel_cutoff}")
                return results, rel_cutoff

        prev_energy = energy

    print("Warning: Convergence not reached within the given REL_CUTOFF range")
    return results, rel_cutoffs[-1]

#def optimize_rel_cutoff(xyz_file: str, basis_set: str, functional: str, cutoff: float, convergence_threshold: float = 1e-5):
#    input_gen = CP2KInputGenerator(xyz_file, basis_set, functional)
#
#    rel_cutoffs = np.arange(10, 101, 10)
#    results = []
#    reference_energy = None
#    optimal_rel_cutoff = None
#    best_efficiency = 0
#
#    for rel_cutoff in rel_cutoffs:
#        input_content = input_gen.generate_input(cutoff, rel_cutoff)
#        with open('input.inp', 'w') as f:
#            f.write(input_content)
#
#        energy, grid_distribution = run_cp2k('input.inp')
#        results.append({
#            'rel_cutoff': float(rel_cutoff),
#            'energy': float(energy),
#            'grid_distribution': [int(x) for x in grid_distribution]
#        })
#
#        print(f"REL_CUTOFF: {rel_cutoff}, Energy: {energy}")
#        print(f"Grid distribution: {grid_distribution}")
#
#        if reference_energy is None:
#            reference_energy = energy
#
#        energy_diff = abs(energy - reference_energy)
#
#        # Calculate grid efficiency
#        total_gaussians = sum(grid_distribution)
#        weighted_sum = sum(g * (4**i) for i, g in enumerate(grid_distribution))
#        efficiency = total_gaussians / weighted_sum
#
#        if energy_diff < convergence_threshold and efficiency > best_efficiency:
#            optimal_rel_cutoff = rel_cutoff
#            best_efficiency = efficiency
#
#        # Stop if the finest grid level is empty
#        if grid_distribution[-1] == 0:
#            break
#
#    if optimal_rel_cutoff is None:
#        print("Warning: Stable convergence not reached within the given REL_CUTOFF range")
#        optimal_rel_cutoff = rel_cutoffs[0]  # Choose the lowest value as a safe default
#
#    return results, optimal_rel_cutoff


def parse_args():
    parser = argparse.ArgumentParser(description="cutoff optimization")
    parser.add_argument("xyz_file", help="Path to the XYZ file")
    return parser.parse_args()


def main():
    args = parse_args()

    basis_set = "DZVP-GTH"
    functional = "PBE"
    pseudo = "GTH-PBE"
    convergence_threshold_cutoff = 1e-4
    convergence_threshold_rel_cutoff = 1e-5

    # Optimize CUTOFF
    cutoff_results, optimal_cutoff = optimize_cutoff(args.xyz_file, basis_set, functional, pseudo, convergence_threshold=convergence_threshold_cutoff)
    print(f"Optimal CUTOFF: {optimal_cutoff}")

    # Optimize REL_CUTOFF
    rel_cutoff_results, optimal_rel_cutoff = optimize_rel_cutoff(args.xyz_file, basis_set, functional, pseudo, optimal_cutoff, convergence_threshold=convergence_threshold_rel_cutoff)
    print(f"Optimal REL_CUTOFF: {optimal_rel_cutoff}")

    # Save results
    with open('optimization_results.json', 'w', emcoding="utf-8") as f:
        json.dump({
            'cutoff_optimization': cutoff_results,
            'rel_cutoff_optimization': rel_cutoff_results,
            'optimal_cutoff': float(optimal_cutoff),
            'optimal_rel_cutoff': float(optimal_rel_cutoff)
        }, f, indent=2)


if __name__ == "__main__":
    main()
