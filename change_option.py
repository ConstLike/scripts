#!/usr/bin/env python3
import os


def command_line_args():
    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-i', '--input',
        type=str,
        help='Provide the inputs.log file')
    parser.add_argument(
        '-o', '--orbital',
        default=False,
        type=str,
        help='Option: add $vec')

    return parser.parse_args()


if __name__ == '__main__':

    arg = command_line_args()
    name_files = arg.input
    make_orbital = arg.orbital
    file_dir = os.path.dirname(os.path.realpath('__file__'))
    file_names = os.path.join(file_dir, name_files)
    inputs = open(str(file_names), "r").read()
    files = inputs.splitlines()

    for file in files:
        f = open(file, "r")
        file_inp = f.read()
        f.close()

        # for ROHF
#       file_inp = file_inp.replace('save_mol=False', 'save_mol=True')
#       file_inp = file_inp.replace('maxit=15', 'maxit=30')
        file_inp = file_inp.replace('save_mol=True', 'save_mol=False')
#       file_inp = file_inp.replace('conv=1.0e-9', 'conv=1.0e-8')
#       file_inp = file_inp.replace('dirscf=.f.','dirscf=.t.')
#       file_inp = file_inp.replace('dfttyp=svwn','dfttyp=libxc')
#       file_inp = file_inp.replace('alp=0.15','mralp=0.15')
#       file_inp = file_inp.replace('alp=0.48','mralp=0.48')
#       file_inp = file_inp.replace('betac=0.95','mrbet=0.95')
#       file_inp = file_inp.replace('betac=0.0','mrbet=0.0')
#       file_inp = file_inp.replace('TDDFT=SPNFLP','tddft=mrsf')
#       file_inp = file_inp.replace('shift=.t.','shift=.f.')
#       file_inp = file_inp.replace("$tddft mralp=0.5 mrbet=0.0 $end","")
#       file_inp = file_inp.replace("swdiis=0.000","swdiis=0.002")
#       file_inp = file_inp.replace("$scf swdiis=0.005 ethrsh=1.5 $end","")
        file_inp = file_inp.splitlines(True)
#       file_inp.insert(8," $tddft mrsoc=.t. $end\n")
#       file_inp.insert(8," $transt $end\n")
#       file_inp.insert(7," $guess guess=hcore $end\n")
#       file_inp.append(" \n $scf swdiis=0.005 diis=.t. ethrsh=2.0 $end")
#       file_inp.append(" \n $scf CONV=1.0d-04 $end")

#       tddft = file.split('_')[1]
#       file_tddft = str('/bighome/k.komarov/scripts/inp_folder/'+tddft+'.inc')
#       f = open(file_tddft,"r")
#       tddft_lines = f.readlines()
#       f.close()

#       for i in tddft_lines:
#           file_inp.append(i)
#           file_inp.insert(5,i)

        f_out = open(file, 'w')
        for il, l in enumerate(file_inp):
            f_out.write(str(l))

#       output = []
#       if make_orbital:
#           f = open(file.replace('inp','dat'),"r")
#           file_dat = f.readlines()
#           f.close()
#           if not guess:
#               output.append(" $guess guess=moread $end\n")
#               output.append(" $dft switch=0 swoff=0 $end\n")
#           output.append(" $guess guess=huckel $end\n")
#           output.append(" $contrl itol=25 $end\n")
#           output.append(" $dft sg1=.t. $end\n")
#           for il, l in enumerate(file_dat):
#               if "$VEC" in l:
#                   k = 0
#                   while(file_dat[il+k].split()[0]!="$END"):
#                       output.append(file_dat[il+k])
#                       k+=1
#           output.append(" $END")

#       file_inp.insert(3,"")

#       for iline in output:
#           f_out.write(str(iline))
        f_out.close()
