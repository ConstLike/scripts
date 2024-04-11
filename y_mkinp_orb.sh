#!/bin/bash

scftypes="rohf"
#functionals="bhhlyp camb3lyp camhb3lyp camqtp00 hcth407 hse06 m062x m06hf m06l olyp pbe qtp17 r2scan r2scan01 svwn thcth tpss tpssh wb97 x3lyp"
functionals="bhhlyp"
basis_sets="631gd" # 631gd, cct, acct
tddfts="mrsfs" # mrsfs, mrsft
#alpha="0.01 0.10 0.19 0.20 0.30 0.40"
#beta="0.00 0.10 0.20 0.29 0.30 0.40"

#alpha="0.19"
#beta="0.3"
#alpha="0.1 0.15 0.2 0.3 0.5"
#alpha="0.40 0.41 0.42 0.43 0.44 0.45 0.46 0.47 0.48"
#beta="0.11 0.12 0.13 0.14 0.15 0.16 0.17 0.18 0.19"
# Define array of PBE exchange-correlation values
#pbe_xc=(.0 .1 .2 .3 .4 .5 .6 0.7 0.8 0.9 1.0)

# for alp in $alpha
# do
# for bet in $beta
# do
#methods="ro-mrsf-${basis_sets}-${functionals}_${alp}_${bet}_0.5_0.0_0.5-2D-finish"
methods="test"
#methods="rohf-mrsf-631gd-functionals"
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
#           for c in "${pbe_xc[@]}"
#           do
#             x=$(echo "1.0-$c" | bc)
#             c_fmt=$(printf "%.1f" $c)
#             x_fmt=$(printf "%.1f" $x)
              fbase="${i%.*}"
              file="${scftype}_mrsfs_${fbase}_${basis}_${func}"
              fout="${method}/$file.inp"
              cat "$HOME/scripts/inp_folder/${scftype}.inc" >> "$fout"
              cat "$HOME/scripts/inp_folder/${func}.inc"    >> "$fout"
#             echo " \$contrl dfttyp=uselibxc \$end" >> "$fout"
#             echo " \$libxc functional=mixed hfex=${c_fmt} \$end" >> "$fout"
#             echo " \$gga_x PBE=$x_fmt \$end" >> "$fout"
#             echo " \$gga_c PBE=1.0 \$end"    >> "$fout"
#             echo " \$contrl dfttyp=uselibxc \$end" >> "$fout"
              cat "$HOME/scripts/inp_folder/dirscff.inc"    >> "$fout"
              cat "$HOME/scripts/inp_folder/gcommon.inc"    >> "$fout"
              cat "$HOME/scripts/inp_folder/${basis}.inc"   >> "$fout"
#             cat "$HOME/scripts/inp_folder/${tddft}.inc"   >> "$fout"
#             echo " \$tddft mramo=.t. \$end"               >> "$fout"
              cat "$HOME/scripts/inp_folder/mrsfs.inc"   >> "$fout"
#             cat "$HOME/scripts/inp_folder/momba.inc"   >> "$fout"
#             echo " \$dft alphac=0.19 betac=0.29 \$end"                  >> "$fout"
#             echo " \$dft alphac=$alp betac=$bet \$end"                  >> "$fout"
#             echo " \$tddft spcp(1)=0.5,0.5,0.5 \$end"                  >> "$fout"
#             echo " \$tddft mrscal=0.5 \$end"                          >> "$fout"
#             echo " \$tddft mralp=0.5 mrbet=0.0 \$end"               >> "$fout"
#             echo " \$tddft mrscal=${alp} \$end"                          >> "$fout"
#             echo " \$tddft mralp=${alp} mrbet=${bet} \$end"               >> "$fout"
#             cat "/bighome/k.komarov/scripts/inp_folder/mrscal.inc"     >> "$fout"
#             echo " \$tddft mrscal=0.5 spcp(1)=0.5,0.5,0.5 \$end"       >> "$fout"
              cat "data"/$i >> "$fout"
#             fsubmite="gms_sbatch2 -i $file.inp -p r630  -s \`pwd\` -v umrsf -e /bighome/k.komarov/projects/gms-mrsf-uhf"
              fsubmite="gms_sbatch2 -i $file.inp -p \"r630,r631,ryzn\" -s \`pwd\` -v konst"
              echo $(basename -- "$file.log") >> "${method}/y_filelist"
              echo "$fsubmite" >> "${method}/y_submite"
#           done
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
# done
# done
