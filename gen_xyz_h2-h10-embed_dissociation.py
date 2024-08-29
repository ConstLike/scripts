#!/usr/bin/env python3

import os
import numpy as np

distances = np.concatenate([np.arange(4.2, 5.61, 0.2), np.arange(6.0, 9.1, 1.0)]).tolist()

output_xyz_dir = "h2-h10_xyz"
os.makedirs(output_xyz_dir, exist_ok=True)


BOHR_TO_ANGSTER = 0.529177249
h10_chain_distance = 1.4*BOHR_TO_ANGSTER
h2_distance = 1.4*BOHR_TO_ANGSTER

for distance_bohr in distances:
    output_dir = f"{output_xyz_dir}/h2-h10-{distance_bohr:.1f}/h2-h10-{distance_bohr:.1f}_xyz"
    os.makedirs(output_dir, exist_ok=True)

    filename_tot = os.path.join(output_dir, f"tot.xyz")
    filename_frag1 = os.path.join(output_dir, f"frag1.xyz")
    filename_frag2 = os.path.join(output_dir, f"frag2.xyz")

    distance = distance_bohr*BOHR_TO_ANGSTER

    with open(filename_tot, 'w') as file:
        file.write("12\n")
        file.write(f"H2/H10 system at d = {distance:.2f} A = {distance_bohr:.1f} Bohr\n")

        for i in range(10):
            file.write(f"H {i * h10_chain_distance:.6f} 0.000000 0.000000\n")

        center_x = h10_chain_distance*4 + h10_chain_distance/2

        file.write(f"H {center_x:.6f} {-h2_distance/2:.6f} {distance:.6f}\n")
        file.write(f"H {center_x:.6f} {+h2_distance/2:.6f} {distance:.6f}\n")

    with open(filename_frag1, 'w') as file:
        file.write("8\n")
        file.write(f"H2/H10 system at d = {distance:.2f} A = {distance_bohr:.1f} Bohr, method=dft\n")

        for i in range(4):
            file.write(f"H {i * h10_chain_distance:.6f} 0.000000 0.000000\n")
        for i in range(6,10):
            file.write(f"H {i * h10_chain_distance:.6f} 0.000000 0.000000\n")

    with open(filename_frag2, 'w') as file:
        file.write("4\n")
        file.write(f"H2/H10 system at d = {distance:.2f} A = {distance_bohr:.1f} Bohr, method=wf\n")

        file.write(f"H {4 * h10_chain_distance:.6f} 0.000000 0.000000\n")
        file.write(f"H {5 * h10_chain_distance:.6f} 0.000000 0.000000\n")

        center_x = h10_chain_distance*4 + h10_chain_distance/2

        file.write(f"H {center_x:.6f} {-h2_distance/2:.6f} {distance:.6f}\n")
        file.write(f"H {center_x:.6f} {+h2_distance/2:.6f} {distance:.6f}\n")

print(f"Generated {len(distances)} xyz files in '{output_xyz_dir}' directory.")
