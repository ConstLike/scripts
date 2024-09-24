""" Input Utility."""
import os
from typing import Dict, List, Tuple


class InputUtils:
    """Utility class for processing XYZ files and related operations."""

    @staticmethod
    def read_xyz_file(xyz_file: str) -> Tuple[int, str, List[str]]:
        """Reads an XYZ file and returns its contents."""
        with open(xyz_file, 'r', encoding="utf-8") as f:
            lines = f.readlines()
        num_atoms = int(lines[0].strip())
        comment = lines[1].strip()
        atoms = []
        for line in lines[2:]:
            parts = line.split()
            if len(parts) == 4:
                atom = parts[0]
                atoms.append(atom)
        return num_atoms, comment, atoms

    @staticmethod
    def get_num_electrons(atoms: List[str]) -> int:
        """Calculates the total number of electrons in the molecule."""
        element_dict = {
            'H': 1, 'He': 2, 'Li': 3, 'Be': 4, 'B': 5, 'C': 6, 'N': 7, 'O': 8,
            'F': 9, 'Ne': 10, 'Na': 11, 'Mg': 12, 'Al': 13, 'Si': 14, 'P': 15,
            'S': 16, 'Cl': 17, 'Ar': 18, 'K': 19, 'Ca': 20, 'Sc': 21, 'Ti': 22,
            'V': 23, 'Cr': 24, 'Mn': 25, 'Fe': 26, 'Co': 27, 'Ni': 28,
            'Cu': 29, 'Zn': 30, 'Ga': 31, 'Ge': 32, 'As': 33, 'Se': 34,
            'Br': 35, 'Kr': 36, 'Rb': 37, 'Sr': 38, 'Y': 39, 'Zr': 40,
            'Nb': 41, 'Mo': 42, 'Tc': 43, 'Ru': 44, 'Rh': 45, 'Pd': 46,
            'Ag': 47, 'Cd': 48, 'In': 49, 'Sn': 50, 'Sb': 51, 'Te': 52,
            'I': 53, 'Xe': 54, 'Cs': 55, 'Ba': 56, 'La': 57, 'Ce': 58,
            'Pr': 59, 'Nd': 60, 'Pm': 61, 'Sm': 62, 'Eu': 63, 'Gd': 64,
            'Tb': 65, 'Dy': 66, 'Ho': 67, 'Er': 68, 'Tm': 69, 'Yb': 70,
            'Lu': 71, 'Hf': 72, 'Ta': 73, 'W': 74, 'Re': 75, 'Os': 76,
            'Ir': 77, 'Pt': 78, 'Au': 79, 'Hg': 80, 'Tl': 81, 'Pb': 82,
            'Bi': 83, 'Po': 84, 'At': 85, 'Rn': 86, 'Fr': 87, 'Ra': 88,
            'Ac': 89, 'Th': 90, 'Pa': 91, 'U': 92, 'Np': 93, 'Pu': 94,
            'Am': 95, 'Cm': 96, 'Bk': 97, 'Cf': 98, 'Es': 99, 'Fm': 100,
            'Md': 101, 'No': 102, 'Lr': 103, 'Rf': 104, 'Db': 105, 'Sg': 106,
            'Bh': 107, 'Hs': 108, 'Mt': 109, 'Ds': 110, 'Rg': 111, 'Cn': 112,
            'Nh': 113, 'Fl': 114, 'Mc': 115, 'Lv': 116, 'Ts': 117, 'Og': 118
        }
        return sum(element_dict.get(atom[0], 0) for atom in atoms)

    @staticmethod
    def get_mol_info(xyz_file: str, config: Dict) -> Dict:
        """Extracts molecule information from XYZ file."""
        num_atoms, comment, atoms = InputUtils.read_xyz_file(xyz_file)
        num_electrons = InputUtils.get_num_electrons(atoms)
        mol_name = os.path.splitext(os.path.basename(xyz_file))[0]
        config.update({
            'mol name': mol_name,
            'num atoms': num_atoms,
            'xyz comment': comment,
            'atom elements': atoms,
            'num electrons': num_electrons
        })
        return config

    @staticmethod
    def get_fragment_files(xyz_dir: str) -> List[str]:
        """Get list of fragment XYZ files."""
        return sorted([f for f in os.listdir(xyz_dir)
                       if f.startswith('frag') and f.endswith('.xyz')])

    @staticmethod
    def get_fragment_info(xyz_dir: str, fragments: List[str]) -> Dict:
        """Get information about fragments."""
        info = {}
        atom_numbers = {
            'H': 1, 'He': 2, 'Li': 3, 'Be': 4, 'B': 5, 'C': 6, 'N': 7, 'O': 8,
            'F': 9, 'Ne': 10, 'Na': 11, 'Mg': 12, 'Al': 13, 'Si': 14, 'P': 15,
            'S': 16, 'Cl': 17, 'Ar': 18, 'K': 19, 'Ca': 20
        }

        def count_electrons(xyz_file):
            total_electrons = 0
            with open(xyz_file, 'r', encoding="utf-8") as file:
                lines = file.readlines()[2:]
                for line in lines:
                    parts = line.split()
                    if len(parts) == 4:
                        atom = parts[0]
                        total_electrons += atom_numbers.get(atom, 0)
            return total_electrons

        for filename in ['tot.xyz'] + fragments:
            file = os.path.join(xyz_dir, filename)
            with open(file, 'r', encoding="utf-8") as f:
                num_atoms = int(f.readline().strip())
            num_electrons = count_electrons(file)

            info[filename] = {
                'atoms': num_atoms,
                'method': 'dft',
                'electrons': num_electrons,
            }

        return info

#  @staticmethod
#  def get_cell_size(atoms: List[Tuple[str, float, float, float]],
#                    padding: float = 5.0) -> Tuple[float, float, float]:
#      """Calculates cell size based on atom coordinates with padding."""
#      if not atoms:
#          return (10.0, 10.0, 10.0)  # Default size if no atoms
#
#      x_coords, y_coords, z_coords = zip(*[(x, y, z) for _, x, y, z in atoms])
#      x_size = max(x_coords) - min(x_coords) + 2 * padding
#      y_size = max(y_coords) - min(y_coords) + 2 * padding
#      z_size = max(z_coords) - min(z_coords) + 2 * padding
#
#      return (x_size, y_size, z_size)
