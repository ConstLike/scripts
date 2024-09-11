#!/usr/bin/env python3

import os

import numpy as np

distances = np.concatenate(
    [np.arange(4.2, 5.61, 0.2),
     np.arange(6.0, 9.1, 1.0)]
).tolist()

OUTPUT_XYZ_DIR = "h2-h10_xyz"
METHOD = "wf"

os.makedirs(OUTPUT_XYZ_DIR, exist_ok=True)


BOHR_TO_ANGSTER = 0.529177249
H10_CHAIN_DISTANCE = 1.4*BOHR_TO_ANGSTER
H2_DISTANCE = 1.4*BOHR_TO_ANGSTER

for distance_bohr in distances:
    output_dir = f"""{OUTPUT_XYZ_DIR}/h2-h10\
-{distance_bohr:.1f}/h2-h10-{distance_bohr:.1f}_xyz"""
    os.makedirs(output_dir, exist_ok=True)

    filename_tot = os.path.join(output_dir, "tot.xyz")
    filename_frag1 = os.path.join(output_dir, "frag1.xyz")
    filename_frag2 = os.path.join(output_dir, "frag2.xyz")

    distance = distance_bohr*BOHR_TO_ANGSTER

    with open(filename_tot, 'w', encoding="utf-8") as file:
        file.write("12\n")
        file.write(f"""H2/H10 system at d = {distance:.2f} A \
= {distance_bohr:.1f} Bboohhrr\n""")

        for i in range(10):
            file.write(f"H {i * H10_CHAIN_DISTANCE:.6f} 0.000000 0.000000\n")

        CENTER_X = H10_CHAIN_DISTANCE*4 + H10_CHAIN_DISTANCE/2

        file.write(f"H {CENTER_X:.6f} {-H2_DISTANCE/2:.6f} {distance:.6f}\n")
        file.write(f"H {CENTER_X:.6f} {+H2_DISTANCE/2:.6f} {distance:.6f}\n")

    with open(filename_frag1, 'w', encoding='utf-8') as file:
        file.write("8\n")
        file.write(f"""H2/H10 system at d = {distance:.2f} A \
= {distance_bohr:.1f} Bboohhrr, method=dft\n""")

        for i in range(4):
            file.write(f"H {i * H10_CHAIN_DISTANCE:.6f} 0.000000 0.000000\n")
        for i in range(6, 10):
            file.write(f"H {i * H10_CHAIN_DISTANCE:.6f} 0.000000 0.000000\n")

    with open(filename_frag2, 'w', encoding='utf-8') as file:
        file.write("4\n")
        file.write(f"""H2/H10 system at d = {distance:.2f} A \
= {distance_bohr:.1f} Bboohhrr, method={METHOD}\n""")

        file.write(f"H {4 * H10_CHAIN_DISTANCE:.6f} 0.000000 0.000000\n")
        file.write(f"H {5 * H10_CHAIN_DISTANCE:.6f} 0.000000 0.000000\n")

        CENTER_X = H10_CHAIN_DISTANCE*4 + H10_CHAIN_DISTANCE/2

        file.write(f"H {CENTER_X:.6f} {-H2_DISTANCE/2:.6f} {distance:.6f}\n")
        file.write(f"H {CENTER_X:.6f} {+H2_DISTANCE/2:.6f} {distance:.6f}\n")

print(f"Generated {len(distances)} xyz files in '{OUTPUT_XYZ_DIR}' directory.")
