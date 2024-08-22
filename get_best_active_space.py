#!/usr/bin/env python3

# Developed by Konstantin Komarov.
import os
import json
import argparse
from active_space_chooser import main as active_space_chooser_main

def extract_molecule_info(xyz_file):
    base_name = os.path.splitext(xyz_file)[0]
    molecule, distance = base_name.rsplit('_', 1)
    return molecule, distance

def find_best_active_space(xyz_file):
    molecule, distance = extract_molecule_info(xyz_file)
    base_folder_name = f"{molecule}_{distance}"

    # Get all CASSCF calculation folders
    folders = [f for f in os.listdir() if f.startswith(base_folder_name) and os.path.isdir(f)]

    # Prepare arguments for active_space_chooser
    mr_files = [os.path.join(folder, f"{folder}.log") for folder in folders]

    # Get paths to reference data
    ref_data_folder = "Dipole_moments_reference_data"
    ground_state_ref = os.path.join(ref_data_folder, f"{molecule}_ground_state_dipole.csv")
    excited_state_refs = [
        os.path.join(ref_data_folder, f"{molecule}_excited_state_{i}_dipole.csv")
        for i in range(1, 3)  # Assuming we have data for the first 3 excited states
    ]

#   # Run GDM-AS
#   gdm_args = [
#       "gdm-as",
#       "-m"] + mr_files + [
#       "-r", ground_state_ref
#   ]
#   print(gdm_args)
#   gdm_result = active_space_chooser_main(gdm_args)
    gdm_result = None

    # Run EDM-AS
    edm_args = [
        "edm-as",
        "-m"] + mr_files + [
        "-S", "1", "2",
        "-r"] + excited_state_refs
    print(edm_args)
    edm_result = active_space_chooser_main(edm_args)

    return {
        "GDM-AS": gdm_result,
        "EDM-AS": edm_result
    }

def main():
    parser = argparse.ArgumentParser(description="Find the best active space for a given molecule.")
    parser.add_argument("xyz_file", help="Path to the XYZ file containing the molecule geometry.")
    args = parser.parse_args()

    best_active_spaces = find_best_active_space(args.xyz_file)

    for method in ["GDM-AS", "EDM-AS"]:
        print(f"\nBest active space according to {method}:")
        if best_active_spaces[method] is not None:
            print(f"Electrons: {best_active_spaces[method]['num_electrons']}")
            print(f"Orbitals: {best_active_spaces[method]['num_orbitals']}")
            print(f"File: {best_active_spaces[method]['path']}")
        else:
            print(f"Could not determine best active space for {method}")

if __name__ == "__main__":
    main()
