#!/usr/bin/env python3

import os

import numpy as np


def create_xyz_files(output_dir, distance_bohr):
    BOHR_TO_ANGSTROM = 0.529177249
    distance = distance_bohr * BOHR_TO_ANGSTROM

    nh3_1 = np.array(
        [
            [1.063707543, 0.132669018, 0.000000000],
            [1.422042627, -0.379623480, 0.821852220],
            [1.422042627, -0.379623480, -0.821852220],
            [0.022123586, 0.004602956, 0.000000000],
        ]
    )

    nh3_2 = np.array(
        [
            [-0.975288454, -0.067152858, 0.000000000],
            [-1.398980541, -1.008788022, 0.000000000],
            [-1.347876889, 0.426563886, -0.826863928],
            [-1.347876889, 0.426563886, 0.826863928],
        ]
    )

    METHOD = "wf"

    displacement = nh3_2[0] - nh3_1[0]
    displacement_norm = np.linalg.norm(displacement)
    displacement_unit = displacement / displacement_norm

    nh3_2 += (distance - displacement_norm) * displacement_unit

    os.makedirs(output_dir, exist_ok=True)

    with open(os.path.join(output_dir, "tot.xyz"), "w", encoding="utf-8") as f:
        f.write("8\n")
        f.write(
            f"Ammonia dimer at d = {distance:.2f} A = {distance_bohr:.1f} Bboohhrr\n"
        )
        counter = 0
        for atom in nh3_1:
            f.write(
                f"{'N' if counter == 0 else 'H'} {atom[0]:.6f} {atom[1]:.6f} {atom[2]:.6f}\n"
            )
            counter += 1

        counter = 0
        for atom in nh3_2:
            f.write(
                f"{'N' if counter == 0 else 'H'} {atom[0]:.6f} {atom[1]:.6f} {atom[2]:.6f}\n"
            )
            counter += 1

    with open(os.path.join(output_dir, "frag1.xyz"), "w", encoding="utf-8") as f:
        f.write("4\n")
        f.write(
            f"Ammonia dimer fragment 1 at d = {distance:.2f} A = {distance_bohr:.1f} Bboohhrr, method=dft\n"
        )
        counter = 0
        for atom in nh3_1:
            f.write(
                f"{'N' if counter == 0 else 'H'} {atom[0]:.6f} {atom[1]:.6f} {atom[2]:.6f}\n"
            )
            counter += 1

    with open(os.path.join(output_dir, "frag2.xyz"), "w", encoding="utf-8") as f:
        f.write("4\n")
        f.write(
            f"Ammonia dimer fragment 2 at d = {distance:.2f} A = {distance_bohr:.1f} Bboohhrr, method={METHOD}\n"
        )
        counter = 0
        for atom in nh3_2:
            f.write(
                f"{'N' if counter == 0 else 'H'} {atom[0]:.6f} {atom[1]:.6f} {atom[2]:.6f}\n"
            )
            counter += 1


distances = np.concatenate(
    [np.arange(4.2, 5.61, 0.2), np.arange(6.0, 9.1, 1.0)]
).tolist()

output_xyz_dir = "nh3-nh3_xyz"
os.makedirs(output_xyz_dir, exist_ok=True)

for distance in distances:
    output_dir = f"{output_xyz_dir}/nh3-nh3-{distance:.1f}/nh3-nh3-{distance:.1f}_xyz"
    create_xyz_files(output_dir, distance)

print(f"Generated {len(distances)} sets of xyz files in '{output_xyz_dir}' directory.")
