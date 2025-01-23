#!/usr/bin/env python3
"""Generate XYZ files for gradient analysis of H2-H10 embedding."""

import os
from typing import Dict, List, Tuple

BOHR_TO_ANGSTER = 0.529177249
ANGSTER_TO_BOHR = 1.8897259886


class GradientXYZGenerator:
    """Generator for H2-H10 embed dissociation XYZ files."""
    def __init__(self, config: Dict):
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

    def create_xyz_file(self, filename: str, coords: List[List[float]],
                        num_atoms: int, distance_bohr: float) -> None:
        """Create XYZ file with given coordinates and parameters."""
        distance = distance_bohr*BOHR_TO_ANGSTER
        dist_a_true = distance + self.shift_a
        dist_bohr_true = distance_bohr + self.shift_bohr

        with open(filename, 'w', encoding="utf-8") as file:
            file.write(f"{num_atoms}\n")
            file.write(f"H2/H10 system at d = {dist_a_true:.2f} A = "
                       f"{dist_bohr_true:.2f} Bboohhrr\n")
            for coord in coords:
                file.write(f"H {coord[0]:.9f} {coord[1]:.9f} {coord[2]:.9f}\n")

    def generate_perturbed_coords(self, base_coords: List[List[float]],
                                  atom_idx: int, coord_idx: int,
                                  sign: int) -> List[List[float]]:
        """Generate perturbed coordinates for gradient calculation."""
        coords = [coord.copy() for coord in base_coords]
        coords[atom_idx][coord_idx] += sign * self.config['step size']
        return coords

    def generate_xyz_files(self):
        """Generate XYZ files for various distances."""
        distances_bohr = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4,
                          1.8, 2.8, 3.8, 4.8]

        for distance in distances_bohr:
            distance_bohr = distance + self.shift_bohr
            output_dir = (f"{self.config['output dir']}/h2-h10-{distance_bohr:.1f}/"
                          f"h2-h10-{distance_bohr:.1f}_xyz")
            os.makedirs(output_dir, exist_ok=True)

            # Base geometry
            frag2_coords = [coord.copy() for coord in self.config['frag2']]
            frag2_coords[2][2] = 1.852120000 + distance * BOHR_TO_ANGSTER
            frag2_coords[3][2] = 1.852120000 + distance * BOHR_TO_ANGSTER
            tot_coords = self.config['frag1'] + frag2_coords

            self.create_xyz_file(
                os.path.join(output_dir, "tot.xyz"),
                tot_coords, 12, distance
            )
            self.create_xyz_file(
                os.path.join(output_dir, "frag1.xyz"),
                self.config['frag1'], 8, distance
            )
            self.create_xyz_file(
                os.path.join(output_dir, "frag2.xyz"),
                frag2_coords, 4, distance
            )

            # Perturbed geometries for numerical gradient
            for atom_idx in range(12):
                for coord_idx in range(3):
                    for sign in [-1, 1]:
                        direction = atom_idx*6 + coord_idx*2 + (sign + 3)//2
                        pert_dir = (f"{self.config['output dir']}/"
                                    f"h2-h10-{distance_bohr:.1f}-{direction}/"
                                    f"h2-h10-{distance_bohr:.1f}-{direction}_xyz")
                        os.makedirs(pert_dir, exist_ok=True)

                        pert_coords = self.generate_perturbed_coords(
                            tot_coords, atom_idx, coord_idx, sign)

                        self.create_xyz_file(
                            os.path.join(pert_dir, "tot.xyz"),
                            pert_coords, 12, distance
                        )

                        if atom_idx < 8:
                            pert_frag1 = self.generate_perturbed_coords(
                                self.config['frag1'],
                                atom_idx, coord_idx, sign)
                            self.create_xyz_file(
                                os.path.join(pert_dir, "frag1.xyz"),
                                pert_frag1, 8, distance
                            )
                            self.create_xyz_file(
                                os.path.join(pert_dir, "frag2.xyz"),
                                frag2_coords, 4, distance
                            )
                        else:
                            self.create_xyz_file(
                                os.path.join(pert_dir, "frag1.xyz"),
                                self.config['frag1'], 8, distance
                            )
                            pert_frag2 = self.generate_perturbed_coords(
                                frag2_coords,
                                atom_idx - 8, coord_idx, sign)
                            self.create_xyz_file(
                                os.path.join(pert_dir, "frag2.xyz"),
                                pert_frag2, 4, distance
                            )


def main():
    """Main function to run the XYZ generator."""
    config = {
        "output dir": "h2-h10_xyz",
        "step size": 0.001
    }
    generator = GradientXYZGenerator(config)
    generator.generate_xyz_files()


if __name__ == "__main__":
    main()
