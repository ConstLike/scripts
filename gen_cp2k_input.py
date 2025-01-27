import os
import sys
from typing import Dict


class CP2KInputGenerator:
    def __init__(self, config: Dict):
        self.config = config
        self.xyz_dir = config["xyz dir"]
        self.basis_set = config["basis set"]
        self.basis_path = config["basis set file"]
        self.dft_functional = config["functional"]
        self.pseudopotential = config["pseudo"]
        self.pseudo_path = config["pseudo file"]
        self.cutoff = config["cutoff"]
        self.rel_cutoff = config["rel cutoff"]
        self.cell_size = config["cell"]
        self.do_hf = False
        if self.dft_functional.lower() == "none":
            self.do_hf = True

    def generate_input(self) -> str:
        """ xx """
        input_content = f"""&GLOBAL
  PROJECT {self.config['mol name']}
  RUN_TYPE ENERGY_FORCE
  PRINT_LEVEL MEDIUM
  CALLGRAPH MASTER
&END GLOBAL

&FORCE_EVAL
  METHOD Quickstep
  &DFT
    BASIS_SET_FILE_NAME {self.basis_path}
    POTENTIAL_FILE_NAME {self.pseudo_path}
    &MGRID
      CUTOFF {self.cutoff}
      REL_CUTOFF {self.rel_cutoff}
    &END MGRID
    &QS
      METHOD GPW
      EPS_DEFAULT 1.0E-10
#     EXTRAPOLATION ASPC
#     EXTRAPOLATION_ORDER 3
    &END QS
    &SCF
      SCF_GUESS ATOMIC
      EPS_SCF 1.0E-8
      MAX_SCF 100
#     &MIXING
#       METHOD BROYDEN_MIXING
#       ALPHA 0.4
#       NBROYDEN 8
#     &END MIXING
    &END SCF
"""
        if self.do_hf:
            input_content += f"""    &XC
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
            input_content += f"""    &XC
      &XC_FUNCTIONAL {self.dft_functional}
      &END XC_FUNCTIONAL
    &END XC
"""
        input_content += f"""    &END DFT
  &SUBSYS
    &CELL
      ABC {self.cell_size[0]} {self.cell_size[1]} {self.cell_size[2]}
    &END CELL
    &TOPOLOGY
      COORD_FILE_FORMAT XYZ
      COORD_FILE_NAME ../{os.path.basename(self.config['xyz dir'])}/tot.xyz
    &END TOPOLOGY
    &KIND DEFAULT
      BASIS_SET {self.basis_set}
      POTENTIAL {self.pseudopotential}
    &END KIND
  &END SUBSYS
  &PRINT
    &FORCES
      FILENAME __STD_OUT__
    &END FORCES
  &END PRINT
&END FORCE_EVAL
"""
        return input_content

    def save_input(self, output_dir: str) -> None:
        """Saves the generated input to a file."""
        file_name = f"{self.config['subfolder']}.inp"
        os.makedirs(output_dir, exist_ok=True)

        try:
            with open(os.path.join(output_dir, file_name),
                      'w',
                      encoding="utf-8") as f:
                f.write(self.generate_input())
            print(f"Generated: {os.path.join(output_dir, file_name)}")
        except IOError as e:
            print(f"Error writing input file: {e}")
            sys.exit(1)
