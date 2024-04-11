#!/bin/bash

scftypes="rohf"
functionals="dtcam" #"bhhlyp camb3lyp camhb3lyp camqtp00 hcth407 hse06 m062x m06hf m06l olyp pbe qtp17 r2scan r2scan01 svwn thcth tpss tpssh wb97 x3lyp"
#functionals="camb3lyp"
basis_sets="631gd" # 631gd, cct, acct
tddfts="mrsfs" # mrsfs, mrsft
alpha="0.5"
beta="0.00"

#alpha="0.40 0.41 0.42 0.43 0.44 0.45 0.46 0.47 0.48"
#beta="0.11 0.12 0.13 0.14 0.15 0.16 0.17 0.18 0.19"

for alp in $alpha
do
  for bet in $beta
  do
    methods="ro_${tddfts}_${basis_sets}_${alp}_${bet}_0.5_0.0_0.5-2D-plot"
    #ethods= ro mrsfs         631gd     alphac  betac mralp mrbet spc 2D-plot
    for method in $methods
    do
    # rm -r $method
      mkdir $method
      for basis in $basis_sets
      do
        for scftype in $scftypes
        do
          for tddft in $tddfts
          do
            for func in $functionals
            do
              for i in `cat data/data.list`
              do
                fbase="${i%.*}"
                file="${scftype}_mrsfs-vee_${fbase}_${basis}_${func}"
                fout="${method}/$file.inp"
                cat "$HOME/scripts/inp_folder/${scftype}.inc"    >> "$fout"
                cat "$HOME/scripts/inp_folder/${func}.inc"       >> "$fout"
                cat "$HOME/scripts/inp_folder/dirscff.inc"       >> "$fout"
                cat "$HOME/scripts/inp_folder/gcommon.inc"       >> "$fout"
                cat "$HOME/scripts/inp_folder/${basis}.inc"      >> "$fout"
                cat "$HOME/scripts/inp_folder/${tddft}.inc"      >> "$fout"
#               echo " \$dft alphac=0.19 betac=0.29 \$end"       >> "$fout"
                echo " \$dft alphac=$alp betac=$bet \$end"       >> "$fout"
                echo " \$tddft spcp(1)=0.5,0.5,0.5 \$end"        >> "$fout"
                echo " \$tddft mrscal=0.5 \$end"                 >> "$fout"
                echo " \$tddft mralp=0.5 mrbet=0.0 \$end"        >> "$fout"
#               echo " \$tddft mrscal=${alp} \$end"              >> "$fout"
#               echo " \$tddft mralp=${alp} mrbet=${bet} \$end"  >> "$fout"
                cat "data"/$i >> "$fout"
                fsubmite="gms_sbatch2 -i $file.inp -p \"r630,r631,ryzn\" -s \`pwd\` -v konst"
                echo $(basename -- "$file.log") >> "${method}/y_filelist"
                echo "$fsubmite" >> "${method}/y_submite"
              done
            done
          done
        done
      done
    done
    echo "$method"
    chmod +x "${method}/y_submite"
    cd $method
     ./y_submite
    cd ../.
  done
done
