#!/usr/bin/python3
"""Generate XYZ files for H2-H10 dissociation."""

import os

import numpy as np

BOHR_TO_ANGSTER = 0.529177249
ANGSTER_TO_BOHR = 1.8897259886


class XYZGenerator:
    """ gen """
    def __init__(self, config):
        self.config = config
        self.config['output_dir'] = "h2-h10_xyz"
        self.config['h10_coords'] = [
            [-3.333816500, 0.000000000, -0.370424000],
            [-2.592968500, 0.000000000, -0.370424000],
            [-1.852120500, 0.000000000, -0.370424000],
            [-1.111272500, 0.000000000, -0.370424000],
            [-0.370424000, 0.000000000, -0.370424000],
            [0.370424000, 0.000000000, -0.370424000],
            [1.111272500, 0.000000000, -0.370424000],
            [1.852120500, 0.000000000, -0.370424000],
            [2.592968500, 0.000000000, -0.370424000],
            [3.333816500, 0.000000000, -0.370424000],
        ]
        self.config['h2_coords'] = [
            [0.000000000, -0.370424000, 1.852120000],
            [0.000000000, 0.370424000, 1.852120000],
        ]
        self.shift_bohr = (0.370424000 + 1.852120000)*ANGSTER_TO_BOHR
        self.shift_a = 0.370424000 + 1.852120000

    def create_xyz_file(self, filename, distance_bohr):
        """ x """
        distance = distance_bohr*BOHR_TO_ANGSTER
        distance_a_true = distance + self.shift_a
        distance_bohr_true = distance_bohr + self.shift_bohr
        with open(filename, 'w', encoding="utf-8") as file:
            file.write("12\n")
            file.write(f"H2/H10 system at d = {distance_a_true:.2f} A = {distance_bohr_true:.2f} Bboohhrr\n")

            for coord in self.config['h10_coords']:
                file.write(f"H {coord[0]:.9f} {coord[1]:.9f} {coord[2]:.9f}\n")

            for coord in self.config['h2_coords']:
                file.write(f"H {coord[0]:.9f} {coord[1]:.9f} {coord[2]+distance:.9f}\n")

    def generate_xyz_files(self):
        """ x """
        distances_bohr = np.concatenate([
            np.arange(0.0, 1.41, 0.2),
            np.arange(1.8, 4.9, 1.0)
        ]).tolist()

        os.makedirs(self.config['output_dir'], exist_ok=True)

        for distance in distances_bohr:
            distance_bohr = distance + self.shift_bohr
            print(distance_bohr)
            output_subdir = f"{self.config['output_dir']}/h2-h10-{distance_bohr:.1f}"
            os.makedirs(output_subdir, exist_ok=True)
            filename = os.path.join(output_subdir, f"h2-h10-{distance_bohr:.1f}.xyz")
            self.create_xyz_file(filename, distance)

        print(f"Generated {len(distances_bohr)} xyz files in '{self.config['output_dir']}' directory.")


def main():
    "xxx"
    config = {}
    generator = XYZGenerator(config)
    generator.generate_xyz_files()


if __name__ == "__main__":
    main()
