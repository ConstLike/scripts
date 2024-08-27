#!/usr/bin/env python3

# Developed by Konstantin Komarov.
import os
import argparse
from typing import List, Tuple, Dict

class CP2KInputGenerator:
    def __init__(self, config: Dict):
        self.xyz_dir = config['xyz dir']
        self.molecule_name = config['molecule']
        self.basis_set = config['cp2k']['basis set']
        self.dft_functional = config['cp2k']['functional']
        self.kinetic_functional = config['cp2k']['kinetic']
        self.pseudopotential = config['cp2k']['pseudo']
        self.cell_size = config['cell']
        self.fragments = self._get_fragments()
        self.fragment_info = self._get_fragment_info()
        self.total_atoms = self.fragment_info['tot.xyz']['atoms']
        config['info fragments'] = {}
        config['info fragments'] = self.fragment_info

    def _get_fragments(self) -> List[str]:
        return sorted([f for f in os.listdir(self.xyz_dir) if f.startswith('frag') and f.endswith('.xyz')])

    def _get_fragment_info(self) -> Dict[str, Dict[str, int]]:
        info = {}
        atom_numbers= {
            'H': 1, 'He': 2, 'Li': 3, 'Be': 4, 'B': 5, 'C': 6, 'N': 7, 'O': 8, 'F': 9, 'Ne': 10,
            'Na': 11, 'Mg': 12, 'Al': 13, 'Si': 14, 'P': 15, 'S': 16, 'Cl': 17, 'Ar': 18,
            'K': 19, 'Ca': 20, 'Sc': 21, 'Ti': 22, 'V': 23, 'Cr': 24, 'Mn': 25, 'Fe': 26, 'Co': 27, 'Ni': 28,
            'Cu': 29, 'Zn': 30, 'Ga': 31, 'Ge': 32, 'As': 33, 'Se': 34, 'Br': 35, 'Kr': 36,
            'Rb': 37, 'Sr': 38, 'Y': 39, 'Zr': 40, 'Nb': 41, 'Mo': 42, 'Tc': 43, 'Ru': 44, 'Rh': 45, 'Pd': 46,
            'Ag': 47, 'Cd': 48, 'In': 49, 'Sn': 50, 'Sb': 51, 'Te': 52, 'I': 53, 'Xe': 54,
            'Cs': 55, 'Ba': 56, 'La': 57, 'Ce': 58, 'Pr': 59, 'Nd': 60, 'Pm': 61, 'Sm': 62, 'Eu': 63, 'Gd': 64,
            'Tb': 65, 'Dy': 66, 'Ho': 67, 'Er': 68, 'Tm': 69, 'Yb': 70, 'Lu': 71,
            'Hf': 72, 'Ta': 73, 'W': 74, 'Re': 75, 'Os': 76, 'Ir': 77, 'Pt': 78, 'Au': 79, 'Hg': 80,
            'Tl': 81, 'Pb': 82, 'Bi': 83, 'Po': 84, 'At': 85, 'Rn': 86,
            'Fr': 87, 'Ra': 88, 'Ac': 89, 'Th': 90, 'Pa': 91, 'U': 92, 'Np': 93, 'Pu': 94, 'Am': 95, 'Cm': 96,
            'Bk': 97, 'Cf': 98, 'Es': 99, 'Fm': 100, 'Md': 101, 'No': 102, 'Lr': 103,
            'Rf': 104, 'Db': 105, 'Sg': 106, 'Bh': 107, 'Hs': 108, 'Mt': 109, 'Ds': 110, 'Rg': 111, 'Cn': 112,
            'Nh': 113, 'Fl': 114, 'Mc': 115, 'Lv': 116, 'Ts': 117, 'Og': 118
        }
        def count_electrons(xyz_file):
            total_electrons = 0
            with open(xyz_file, 'r') as file:
                lines = file.readlines()[2:]  # Skip the first two lines
                for line in lines:
                    parts = line.split()
                    if len(parts) == 4:
                        atom = parts[0]
                        total_electrons += atom_numbers.get(atom, 0)
            return total_electrons

        for filename in ['tot.xyz'] + self.fragments:
            file = os.path.join(self.xyz_dir, filename)
            with open(file, 'r') as f:
                num_atoms = int(f.readline().strip())
                second_line = f.readline().strip().lower()
                method = 'dft'  # Default method
                if 'method=' in second_line:
                    method = second_line.split('method=')[1].split()[0]

            num_electrons = count_electrons(file)

            info[filename] = {
                    'atoms': num_atoms,
                    'method': method,
                    'electrons': num_electrons,
            }

        return info

    def generate_input(self) -> str:
        input_content = f"""&global
  print_level medium
  project {self.molecule_name}
  run_type energy_force
  callgraph master
&end

&multiple_force_evals
  force_eval_order {' '.join(str(i) for i in range(2, len(self.fragments) + 3))}
  multiple_subsys t
&end

&force_eval
  method embed
  &embed
    embed_method fat
    ngroups 1
    &mapping
      &force_eval 1
        &fragment 1  # Total
          1 {self.total_atoms}
          map 1
        &end
      &end
"""

        for i, frag in enumerate(self.fragments, start=2):
            atoms = self.fragment_info[frag]['atoms']
            input_content += f"""      &force_eval {i}  # fragment {i-1}
        &fragment 1
          1 {atoms}
          map {i}
        &end
      &end
"""

        input_content += f"""      &force_eval_embed
        &fragment 1  # Total
          1 {self.total_atoms}
        &end
"""

        start = 1
        for i, frag in enumerate(self.fragments, start=2):
            atoms = self.fragment_info[frag]['atoms']
            end = start + atoms - 1
            input_content += f"""        &fragment {i}  # Fragment {i-1}
          {start} {end}
        &end
"""
            start = end + 1

        input_content += f"""      &end
    &end
  &end
  &subsys
    &cell
      abc {self.cell_size[0]:.2f} {self.cell_size[1]:.2f} {self.cell_size[2]:.2f}
    &end
    &topology
      coord_file_format xyz
      coord_file_name {self.xyz_dir}/tot.xyz
    &end
  &end
&end

"""

        # Add force_eval sections for total system and fragments
        for i in range(len(self.fragments) + 1):
            input_content += self._generate_force_eval_section(i)

        return input_content

    def _generate_force_eval_section(self, index: int) -> str:


        if index == 0:
            section = """# Total
"""
            filename = 'tot.xyz'
        else:
            filename = self.fragments[index-1]
            method = self.fragment_info[filename]['method'].lower()
            if method == "wf":
                section = f"""# Fragment {index}, WF
"""
            else:
                section = f"""# Fragment {index}, DFT
"""
        method = self.fragment_info[filename]['method'].lower()

        section += """&force_eval
  &dft
    basis_set_file_name GTH_BASIS_SETS
    potential_file_name GTH_POTENTIALS
"""

        if method == "wf":
            section +="""    &qs
      fat_extern t
    &end
"""
        if index == 0:
            section += f"""    &qs
      ref_embed_subsys t
      &opt_embed
        n_iter 50
        dens_conv_max 1e-8
        &xc
          &xc_functional
            &{self.kinetic_functional}
            &end
          &end
        &end
      &end
    &end
"""
        section += f"""    &scf
      eps_scf 1e-8
    &end
    &xc
      &xc_functional {self.dft_functional}
      &end
    &end
"""
        if index != 0:
            section += f"""    &print
      &e_density_cube
        filename frag{index}
        stride 1 1 1
      &end
    &end
"""
        section +=f"""  &end
  &subsys
    &cell
      abc {self.cell_size[0]:.2f} {self.cell_size[1]:.2f} {self.cell_size[2]:.2f}
    &end
    &kind default
      basis_set {self.basis_set}
      potential {self.pseudopotential}
    &end
    &topology
      coord_file_format xyz
      coord_file_name {self.xyz_dir}/{filename}
    &end
  &end
"""
        if index == 0:
            section += """  &print
    &forces
      filename "force_tot"
    &end
  &end
"""
        section += """&end

"""
        return section

    def save_input(self, output_dir: str):
        dir_name = ""
        method = 'wf' if any(info['method'].lower() == 'wf' for info in self.fragment_info.values()) else 'dft'
        file_name = f"{method}-in-dft_{self.molecule_name}_{self.basis_set.lower()}_{self.dft_functional.lower()}_{self.pseudopotential.lower()}"
        output_path = os.path.join(output_dir, dir_name)
        os.makedirs(output_path, exist_ok=True)
        filename = f"{file_name}.inp"
        with open(os.path.join(output_path, filename), 'w') as f:
            f.write(self.generate_input())
        print(f"Generated: {os.path.join(output_path, filename)}")


class OpenMOLCASInputGenerator:
    def __init__(self, config: Dict):
        self.xyz_dir = config['xyz dir']
        self.molecule_name = config['molecule']
        self.basis_set = config['molcas']['basis set']
        self.cell_size = config['cell']
        self.fragment_info = config['info fragments']
        self.wf_fragments = [frag for frag, info in self.fragment_info.items() if info['method'] == 'wf']
        self.min_active_space = [2, 6]
        self.max_active_space = [14, 14]

    def _angstrom_to_au(self, value: float) -> float:
#       return value * 1.8897259886
        return value * 1.8722325

    def generate_active_space(self, num_electrons):

        min_electrons, max_electrons = self.min_active_space[0], self.max_active_space[0]
        min_orbitals, max_orbitals = self.min_active_space[1], self.max_active_space[1]

        active_electrons = min(max(num_electrons, min_electrons), max_electrons)
        active_orbitals = min(max(num_electrons, min_orbitals), max_orbitals)

        space = [active_electrons, active_orbitals]

        return space

    def generate_input(self, fragment_number: str) -> str:
        cell_au = [self._angstrom_to_au(size) for size in self.cell_size]
        grid_origin = [-size/2 for size in cell_au]

        n_electrons = self.fragment_info[f'frag{fragment_number}.xyz']['electrons']
        active_space = self.generate_active_space(n_electrons)
        active_electrons = active_space[0]
        active_orbitals = active_space[1]
        inactive = (n_electrons - active_electrons) // 2

        input_content = f"""> copy $CurrDir/vemb_{fragment_number}.dat $WorkDir
> copy $CurrDir/{self.xyz_dir}/frag{fragment_number}.xyz $WorkDir
&gateway
  title=extern_{fragment_number}
  coord=frag{fragment_number}.xyz
  Basis={self.basis_set}
  group=c1

&seward
  EMBEdding
  EMBInput=vemb_{fragment_number}.dat
  ENDEmbedding

&scf

&rasscf
   Spin=1
   Symmetry=1
   nActEl={active_electrons} 0 0
   Inactive={inactive}
   RAS1=0
   RAS2={active_orbitals}
   RAS3=0
   CIRoot=1 1 1

&grid_it
  name=rasscf
  npoints=107 107 107
  gori
  {grid_origin[0]:.7f} {grid_origin[1]:.7f} {grid_origin[2]:.7f}
  {cell_au[0]:.7f} 0.0 0.0
  0.0 {cell_au[1]:.7f} 0.0
  0.0 0.0 {cell_au[2]:.7f}

&alaska
"""
        return input_content

    def generate_run_script(self, fragment_number: str) -> str:
        script_content = f"""#!/bin/sh
pymolcas extern_{fragment_number}.inp | tee extern_{fragment_number}.out
grep "1 Total energy" extern_{fragment_number}.out | awk '{{ print $8 }}' > extern_{fragment_number}.e
python2 $MOLCAS/Tools/grid2cube/grid2cube.py extern_{fragment_number}.rasscf.lus extern_{fragment_number}_orig.cube
python3 roll_cubefile.py extern_{fragment_number}_orig.cube extern_{fragment_number}.cube

"""
        return script_content

    def generate_roll_cubefile_script(self) -> str:
        return """from sys import argv
import numpy as np
from ase.io.cube import read_cube, write_cube

with open(argv[1]) as f:
    a = read_cube(f)
a["origin"] = np.zeros_like(a["origin"])
nx, ny, nz = a["data"].shape
a["data"] = np.roll(a["data"], (nx//2, ny//2, nz//2), (0, 1, 2))
with open(argv[2], "w") as f:
    write_cube(f, a["atoms"], a["data"], a["origin"])
"""

    def save_input(self, output_dir: str):
        for fragment in self.wf_fragments:
            fragment_number = fragment.split('.')[0].replace('frag', '')

            # Generate and save input file
            input_filename = f"extern_{fragment_number}.inp"
            with open(os.path.join(output_dir, input_filename), 'w') as f:
                f.write(self.generate_input(fragment_number))
            print(f"Generated: {os.path.join(output_dir, input_filename)}")

            # Generate and save run script
            script_filename = f"extern_{fragment_number}.sh"
            with open(os.path.join(output_dir, script_filename), 'w') as f:
                f.write(self.generate_run_script(fragment_number))
            print(f"Generated: {os.path.join(output_dir, script_filename)}")

            # Generate and save run script
            roll_cubefile_filename = "roll_cubefile.py"
            with open(os.path.join(output_dir, roll_cubefile_filename), 'w') as f:
                f.write(self.generate_roll_cubefile_script())
            print(f"Generated: {os.path.join(output_dir, roll_cubefile_filename)}")

#           # Make the script executable
#           os.chmod(os.path.join(output_dir, script_filename), 0o755)

def parse_args():
    parser = argparse.ArgumentParser(description="Generate CP2K input file for embedding theory")
    parser.add_argument("xyz_dir", help="Path to the directory containing XYZ files")
    parser.add_argument("--cell", nargs=3, type=float, default=[10, 10, 10], help="Cell size in Angstroms (e.g. --cell 10 10 10)")
    parser.add_argument("--output", default=".", help="Output directory for the generated input file")
    return parser.parse_args()

def main():
    args = parse_args()

    config = {}
    config['xyz dir'] = args.xyz_dir
    config['molecule'] = os.path.basename(args.xyz_dir).replace('_xyz', '')
    config['cell'] = args.cell
    config['cp2k'] = {}
    config['cp2k']['basis set']  = 'dzvp-gth'
    config['cp2k']['pseudo']     = 'gth-lda'
    config['cp2k']['functional'] = 'lda'
    config['cp2k']['kinetic']    = 'lda_k_tf'

    gen_cp2k = CP2KInputGenerator(config)
    gen_cp2k.save_input(args.output)

    if any(info['method'] == 'wf' for info in config['info fragments'].values()):
        pass
        config['molcas'] = {}
        config['molcas']['basis set']  = 'ANO-S'

        gen_molcas = OpenMOLCASInputGenerator(config)
        gen_molcas.save_input(args.output)

if __name__ == "__main__":
    main()
