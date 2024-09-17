#!/usr/bin/env python3

# Developed by Konstantin Komarov.
import argparse
import os
from typing import Any, Dict, List


class CP2KInputGenerator:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.xyz_dir = config["xyz dir"]
        self.molecule_name = config["molecule"]
        self.basis_set = config["cp2k"]["basis set"]
        self.basis_path = config["cp2k"]["basis path"]
        self.dft_functional = config["cp2k"].get("functional")
        self.kinetic_functional = config["cp2k"].get("kinetic")
        self.pseudopotential = config["cp2k"]["pseudo"]
        self.pseudo_path = config["cp2k"]["pseudo path"]
        self.cutoff = config["cp2k"]["mgrid"]["cutoff"]
        self.rel_cutoff = config["cp2k"]["mgrid"]["rel cutoff"]
        self.cell_size = config["cell"]
        self.fragments = self._get_fragments()
        self.fragment_info = self._get_fragment_info()
        self.total_atoms = self.fragment_info["tot.xyz"]["atoms"]
        config["info fragments"] = {}
        config["info fragments"] = self.fragment_info
        self.do_hf = False
        if self.dft_functional.lower() == "none":
            self.do_hf = True

    def _get_fragments(self) -> List[str]:
        return sorted(
            [
                f
                for f in os.listdir(self.xyz_dir)
                if f.startswith("frag") and f.endswith(".xyz")
            ]
        )

    def _get_fragment_info(self) -> Dict[str, Dict[str, int]]:
        info = {}
        atom_numbers = {
            "H": 1,
            "He": 2,
            "Li": 3,
            "Be": 4,
            "B": 5,
            "C": 6,
            "N": 7,
            "O": 8,
            "F": 9,
            "Ne": 10,
            "Na": 11,
            "Mg": 12,
            "Al": 13,
            "Si": 14,
            "P": 15,
            "S": 16,
            "Cl": 17,
            "Ar": 18,
            "K": 19,
            "Ca": 20,
            "Sc": 21,
            "Ti": 22,
            "V": 23,
            "Cr": 24,
            "Mn": 25,
            "Fe": 26,
            "Co": 27,
            "Ni": 28,
            "Cu": 29,
            "Zn": 30,
            "Ga": 31,
            "Ge": 32,
            "As": 33,
            "Se": 34,
            "Br": 35,
            "Kr": 36,
            "Rb": 37,
            "Sr": 38,
            "Y": 39,
            "Zr": 40,
            "Nb": 41,
            "Mo": 42,
            "Tc": 43,
            "Ru": 44,
            "Rh": 45,
            "Pd": 46,
            "Ag": 47,
            "Cd": 48,
            "In": 49,
            "Sn": 50,
            "Sb": 51,
            "Te": 52,
            "I": 53,
            "Xe": 54,
            "Cs": 55,
            "Ba": 56,
            "La": 57,
            "Ce": 58,
            "Pr": 59,
            "Nd": 60,
            "Pm": 61,
            "Sm": 62,
            "Eu": 63,
            "Gd": 64,
            "Tb": 65,
            "Dy": 66,
            "Ho": 67,
            "Er": 68,
            "Tm": 69,
            "Yb": 70,
            "Lu": 71,
            "Hf": 72,
            "Ta": 73,
            "W": 74,
            "Re": 75,
            "Os": 76,
            "Ir": 77,
            "Pt": 78,
            "Au": 79,
            "Hg": 80,
            "Tl": 81,
            "Pb": 82,
            "Bi": 83,
            "Po": 84,
            "At": 85,
            "Rn": 86,
            "Fr": 87,
            "Ra": 88,
            "Ac": 89,
            "Th": 90,
            "Pa": 91,
            "U": 92,
            "Np": 93,
            "Pu": 94,
            "Am": 95,
            "Cm": 96,
            "Bk": 97,
            "Cf": 98,
            "Es": 99,
            "Fm": 100,
            "Md": 101,
            "No": 102,
            "Lr": 103,
            "Rf": 104,
            "Db": 105,
            "Sg": 106,
            "Bh": 107,
            "Hs": 108,
            "Mt": 109,
            "Ds": 110,
            "Rg": 111,
            "Cn": 112,
            "Nh": 113,
            "Fl": 114,
            "Mc": 115,
            "Lv": 116,
            "Ts": 117,
            "Og": 118,
        }

        def count_electrons(xyz_file):
            total_electrons = 0
            with open(xyz_file, "r", encoding="utf-8") as file:
                lines = file.readlines()[2:]  # Skip the first two lines
                for line in lines:
                    parts = line.split()
                    if len(parts) == 4:
                        atom = parts[0]
                        total_electrons += atom_numbers.get(atom, 0)
            return total_electrons

        for filename in ["tot.xyz"] + self.fragments:
            file = os.path.join(self.xyz_dir, filename)
            with open(file, "r") as f:
                num_atoms = int(f.readline().strip())
                second_line = f.readline().strip().lower()
                method = "dft"  # Default method dft-in-dft
                if "method=" in second_line:
                    method = second_line.split("method=")[1].split()[0]

            num_electrons = count_electrons(file)

            info[filename] = {
                "atoms": num_atoms,
                "method": method,
                "electrons": num_electrons,
            }

        return info

    def generate_input(self) -> str:
        input_content = f"""&GLOBAl
  PROJECT {self.molecule_name}
  RUN_TYPE ENERGY_FORCE
  PRINT_LEVEL MEDIUM
  CALLGRAPH MASTER
&END

&MULTIPLE_FORCE_EVALS
  FORCE_EVAL_ORDER {' '.join(str(i) for i in range(2, len(self.fragments) + 3))}
  MULTIPLE_SUBSYS T
&END

&FORCE_EVAL
  METHOD EMBED
  &EMBED
    EMBED_METHOD FAT
    NGROUPS 1
    &MAPPING
      &FORCE_EVAL 1
        &FRAGMENT 1  # Total
          1 {self.total_atoms}
          MAP 1
        &END
      &END
"""

        for i, frag in enumerate(self.fragments, start=2):
            atoms = self.fragment_info[frag]["atoms"]
            input_content += f"""      &FORCE_EVAL {i}  # FRAGMENT {i-1}
        &FRAGMENT 1
          1 {atoms}
          MAP {i}
        &END
      &END
"""

        input_content += f"""      &FORCE_EVAL_EMBED
        &FRAGMENT 1  # Total
          1 {self.total_atoms}
        &END
"""

        start = 1
        for i, frag in enumerate(self.fragments, start=2):
            atoms = self.fragment_info[frag]["atoms"]
            end = start + atoms - 1
            input_content += f"""        &FRAGMENT {i}  # Fragment {i-1}
          {start} {end}
        &END
"""
            start = end + 1

        input_content += f"""      &END
    &END
  &END
  &SUBSYS
    &CELL
      ABC {self.cell_size[0]:.2f} {self.cell_size[1]:.2f} {self.cell_size[2]:.2f}
    &END
    &TOPOLOGY
      COORD_FILE_FORMAT XYZ
      COORD_FILE_NAME {self.molecule_name}_xyz/tot.xyz
    &END
  &END
&END

"""

        for i in range(len(self.fragments) + 1):
            input_content += self._generate_force_eval_section(i)

        return input_content

    def _generate_force_eval_section(self, index: int) -> str:
        if index == 0:
            section = """# Total
"""
            filename = "tot.xyz"
        else:
            filename = self.fragments[index - 1]
            method = self.fragment_info[filename]["method"].lower()
            if method == "wf":
                section = f"""# Fragment {index}, WF
"""
            else:
                section = f"""# Fragment {index}, DFT
"""
        method = self.fragment_info[filename]["method"].lower()

        section += f"""&FORCE_EVAL
  &DFT
    BASIS_SET_FILE_NAME {self.basis_path}
    POTENTIAL_FILE_NAME {self.pseudo_path}
#   &MGRID
#     NGRIDS 4
#     CUTOFF {self.cutoff}
#     REL_CUTOFF {self.rel_cutoff}
#   &END MGRID
"""

        if method == "wf":
            section += """    &QS
      FAT_EXTERN T
    &END QS
"""
        if index == 0:
            section += f"""    &QS
      METHOD GPW
      EPS_DEFAULT 1.0E-8
      REF_EMBED_SUBSYS T
      &OPT_EMBED
        N_ITER 50
        DENS_CONV_MAX 1E-8
        &XC
          &XC_FUNCTIONAL
            &{self.kinetic_functional}
            &END {self.kinetic_functional}
          &END XC_FUNCTIONAL
        &END XC
"""
            section += """      &END OPT_EMBED
    &END QS
"""
        section += """    &SCF
      SCF_GUESS ATOMIC
      EPS_SCF 1E-8
      MAX_SCF 50
      CHOLESKY INVERSE
      &DIAGONALIZATION
        ALGORITHM STANDARD
      &END DIAGONALIZATION
    &END SCF
"""
        if self.do_hf:
            section += f"""    &XC
      &XC_FUNCTIONAL NONE
      &END XC_FUNCTIONAL
      &HF
        FRACTION 1.0
        &SCREENING
          EPS_SCHWARZ 1.0E-10
        &END
        &INTERACTION_POTENTIAL
          POTENTIAL_TYPE TRUNCATED
          CUTOFF_RADIUS {self.cell_size[0]/2.0 - 0.5}
        &END INTERACTION_POTENTIAL
      &END HF
    &END XC
"""
        else:
            section += f"""    &XC
      &XC_FUNCTIONAL {self.dft_functional}
      &END XC_FUNCTIONAL
    &END XC
"""
        if index != 0:
            section += f"""    &PRINT
      &E_DENSITY_CUBE
        FILENAME FRAG{index}
        STRIDE 1 1 1
      &END E_DENSITY_CUBE
    &END PRINT
"""
        section += f"""  &END DFT
  &SUBSYS
    &CELL
      ABC {self.cell_size[0]:.2f} {self.cell_size[1]:.2f} {self.cell_size[2]:.2f}
    &END CELL
    &KIND DEFAULT
      BASIS_SET {self.basis_set}
      POTENTIAL {self.pseudopotential}
    &END KIND
    &TOPOLOGY
      COORD_FILE_FORMAT XYZ
      COORD_FILE_NAME {self.molecule_name}_xyz/{filename}
    &END TOPOLOGY
  &END SUBSYS
"""
        if index == 0:
            section += """  &PRINT
    &FORCES
      FILENAME "force_tot"
    &END FORCES
  &END PRINT
"""
        section += """&end

"""
        return section

    def save_input(self, output_dir: str):
        method = (
            "wf"
            if any(
                info["method"].lower() == "wf" for info in self.fragment_info.values()
            )
            else "dft"
        )
        file_name = f"{method}-in-dft_{self.molecule_name}_{self.basis_set.lower()}_{self.dft_functional.lower()}_{self.pseudopotential.lower()}"
        output_path = output_dir
        os.makedirs(output_path, exist_ok=True)
        filename = f"{file_name}.inp"
        with open(os.path.join(output_path, filename), "w", encoding="utf-8") as f:
            f.write(self.generate_input())
        print(f"Generated: {os.path.join(output_path, filename)}")


class OpenMOLCASInputGenerator:
    def __init__(self, config: Dict):
        self.xyz_dir = config["xyz dir"]
        self.molecule_name = config["molecule"]
        self.basis_set = config["molcas"]["basis set"]
        self.cell_size = config["cell"]
        self.fragment_info = config["info fragments"]
        self.wf_fragments = [
            frag for frag, info in self.fragment_info.items() if info["method"] == "wf"
        ]
        self.min_active_space = [2, 6]
        self.max_active_space = [14, 14]
    
    def get_basis(self):
        content = """  Basis set
* HYDROGEN  (4s,1p) -> [2s,1p]
 H    / inline
      1.00   1
* S-type functions
     4    2
               1.301000E+01
               1.962000E+00
               4.446000E-01
               1.220000E-01
      1.968500E-02           0.000000E+00
      1.379770E-01           0.000000E+00
      4.781480E-01           0.000000E+00
      5.012400E-01           1.000000E+00
* P-type functions
     1    1
               7.270000E-01
      1.0000000
End of basis basis_set"""
        return content

    def _angstrom_to_au(self, value: float) -> float:
        #       return value * 1.8897259886
        return value * 1.8722325

    def generate_active_space(self, num_electrons):

        min_electrons, max_electrons = (
            self.min_active_space[0],
            self.max_active_space[0],
        )
        min_orbitals, max_orbitals = self.min_active_space[1], self.max_active_space[1]

        active_electrons = min(max(num_electrons, min_electrons), max_electrons)
        active_orbitals = min(max(num_electrons, min_orbitals), max_orbitals)

        space = [active_electrons, active_orbitals]

        return space

    def generate_input(self, fragment_number: str) -> str:
        cell_au = [self._angstrom_to_au(size) for size in self.cell_size]
        grid_origin = [-size / 2 for size in cell_au]

        input_content = f"""> copy $CurrDir/vemb_{fragment_number}.dat $WorkDir
> copy $CurrDir/{self.molecule_name}_xyz/frag{fragment_number}.xyz $WorkDir
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
  charge=0

&scf
  charge=0
  ksdft=lda

&grid_it
  name=Scf
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
            fragment_number = fragment.split(".")[0].replace("frag", "")

            # Generate and save input file
            input_filename = f"extern_{fragment_number}.inp"
            with open(os.path.join(output_dir, input_filename), "w") as f:
                f.write(self.generate_input(fragment_number))
            print(f"Generated: {os.path.join(output_dir, input_filename)}")

            # Generate and save run script
            script_filename = f"extern_{fragment_number}.sh"
            with open(os.path.join(output_dir, script_filename), "w") as f:
                f.write(self.generate_run_script(fragment_number))
            print(f"Generated: {os.path.join(output_dir, script_filename)}")

            # Generate and save roll cubefile script
            roll_cubefile_filename = "roll_cubefile.py"
            with open(os.path.join(output_dir, roll_cubefile_filename), "w") as f:
                f.write(self.generate_roll_cubefile_script())
            print(f"Generated: {os.path.join(output_dir, roll_cubefile_filename)}")


def process_input(input_path: str, config: Dict[str, Any]):
    def process_xyz_directory(xyz_dir: str):
        if not os.path.exists(os.path.join(xyz_dir, "tot.xyz")):
            print(f"Skipping {xyz_dir}: no tot.xyz file found")
            return

        molecule_name = os.path.basename(os.path.dirname(xyz_dir))
        config_copy = config.copy()
        config_copy.update(
            {
                "xyz dir": xyz_dir,
                "molecule": molecule_name,
            }
        )

        generator = CP2KInputGenerator(config_copy)
        generator.save_input(os.path.dirname(xyz_dir))

<<<<<<< HEAD
        if any(info["method"] == "wf" for info in generator.fragment_info.values()):
            molcas_config = config_copy.copy()
            molcas_config["molcas"] = config.get("molcas", {"basis set": "ANO-S"})
            gen_molcas = OpenMOLCASInputGenerator(molcas_config)
=======
        if any(info['method'] == 'wf' for info in generator.fragment_info.values()):
            gen_molcas = OpenMOLCASInputGenerator(config_copy)
>>>>>>> 3dd6c46 (some fix)
            gen_molcas.save_input(os.path.dirname(xyz_dir))

    if os.path.isdir(input_path):
        for root, dirs, files in os.walk(input_path):
            if root.endswith("_xyz"):
                process_xyz_directory(root)
    else:
        print(f"Error: {input_path} is not a directory")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate CP2K input file for embedding theory"
    )
    parser.add_argument(
        "input_path",
        help="Path to the directory containing subdirectories with XYZ files",
    )
    parser.add_argument(
        "--cell",
        nargs=3,
        type=float,
        default=[10, 10, 10],
        help="Cell size in Angstroms (e.g. --cell 10 10 10)",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    config = {
<<<<<<< HEAD
        "cell": args.cell,
        "cp2k": {
            "basis path": "GTH_BASIS_SETS",
            "basis set": "DZVP-GTH",
            "functional": "NONE",
            "kinetic": "LDA_K_ZLP",
            "pseudo path": "HF_POTENTIALS",
            "pseudo": "GTH-HF",
            "mgrid": {"cutoff": 210, "rel cutoff": 30},
        },
=======
        'cell': args.cell,
        'cp2k': {
            'basis path': 'GTH_BASIS_SETS',
            'basis set': 'DZVP-GTH',
            'functional': 'LDA',
            'kinetic': 'LDA_K_TF',
            'pseudo path': 'GTH_POTENTIALS',
            'pseudo': 'GTH-LDA',
            'mgrid': {
                'cutoff': 210,
                'rel cutoff': 30
            }
        },
        'molcas': {
            'basis set': 'ANO-S'  # DZ, TZ, ANO-S-VDZP,
        }
>>>>>>> 3dd6c46 (some fix)
    }

    process_input(args.input_path, config)


if __name__ == "__main__":
    main()
