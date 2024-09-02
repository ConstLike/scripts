#!/usr/bin/env python3

import os
import numpy as np

def create_xyz_file(filename, distance_bohr):
    BOHR_TO_ANGSTROM = 0.529177249
    h10_chain_distance = 1.4*BOHR_TO_ANGSTROM
    h2_distance = 1.4*BOHR_TO_ANGSTROM
    distance = distance_bohr*BOHR_TO_ANGSTROM

    with open(filename, 'w') as file:
        file.write("12\n")
        file.write(f"H2/H10 system at d = {distance:.2f} A = {distance_bohr:.1f} Bboohhrr\n")

        for i in range(10):
            file.write(f"H {i * h10_chain_distance:.6f} 0.000000 0.000000\n")

        center_x = h10_chain_distance*4 + h10_chain_distance/2

        file.write(f"H {center_x:.6f} {-h2_distance/2:.6f} {distance:.6f}\n")
        file.write(f"H {center_x:.6f} {+h2_distance/2:.6f} {distance:.6f}\n")


distances = np.concatenate([np.arange(4.2, 5.61, 0.2), np.arange(6.0, 9.1, 1.0)]).tolist()

output_xyz_dir = "h2-h10_xyz"
os.makedirs(output_xyz_dir, exist_ok=True)

for distance in distances:
    output_dir = f"{output_xyz_dir}/h2-h10-{distance:.1f}"
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(output_dir, f"h2-h10-{distance:.1f}.xyz")
    create_xyz_file(filename, distance)

print(f"Generated {len(distances)} xyz files in '{output_xyz_dir}' directory.")
