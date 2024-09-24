#!/usr/bin/env python3
"""Generate XYZ files for H2-H10 embed dissociation."""

import os

import numpy as np

BOHR_TO_ANGSTER = 0.529177249
ANGSTER_TO_BOHR = 1.8897259886


class XYZGenerator:
    """Generator for H2-H10 embed dissociation XYZ files."""

    def __init__(self, config):
        self.config = config
        self.config['frag1'] = [
            [-3.333816500, 0.000000000, -0.370424000],
            [-2.592968500, 0.000000000, -0.370424000],
            [-1.852120500, 0.000000000, -0.370424000],
            [-1.111272500, 0.000000000, -0.370424000],
            [1.111272500, 0.000000000, -0.370424000],
            [1.852120500, 0.000000000, -0.370424000],
            [2.592968500, 0.000000000, -0.370424000],
            [3.333816500, 0.000000000, -0.370424000],
        ]
        self.config['frag2'] = [
            [-0.370424000, 0.000000000, -0.370424000],
            [0.370424000, 0.000000000, -0.370424000],
            [0.000000000, -0.370424000, 1.852120000],
            [0.000000000, 0.370424000, 1.852120000],
        ]
        self.config['tot'] = self.config['frag1'] + self.config['frag2']
        self.shift_bohr = (0.370424000 + 1.852120000)*ANGSTER_TO_BOHR
        self.shift_a = 0.370424000 + 1.852120000

    def create_xyz_file(self, filename, coords, num_atoms, distance_bohr ):
        """Create XYZ file with given coordinates and parameters."""
        distance = distance_bohr*BOHR_TO_ANGSTER
        dist_a_true = distance + self.shift_a
        dist_bohr_true = distance_bohr + self.shift_bohr
        with open(filename, 'w', encoding="utf-8") as file:
            file.write(f"{num_atoms}\n")
            file.write(f"H2/H10 system at d = {dist_a_true:.2f} A = {dist_bohr_true:.2f} "
                       f"Bboohhrr\n")
            for coord in coords:
                file.write(f"H {coord[0]:.9f} {coord[1]:.9f} {coord[2]:.9f}\n")

    def generate_xyz_files(self):
        """Generate XYZ files for various distances."""
        distances_bohr = np.concatenate([
            np.arange(0.0, 1.41, 0.2),
            np.arange(1.8, 4.9, 1.0)
        ]).tolist()

        for distance in distances_bohr:
            distance_bohr = distance + self.shift_bohr
            output_dir = (f"{self.config['output dir']}/h2-h10-{distance_bohr:.1f}/"
                          f"h2-h10-{distance_bohr:.1f}_xyz")
            os.makedirs(output_dir, exist_ok=True)

            frag2_coords = self.config['frag2'].copy()
            frag2_coords[2][2] = 1.852120000 + distance * BOHR_TO_ANGSTER
            frag2_coords[3][2] = 1.852120000 + distance * BOHR_TO_ANGSTER

            tot_coords = self.config['frag1'] + frag2_coords

            self.create_xyz_file(
                os.path.join(output_dir, "tot.xyz"),
                tot_coords,
                12,
                distance
            )
            self.create_xyz_file(
                os.path.join(output_dir, "frag1.xyz"),
                self.config['frag1'],
                8,
                distance
            )
            self.create_xyz_file(
                os.path.join(output_dir, "frag2.xyz"),
                frag2_coords,
                4,
                distance
            )

        print(f"Generated {len(distances_bohr)} xyz files in '{self.config['output dir']}'.")


def main():
    """Main function to run the XYZ generator."""
    config = {
        "output dir": "h2-h10_xyz"
    }
    generator = XYZGenerator(config)
    generator.generate_xyz_files()


if __name__ == "__main__":
    main()
