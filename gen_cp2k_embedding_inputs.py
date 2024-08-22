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
        for filename in ['tot.xyz'] + self.fragments:
            with open(os.path.join(self.xyz_dir, filename), 'r') as f:
                num_atoms = int(f.readline().strip())
                second_line = f.readline().strip().lower()
                method = 'dft'  # Default method
                if 'method=' in second_line:
                    method = second_line.split('method=')[1].split()[0]
            info[filename] = {'atoms': num_atoms, 'method': method}
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
            section = f"""# Fragment {index}
"""
            filename = self.fragments[index-1]

        section += """&force_eval
  &dft
    basis_set_file_name GTH_BASIS_SETS
    potential_file_name GTH_POTENTIALS
"""

        method = self.fragment_info[filename]['method'].lower()
        if method == "wf":
            section +="""    &qs
      fat_extern t
    &end
"""
        if index == 0:
            section += f"""    &qs
      ref_embed_subsys t
      &opt_embed
        n_iter 20
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
      filename tot
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

    def _angstrom_to_au(self, value: float) -> float:
        return value * 1.8897259886

    def generate_input(self, fragment_number: str) -> str:
        cell_au = [self._angstrom_to_au(size) for size in self.cell_size]
        grid_origin = [-size/2 for size in cell_au]

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

&grid_it
  name=Scf
  npoints=107 107 107
  gori
  {grid_origin[0]:.7f} {grid_origin[1]:.7f} {grid_origin[2]:.7f}
  {cell_au[0]:.7f} 0.0 0.0
  0.0 {cell_au[1]:.7f} 0.0
  0.0 0.0 {cell_au[2]:.7f}

"""
        return input_content

    def generate_run_script(self, fragment_number: str) -> str:
        script_content = f"""#!/bin/bash
pymolcas extern_{fragment_number}.inp | tee extern_{fragment_number}.out
grep "Total SCF energy" extern_{fragment_number}.out | awk '{{ print $5 }}' > extern_{fragment_number}.e
python2 $MOLCAS/Tools/grid2cube/grid2cube.py extern_{fragment_number}.Scf.lus extern_{fragment_number}_orig.cube
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
        config['molcas']['basis set']  = 'ANO-S-VDZP'

        gen_molcas = OpenMOLCASInputGenerator(config)
        gen_molcas.save_input(args.output)

if __name__ == "__main__":
    main()
