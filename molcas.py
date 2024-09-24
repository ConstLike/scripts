""" Molcas input class.
@input: config dictionary, containing:
  config['calc type'] = string('hf'/'dft'/'casscf'/'caspt2')
  config['prefix'] = string()
  config['mol name'] = string()
  config['xyz file'] = string()
  config['basis set'] = string()
  config['functional'] = string()
  config['active space'] = [(int(num_electrons), int(num_orbitals)]
  config['symm a1'] = int()
  config['symm b2'] = int()
  config['symm b1'] = int()
  config['symm a2'] = int()
  config['num roots'] = int()
"""
import os
import sys
from typing import Dict


class MolcasInputGenerator:
    """Generates Molcas input files based on configuration."""
    def __init__(self, config: Dict):
        self.config = config

    def gen_input_hf(self) -> str:
        """Generates Molcas input for HF."""
        content = f"""> copy $CurrDir/../{self.config['mol name']}_xyz/tot.xyz $WorkDir/.

&GATEway
  COORd = tot.xyz
  BASIs = {self.config['basis set']}

&SEWArd

&SCF
  CHARge = 0
  SPIN = 1

&GRID_it
  NAME = {self.config['calc type']}
  NPOInts = 107 107 107
  GORI
  -9.3611625 -9.3611625 -9.3611625
  18.7223250 0.0 0.0
  0.0 18.7223250 0.0
  0.0 0.0 18.7223250
"""
        return content

    def gen_input_dft(self) -> str:
        """Generates Molcas input DFT."""
        content = f"""> copy $CurrDir/../{self.config['mol name']}_xyz/tot.xyz $WorkDir/.

&GATEway
  COORd = tot.xyz
  BASIs = {self.config['basis set']}

&SEWArd

&SCF
  CHARge = 0
  SPIN = 1

&SCF
  CHARge = 0
  SPIN = 1
  KSDFt = {self.config['functional']}

&GRID_it
  NAME = {self.config['calc type']}
  NPOInts = 107 107 107
  GORI
  -9.3611625 -9.3611625 -9.3611625
  18.7223250 0.0 0.0
  0.0 18.7223250 0.0
  0.0 0.0 18.7223250
"""
        return content

    def gen_input_casscf(self) -> str:
        """Generates Molcas input CASSCF."""
        a1, b1 = self.config['symm a1'], self.config['symm b1']
        a2, b2 = self.config['symm a2'], self.config['symm b2']
        active_e, _ = self.config['active space']
        n_roots = self.config['num roots']
        content = f"""> copy $CurrDir/../{self.config['mol name']}_xyz/tot.xyz $WorkDir/.

&GATEway
  COORd = tot.xyz
  BASIs = {self.config['basis set']}

&SEWArd

&SCF
  CHARge = 0
  SPIN = 1

&RASScf
  Spin = 1
  Symmetry = 1
  nActEl = {active_e} 0 0
  Inactive =  0 0 0 0
  RAS1 = 0 0 0 0
  RAS2 = {a1} {b1} {a2} {b2}
  RAS3 = 0 0 0 0
  CIRoot = {n_roots} {n_roots} 1
  LevShift = 0.5

&GRID_it
  NAME = {self.config['calc type']}
  NPOInts = 107 107 107
  GORI
  -9.3611625 -9.3611625 -9.3611625
  18.7223250 0.0 0.0
  0.0 18.7223250 0.0
  0.0 0.0 18.7223250
"""
        if n_roots > 1:
            content += f"""
&RASSi
  NROFjobiphs = 1 {n_roots}
  {' '.join(str(i) for i in range(1, n_roots + 1))}
  XVES
  MEES
  PROP
  3
  'mltpl  1' 1
  'mltpl  1' 2
  'mltpl  1' 3
"""
        return content

    def gen_input_caspt2(self) -> str:
        """Generates Molcas input CASSCF."""
        a1, b1 = self.config['symm a1'], self.config['symm b1']
        a2, b2 = self.config['symm a2'], self.config['symm b2']
        active_e, _ = self.config['active space']
        n_roots = self.config['num roots']
        content = f"""> copy $CurrDir/../{self.config['mol name']}_xyz/tot.xyz $WorkDir/.

&GATEway
  COORd = tot.xyz
  BASIs = {self.config['basis set']}

&SEWArd

&SCF
  CHARge = 0
  SPIN = 1

&RASScf
  Spin = 1
  Symmetry = 1
  nActEl = {active_e} 0 0
  Inactive =  0 0 0 0
  RAS1 = 0 0 0 0
  RAS2 = {a1} {b1} {a2} {b2}
  RAS3 = 0 0 0 0
  CIRoot = {n_roots} {n_roots} 1
  LevShift = 0.5

&CASPt2
  PROP

&GRID_it
  NAME = {self.config['calc type']}
  NPOInts = 107 107 107
  GORI
  -9.3611625 -9.3611625 -9.3611625
  18.7223250 0.0 0.0
  0.0 18.7223250 0.0
  0.0 0.0 18.7223250
"""
        if n_roots > 1:
            content += f"""
&RASSi
  NROFjobiphs = 1 {n_roots}
  {' '.join(str(i) for i in range(1, n_roots + 1))}
  XVES
  MEES
  PROP
  3
  'mltpl  1' 1
  'mltpl  1' 2
  'mltpl  1' 3
"""
        return content

    def save_input(self, output_dir: str) -> None:
        """Saves the generated input to a file."""
        file_name = f"{self.config['subfolder']}.inp"
        os.makedirs(output_dir, exist_ok=True)

        # Save Molcas input
        try:
            with open(os.path.join(output_dir, file_name),
                      'w',
                      encoding="utf-8") as f:
                method_name = f"gen_input_{self.config['calc type'].lower()}"
                input_generator = getattr(self, method_name)
                f.write(input_generator())
            print(f"Generated: {os.path.join(output_dir, file_name)}")
        except IOError as e:
            print(f"Error writing input file: {e}")
            sys.exit(1)
