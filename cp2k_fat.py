""" CP2K input class.
@input: config dictionary, containing:
  config['calc type'] = string(dft|casscf|caspt2)
  config['mol name'] = string()
  config['xyz dir'] = string()
  config['cell'] = [float(), float(), float()]
  config['basis set'] = string()
  config['basis set file'] = string()
  config['kinetic'] = string()
  config['functional'] = string()
  config['pseudo'] = string()
  config['pseudo file'] = string()

  config['wf basis set'] = string()
  config['wf functional'] = string()
  config['active space'] = [(int(num_electrons), int(num_orbitals)]
  config['symm a1'] = int()
  config['symm b2'] = int()
  config['symm b1'] = int()
  config['symm a2'] = int()
  config['num roots'] = int()
"""
import os
from typing import Dict, List

from utils import InputUtils


class CP2KFATInputGenerator:
    """Generates CP2K input files for FAT calculations."""

    def __init__(self, config: Dict):
        """Initialize the CP2K input generator."""
        self.config = config
        self.config['fragments'] = self._get_fragments()
        self.config['frag info'] = InputUtils.get_fragment_info(
            self.config['xyz dir'], self.config['fragments']
        )
        self.config['tot atoms'] = self.config['frag info']['tot.xyz']['atoms']
        emb_frag = self.config['emb frag'][0]
        method = self.config['emb frag'][1]
        self.config['frag info'][emb_frag]['method'] = method

    def _get_fragments(self) -> List[str]:
        """Get list of fragment XYZ files."""
        return InputUtils.get_fragment_files(self.config['xyz dir'])

    def generate_fat_input(self) -> str:
        """Generate the CP2K FAT input content."""
        input_content = self._generate_global_section()
        input_content += self._generate_force_eval_section()
        input_content += self._generate_subsys_section()

        for i in range(len(self.config['fragments']) + 1):
            input_content += self._generate_fragment_section(i)

        return input_content

    def _generate_global_section(self) -> str:
        """Generate the global section of the input."""
        return f"""&GLOBAL
  PRINT_LEVEL MEDIUM
  PROJECT {self.config['mol name']}
  RUN_TYPE ENERGY_FORCE
  CALLGRAPH MASTER
&END GLOBAL

&MULTIPLE_FORCE_EVALS
  FORCE_EVAL_ORDER {
  ' '.join(str(i) for i in range(2, len(self.config['fragments']) + 3))
  }
  MULTIPLE_SUBSYS T
&END MULTIPLE_FORCE_EVALS

"""

    def _generate_force_eval_section(self) -> str:
        """Generate the force_eval section of the input."""
        content = """&FORCE_EVAL
  METHOD EMBED
  &EMBED
    EMBED_METHOD FAT
    NGROUPS 1
    &MAPPING
      &FORCE_EVAL 1
        &FRAGMENT 1  # TOTAL
"""
        content += f"          1 {self.config['tot atoms']}\n"
        content += """          MAP 1
        &END FRAGMENT
      &END FORCE_EVAL
"""
        for i, frag in enumerate(self.config['fragments'], start=2):
            atoms = self.config['frag info'][frag]['atoms']
            content += f"""      &FORCE_EVAL {i}  # Fragment {i-1}
        &FRAGMENT 1
          1 {atoms}
          MAP {i}
        &END FRAGMENT
      &END FORCE_EVAL
"""
        content += f"""      &FORCE_EVAL_EMBED
        &FRAGMENT 1  # Total
          1 {self.config['tot atoms']}
        &END FRAGMENT
"""
        start = 1
        for i, frag in enumerate(self.config['fragments'], start=2):
            atoms = self.config['frag info'][frag]['atoms']
            end = start + atoms - 1
            content += f"""        &FRAGMENT {i}  # Fragment {i-1}
          {start} {end}
        &END FRAGMENT
"""
            start = end + 1
        content += """      &END FORCE_EVAL_EMBED
    &END MAPPING
  &END EMBED
"""
        return content

    def _generate_subsys_section(self) -> str:
        """Generate the subsys section of the input."""
        cell = self.config['cell']
        return f"""  &SUBSYS
    &CELL
      ABC {cell[0]:.2f} {cell[1]:.2f} {cell[2]:.2f}
    &END CELL
    &TOPOLOGY
      COORD_FILE_FORMAT XYZ
      COORD_FILE_NAME ../{self.config['mol name']}_xyz/tot.xyz
    &END TOPOLOGY
  &END SUBSYS
&END FORCE_EVAL

"""

    def _generate_fragment_section(self, index: int) -> str:
        """Generate a fragment section of the input."""
        if index == 0:
            return self._generate_total_fragment()
        else:
            return self._generate_subfragment(index)

    def _generate_total_fragment(self) -> str:
        """Generate the total fragment section."""
        cell = self.config['cell']
        return f"""&FORCE_EVAL
  &DFT
    BASIS_SET_FILE_NAME {self.config['basis set file']}
    POTENTIAL_FILE_NAME {self.config['pseudo file']}
    &MGRID
      NGRIDS 1
      CUTOFF 400
      REL_CUTOFF 400
    &END MGRID
    &QS
      METHOD GPW
      EPS_DEFAULT 1.0E-8
      REF_EMBED_SUBSYS T
      &OPT_EMBED
        N_ITER 50
        DENS_CONV_MAX 1E-8
        &XC
          &XC_FUNCTIONAL
            &{self.config['kinetic']}
            &END {self.config['kinetic']}
          &END XC_FUNCTIONAL
        &END XC
      &END OPT_EMBED
    &END QS
    &SCF
      SCF_GUESS ATOMIC
      EPS_SCF 1E-8
      MAX_SCF 50
    &END SCF
    &XC
      &XC_FUNCTIONAL {self.config['functional']}
      &END XC_FUNCTIONAL
    &END XC
  &END DFT
  &SUBSYS
    &CELL
      ABC {cell[0]:.2f} {cell[1]:.2f} {cell[2]:.2f}
    &END CELL
    &KIND DEFAULT
      BASIS_SET {self.config['basis set']}
      POTENTIAL {self.config['pseudo']}
    &END KIND
    &TOPOLOGY
      COORD_FILE_FORMAT XYZ
      COORD_FILE_NAME ../{self.config['mol name']}_xyz/tot.xyz
    &END TOPOLOGY
  &END SUBSYS
  &PRINT
    &FORCES
      FILENAME "force_tot"
    &END FORCES
  &END PRINT
&END FORCE_EVAL

"""

    def _generate_subfragment(self, index: int) -> str:
        """Generate a subfragment section."""
        filename = self.config['fragments'][index-1]
        method = self.config['frag info'][filename]['method'].lower()
        cell = self.config['cell']
        content = f"""&FORCE_EVAL
  &DFT
    BASIS_SET_FILE_NAME {self.config['basis set file']}
    POTENTIAL_FILE_NAME {self.config['pseudo file']}
    &MGRID
      NGRIDS 1
      CUTOFF 400
      REL_CUTOFF 400
    &END MGRID
"""
        if method == "extern":
            content += """    &QS
      FAT_EXTERN T
    &END QS
"""
        content += f"""    &SCF
      SCF_GUESS ATOMIC
      EPS_SCF 1E-8
      MAX_SCF 50
    &END SCF
    &XC
      &XC_FUNCTIONAL {self.config['functional']}
      &END XC_FUNCTIONAL
    &END
    &PRINT
      &E_DENSITY_CUBE
        FILENAME frag{index}
        STRIDE 1 1 1
      &END E_DENSITY_CUBE
    &END PRINT
  &END DFT
  &SUBSYS
    &CELL
      ABC {cell[0]:.2f} {cell[1]:.2f} {cell[2]:.2f}
    &END CELL
    &KIND DEFAULT
      BASIS_SET {self.config['basis set']}
      POTENTIAL {self.config['pseudo']}
    &END KIND
    &TOPOLOGY
      COORD_FILE_FORMAT XYZ
      COORD_FILE_NAME ../{self.config['mol name']}_xyz/{filename}
    &END TOPOLOGY
  &END SUBSYS
&END FORCE_EVAL

"""
        return content

    def _generate_molcas_input(self, fragment_number: str) -> str:
        """Generate Molcas input for a WF fragment."""
        a1, b1 = self.config['symm a1'], self.config['symm b1']
        a2, b2 = self.config['symm a2'], self.config['symm b2']
        active_e, _ = self.config['active space']
        n_roots = self.config['num roots']
        method = self.config['calc type'].split('-')[0]

        # > copy $CurrDir/extern_{fragment_number}.ScfOrb $WorkDir/INPORB
        if self.config['calc type'] == "caspt2-in-dft":
            content = f"""> copy $CurrDir/vemb_{fragment_number}.dat $WorkDir
> copy $CurrDir/../{self.config['mol name']}_xyz/frag{fragment_number}.xyz $WorkDir

&GATEway
  TITLe=extern_{fragment_number}
  COORd=frag{fragment_number}.xyz
  BASIs={self.config['wf basis set']}

&SEWArd
  EMBEdding
    EMBInput=vemb_{fragment_number}.dat
  ENDEmbedding

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
            content += f"""
&CASPt2
  PROP

&GRID_it
  NAME={method}
  NPOInts=191 191 191
  GORI
  -14.099128569576477 -14.099128569576477 -14.099128569576477
  28.198257139152954 0.0 0.0
  0.0 28.198257139152954 0.0
  0.0 0.0 28.198257139152954
"""
        elif self.config['calc type'] == "casscf-in-dft":
            content = f"""> copy $CurrDir/vemb_{fragment_number}.dat $WorkDir
> copy $CurrDir/../{self.config['mol name']}_xyz/frag{fragment_number}.xyz $WorkDir

&GATEway
  TITLe=extern_{fragment_number}
  COORd=frag{fragment_number}.xyz
  BASIs={self.config['wf basis set']}

&SEWArd
  EMBEdding
    EMBInput=vemb_{fragment_number}.dat
  ENDEmbedding

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
            content += f"""
&GRID_it
  NAME={method}
  NPOInts=191 191 191
  GORI
  -14.099128569576477 -14.099128569576477 -14.099128569576477
  28.198257139152954 0.0 0.0
  0.0 28.198257139152954 0.0
  0.0 0.0 28.198257139152954
"""
        elif self.config['calc type'] == "dft-in-dft":
            content = f"""> copy $CurrDir/vemb_{fragment_number}.dat $WorkDir
> copy $CurrDir/../{self.config['mol name']}_xyz/frag{fragment_number}.xyz $WorkDir

&GATEway
  TITLe=extern_{fragment_number}
  COORd=frag{fragment_number}.xyz
  BASIs={self.config['wf basis set']}

&SEWArd
  EMBEdding
    EMBInput=vemb_{fragment_number}.dat
  ENDEmbedding

&SCF
  CHARge = 0
  SPIN = 1

&SCF
  CHARge = 0
  SPIN = 1
  KSDFT = {self.config['wf functional']}

&GRID_it
  NAME={method}
  NPOInts=191 191 191
  GORI
  -14.099128569576477 -14.099128569576477 -14.099128569576477
  28.198257139152954 0.0 0.0
  0.0 28.198257139152954 0.0
  0.0 0.0 28.198257139152954
"""
        return content

    def _generate_molcas_script(self, fragment_number: str) -> str:
        """generate molcas run script for a wf fragment."""
        content = ''
        method = self.config['calc type'].split('-')[0]
        if self.config['calc type'] == 'casscf-in-dft':
            content = f"""#!/bin/sh
pymolcas extern_{fragment_number}.inp | tee extern_{fragment_number}.out
grep "1 Total energy" extern_{fragment_number}.out | awk '{{ print $8 }}' > extern_{fragment_number}.e
python2 $MOLCAS/Tools/grid2cube/grid2cube.py extern_{fragment_number}.{method}.lus extern_{fragment_number}_orig.cube
python3 roll_cubefile.py extern_{fragment_number}_orig.cube extern_{fragment_number}.cube
"""
        elif self.config['calc type'] == 'caspt2-in-dft':
            content = f"""#!/bin/sh
pymolcas extern_{fragment_number}.inp | tee extern_{fragment_number}.out
grep "CASPT2 Root  1     Total energy" extern_{fragment_number}.out | awk '{{ print $7 }}' > extern_{fragment_number}.e
python2 $MOLCAS/Tools/grid2cube/grid2cube.py extern_{fragment_number}.{method}.lus extern_{fragment_number}_orig.cube
python3 roll_cubefile.py extern_{fragment_number}_orig.cube extern_{fragment_number}.cube
"""
        elif self.config['calc type'] == 'dft-in-dft':
            content = f"""#!/bin/sh
pymolcas extern_{fragment_number}.inp | tee extern_{fragment_number}.out
#grep "Total SCF energy" extern_{fragment_number}.out | awk '{{ print $5 }}' > extern_2.e
grep "Total KS-DFT energy" extern_{fragment_number}.out | awk '{{ print $5 }}' > extern_2.e
python2 $MOLCAS/Tools/grid2cube/grid2cube.py extern_{fragment_number}.{method}.lus extern_{fragment_number}_orig.cube
python3 roll_cubefile.py extern_{fragment_number}_orig.cube extern_{fragment_number}.cube
"""
        return content

    def _generate_roll_cubefile_script_old(self) -> str:
        """Generate roll_cubefile.py script."""
        return """from sys import argv
import numpy as np
from ase.io.cube import read_cube, write_cube

with open(argv[1]) as f:
    a = read_cube(f)
a["origin"] = np.zeros_like(a["origin"])
nx, ny, nz = a["data"].shape
a["data"] = np.roll(a["data"], (-nx//2, -ny//2, -nz//2), (0, 1, 2))
with open(argv[2], "w") as f:
    write_cube(f, a["atoms"], a["data"], a["origin"])
"""

    def _generate_roll_cubefile_script(self) -> str:
        """Generate roll_cubefile.py script."""
        return """from sys import argv
import numpy as np
from ase.io.cube import read_cube, write_cube

with open(argv[1]) as f:
    a = read_cube(f)
nx, ny, nz = a["data"].shape
data_shifted = 0.5 * (np.roll(a["data"], (-nx//2, -ny//2, -nz//2), (0, 1, 2)) 
                    + np.roll(a["data"], (-nx//2+1, -nx//2+1, -nx//2+1), (0, 1, 2)))
with open(argv[2], "w") as f:
    write_cube(f, a["atoms"], data_shifted, a["origin"])
"""

    def _generate_roll_cubefile_script_fail(self) -> str:
        """Generate roll_cubefile.py script."""
        return """from sys import argv
import numpy as np
from ase.io.cube import read_cube, write_cube
from scipy import fft


def refine_alignment(data):
    nx, ny, nz = data.shape

    # Вычисление FFT
    fft_data = fft.fftn(data)

    # Создание массива сдвигов (на полрешетки)
    shifts = [
        (np.roll(data, shift, axis) + np.roll(data, shift + 1, axis)) / 2
        for shift, axis in [(-nx // 2, 0), (-ny // 2, 1), (-nz // 2, 2)]
    ]
    averaged_shifted_data = np.mean(shifts, axis=0)

    # Дополнительная обработка фазовых и амплитудных различий
    fft_shifted = fft.fftn(averaged_shifted_data)
    amplitude_ratio = np.abs(fft_data) / (np.abs(fft_shifted) + 1e-10)
    phase_shift_correction = fft_shifted * amplitude_ratio
    corrected_data = np.real(fft.ifftn(phase_shift_correction))

    return corrected_data


with open(argv[1]) as f:
    a = read_cube(f)

aligned_data = refine_alignment(a["data"])

with open(argv[2], "w") as f:
    write_cube(f, a["atoms"], aligned_data, a["origin"])
"""

    def save_input(self, output_dir: str) -> None:
        """Save the generated input files."""
        file_name = f"{self.config['subfolder']}.inp"
        os.makedirs(output_dir, exist_ok=True)

        # Save CP2K input
        with open(os.path.join(output_dir, file_name),
                  'w',
                  encoding="utf-8") as f:
            f.write(self.generate_fat_input())
        print(f"Generated: {os.path.join(output_dir, file_name)}")

        # Generate Molcas files for WF fragments
        wf_fragments = [frag for frag, info in self.config['frag info'].items()
                        if info['method'].lower() == 'extern']

        if wf_fragments:
            # Generate roll_cubefile.py
            with open(os.path.join(output_dir, "roll_cubefile.py"),
                      'w',
                      encoding="utf-8") as f:
                f.write(self._generate_roll_cubefile_script())
            print(f"Generated: {os.path.join(output_dir, 'roll_cubefile.py')}")

            for frag in wf_fragments:
                fragment_number = frag.split('.')[0].replace('frag', '')

                # Generate Molcas input
                molcas_input = self._generate_molcas_input(fragment_number)
                molcas_filename = f"extern_{fragment_number}.inp"
                with open(os.path.join(output_dir, molcas_filename),
                          'w',
                          encoding="utf-8") as f:
                    f.write(molcas_input)
                print(f"Generated: {os.path.join(output_dir, molcas_filename)}")

                # Generate Molcas run script
                script = self._generate_molcas_script(fragment_number)
                script_filename = f"extern_{fragment_number}.sh"
                with open(os.path.join(output_dir, script_filename),
                          'w',
                          encoding="utf-8") as f:
                    f.write(script)
                print(f"Generated: {os.path.join(output_dir, script_filename)}")
