#!/usr/bin/env python3

import os

import numpy as np


def create_xyz_files(output_dir, distance_bohr):
    BOHR_TO_ANGSTROM = 0.529177249
    distance = distance_bohr * BOHR_TO_ANGSTROM

    water1 = np.array(
        [
            [0.000000000, 0.000000000, 0.000000000],
            [-0.281414990, 0.922296680, 0.000000000],
            [0.959816699, 0.048445268, 0.000000000],
        ]
    )

    water2 = np.array(
        [
            [1.586459417, 0.000000000, 0.000000000],
            [1.793475328, 0.557540054, -0.747754745],
            [1.793475328, 0.557540054, 0.747754745],
        ]
    )

    water2[:, 0] += distance - 1.586459417

    METHOD = "dft"

    os.makedirs(output_dir, exist_ok=True)

    with open(os.path.join(output_dir, "tot.xyz"), "w") as f:
        f.write("6\n")
        f.write(f"Water dimer at d = {distance:.2f} A = {distance_bohr:.1f} Bboohhrr\n")
        for atom in water1:
            f.write(
                f"{'O' if np.all(atom == 0) else 'H'} {atom[0]:.6f} {atom[1]:.6f} {atom[2]:.6f}\n"
            )
        for atom in water2:
            f.write(
                f"{'O' if atom[1] == 0 and atom[2] == 0 else 'H'} {atom[0]:.6f} {atom[1]:.6f} {atom[2]:.6f}\n"
            )

    with open(os.path.join(output_dir, "frag1.xyz"), "w") as f:
        f.write("3\n")
        f.write(
            f"Water dimer fragment 1 at d = {distance:.2f} A = {distance_bohr:.1f} Bboohhrr, method=dft\n"
        )
        for atom in water1:
            f.write(
                f"{'O' if np.all(atom == 0) else 'H'} {atom[0]:.6f} {atom[1]:.6f} {atom[2]:.6f}\n"
            )

    with open(os.path.join(output_dir, "frag2.xyz"), "w") as f:
        f.write("3\n")
        f.write(
            f"Water dimer fragment 2 at d = {distance:.2f} A = {distance_bohr:.1f} Bboohhrr, method={METHOD}\n"
        )
        for atom in water2:
            f.write(
                f"{'O' if atom[1] == 0 and atom[2] == 0 else 'H'} {atom[0]:.6f} {atom[1]:.6f} {atom[2]:.6f}\n"
            )


distances = np.concatenate(
    [np.arange(4.2, 5.61, 0.2), np.arange(6.0, 9.1, 1.0)]
).tolist()

output_xyz_dir = "h2o-h2o_xyz"
os.makedirs(output_xyz_dir, exist_ok=True)

for distance in distances:
    output_dir = f"{output_xyz_dir}/h2o-h2o-{distance:.1f}/h2o-h2o-{distance:.1f}_xyz"
    create_xyz_files(output_dir, distance)

print(f"Generated {len(distances)} sets of xyz files in '{output_xyz_dir}' directory.")
