
#!/usr/bin/env python3

import os

import numpy as np


def create_xyz_file(filename, distance_bohr):
    BOHR_TO_ANGSTROM = 0.529177249
    DISTANCE = distance_bohr * BOHR_TO_ANGSTROM

    water1 = np.array(
        [
            [1.063707543,     0.132669018,     0.000000000],
            [1.422042627,    -0.379623480,     0.821852220],
            [1.422042627,    -0.379623480,    -0.821852220],
            [0.022123586,     0.004602956,     0.000000000],
        ]
    )

    water2 = np.array(
        [
            [-0.975288454,    -0.067152858,     0.000000000],
            [-1.398980541,    -1.008788022,     0.000000000],
            [-1.347876889,     0.426563886,    -0.826863928],
            [-1.347876889,     0.426563886,     0.826863928],
        ]
    )

    water2[:, 0] += DISTANCE - 1.586459417

    with open(filename, "w", encoding="utf-8") as file:
        file.write("6\n")
        file.write(
            f"Water dimer at d = {DISTANCE:.2f} A = {distance_bohr:.1f} Bboohhrr\n"
        )

        for atom in water1:
            file.write(
                f"{'N' if np.all(atom == 0) else 'H'} {atom[0]:.6f} {atom[1]:.6f} {atom[2]:.6f}\n"
            )

        for atom in water2:
            file.write(
                f"{'N' if atom[1] == 0 and atom[2] == 0 else 'H'} {atom[0]:.6f} {atom[1]:.6f} {atom[2]:.6f}\n"
            )


DISTANCES = np.concatenate(
    [np.arange(4.2, 5.61, 0.2), np.arange(6.0, 9.1, 1.0)]
).tolist()

OUTPUT_XYZ_DIR = "nh3-nh3_xyz"
os.makedirs(OUTPUT_XYZ_DIR, exist_ok=True)

for DISTANCE in DISTANCES:
    output_dir = f"{OUTPUT_XYZ_DIR}/nh3-nh3-{DISTANCE:.1f}"
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(output_dir, f"nh3-nh3-{DISTANCE:.1f}.xyz")
    create_xyz_file(filename, DISTANCE)

print(f"Generated {len(DISTANCES)} xyz files in '{OUTPUT_XYZ_DIR}' directory.")