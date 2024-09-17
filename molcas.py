""" Molcas input class.
@input: config dictionary, containing:
  config['calc type'] = string('hf'/'dft'/'casscf'/'caspt2')
  config['mol name'] = string()
  config['xyz file'] = string()
  config['basis set'] = string()
  config['active space'] = [(int(num_electrons), int(num_orbitals)]
  config['symm a1'] = int()
  config['symm b2'] = int()
  config['symm b1'] = int()
  config['symm a2'] = int()
  config['num roots'] = int()
"""
import sys
from typing import Dict


class MolcasInputGenerator:
    """Generates Molcas input files based on configuration."""
    def __init__(self, config: Dict):
        self.config = config

    def gen_input_hf(self) -> str:
        """Generates Molcas input for HF."""
        content = f"""&GATEway
  COORd = {self.config['xyz file']}
  BASIs = {self.config['basis set']}

&SEWArd

&SCF
  CHARge = 0
  SPIN = 1
"""
        return content

    def gen_input_dft(self) -> str:
        """Generates Molcas input DFT."""
        content = f"""&GATEway
  COORd = {self.config['xyz file']}
  BASIs = {self.config['basis set']}

&SEWArd

&SCF
  CHARge = 0
  SPIN = 1

&SCF
  CHARge = 0
  SPIN = 1
  KSDFt = lda
"""
        return content

    def gen_input_casscf(self) -> str:
        """Generates Molcas input CASSCF."""
        a1 = self.config['symm a1']
        b2 = self.config['symm b2']
        b1 = self.config['symm b1']
        a2 = self.config['symm a2']
        active_e, _ = self.config['active space']
        n_roots = self.config['num roots']
        content = f"""&GATEway
  COORd = {self.config['xyz file']}
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
  RAS2 = {a1} {b2} {b1} {a2}
  RAS3 = 0 0 0 0
  CIRoot = {n_roots} {n_roots} 1
  LevShift = 0.5

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

    def gen_input_caspt2(self):
        """Generates Molcas input CASPT2."""
        n_roots = self.config['num roots']
        content = self.gen_input_casscf()
        content += """&CASPt2
  PROP
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
        mol_name = self.config['mol name']
        active_e, active_o = self.config['active space']
        filename = f"{mol_name}_{active_e}-{active_o}.inp"
        filepath = f"{output_dir}/{filename}"

        try:
            with open(filepath, 'w', encoding="utf-8") as f:
                method_name = f"gen_input_{self.config['calc type'].lower()}"
                input_generator = getattr(self, method_name)
                f.write(input_generator())
            print(f"Generated: {filepath}")
        except IOError as e:
            print(f"Error writing input file: {e}")
            sys.exit(1)
