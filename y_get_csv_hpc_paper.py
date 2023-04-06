#!/usr/bin/env python3.6
import fileinput
import os
import sys
import numpy as np
import argparse
import csv

def extract_data(file):
    filedata = None
    f = open(file, 'r')
    filedata = f.read()
    f.close()
    out = filedata.splitlines()

    dirscf = False

    t_of_ERI = 0.0
    t_cpu_ERI = 0.0
    t_write = 0.0
    t_flush = 0.0
    t_of_scf = 0.0
    t_cpu_scf = 0.0
    t_of_davidson = 0.0
    t_of_dav_transp = 0.0
    t_of_dav_trans1 = 0.0
    t_of_dav_trans2 = 0.0
    t_cpu_davidson = 0.0
    data_row = []
    iii=0
    for il, l in enumerate(out):
        if "dirscf=.t." in l:
            dirscf=True
        if not dirscf and "Flushing page cache" in l:
            if iii==0:
                # Timing of getting ERI
                t_of_ERI = float(out[il-8].split()[4])
                # Step CPU time of getting ERI
                if (str(out[il-10].split()[5])==str("TOTAL")):
                    t_cpu_ERI = float(out[il-10].split()[4])
                else:
                    t_cpu_ERI = float(out[il-10].split()[5])
                # Time of writing int
                t_write = float(out[il-1].split()[4])
                # time of flushing
                t_flush = float(out[il+4].split()[4])
            iii+=1
        if not dirscf and "DENSITY CHANGE" in l:
            # Timing of the first SCF stap
            t_of_scf = float(out[il+3].split()[4])
#           # Step CPU time of the first  SCF
            if (str(out[il+1].split()[5])==str("PROCEDURE")):
                continue
            else:
                if (str(out[il+1].split()[5])==str("TOTAL")):
                    t_cpu_scf = float(out[il+1].split()[4])
                else:
                    t_cpu_scf = float(out[il+1].split()[5])
        if dirscf and "DENSITY CHANGE" in l:
            # Timing of the first SCF stap
            t_of_scf = float(out[il+3].split()[4])
            # Total CPU time of the first  SCF
            if (str(out[il+1].split()[5])==str("TOTAL")):
                t_cpu_scf = float(out[il+1].split()[4])
            else:
                t_cpu_scf = float(out[il+1].split()[5])

        if "timing for transpose 1" in l:
            # Timing of the transpose in first Devidson iteration
            t_of_dav_trans1 = float(out[il+3].split()[4])
        if "timing for transpose 2" in l:
            # Timing of the transpose in first Devidson iteration
            t_of_dav_trans2 = float(out[il+3].split()[4])
        t_of_dav_transp = t_of_dav_trans1+t_of_dav_trans2
        if not dirscf and "kkk step wall time:" in l:
            # Timing of the first Devidson iteration
            t_of_davidson = float(out[il].split()[4])
            # CPU time on step
            if (str(out[il-2].split()[5])==str("TOTAL")):
                t_cpu_davidson = float(out[il-2].split()[4])
            else:
                t_cpu_davidson = float(out[il-2].split()[5])
        if dirscf and "kkk step wall time:" in l:
            # Timing of the first Devidson iteration
            t_of_davidson = float(out[il].split()[4])
            # CPU time on step
            if (str(out[il-2].split()[5])==str("TOTAL")):
                t_cpu_davidson = float(out[il-2].split()[4])
            else:
                t_cpu_davidson = float(out[il-2].split()[5])
    row = (t_of_ERI,       #0
           t_cpu_ERI,      #1
           t_write,        #2
           t_flush,        #3
           t_of_scf,       #4
           t_cpu_scf,      #5
           t_of_davidson,  #6
           t_cpu_davidson, #7
           t_of_dav_transp,#8
           )
    data_row.append(row)
    return  data_row

def check_node(file):
    filedata = None
    f = open(file, 'r')
    filedata = f.read()
    f.close()
    out = filedata.splitlines()
    for il, l in enumerate(out):
        if "compute processes on" in l:
            n_node = int(out[il].split()[5])
    if n_node>1:
        print( file, 'warning, node != 1, node =', n_node)
    return
def extract_n_state(file):
    filedata = None
    f = open(file, 'r')
    filedata = f.read()
    f.close()
    out = filedata.splitlines()
    for il, l in enumerate(out):
        if "TDDFT INPUT PARAMETERS" in l:
            n_state = int(out[il+2].split()[1])
            return n_state

def extract_nbf(file):
    filedata = None
    f = open(file, 'r')
    filedata = f.read()
    f.close()
    out = filedata.splitlines()
    for il, l in enumerate(out):
        if "NUMBER OF CARTESIAN GAUSSIAN BASIS FUNCTIONS" in l:
            nbf = int(out[il].split()[7])
            return nbf

def extract_cpu(file):
    filedata = None
    f = open(file, 'r')
    filedata = f.read()
    f.close()
    out = filedata.splitlines()
    for il, l in enumerate(out):
        if "Initiating" in l:
            cpu = int(out[il].split()[1])
            return cpu

def extract_basis(file):
    '''  mrsf_1a_c60_631g_c1_n4_t0.log '''
    '''  [0] [1] [2] [3] [4] [5] [6].log '''

    file_parts = file.split("_")

    theory = file_parts[0]
    alg = file_parts[1]
    molecule = file_parts[2]
    bas = file_parts[3]
    check_n_cpu = int(file_parts[4].split('c')[1])
    check_n_state = int(file_parts[5].split('n')[1])
    test_series_number = int(file_parts[6].split('.')[0].split('t')[1])

    n_state = extract_n_state(file)
    n_cpu = extract_cpu(file)
    if check_n_cpu != n_cpu:
        print("Warning, n_CPU != CPU in log")
        print(file, 'name:', check_n_cpu,'in log:', n_cpu)
    if check_n_state != n_state:
        print("Warning, n_state != n_state in log")
        print(file, 'name:', check_n_state,'in log:', n_state)

    nbf = extract_nbf(file)

    method = str('Direct')
    if file.count('-') >=1:
        method = str('Storage')

    basis = 'ERROR'
    if bas.count('631')==1:
        basis = bas.replace('631g','6-31G')
    if bas.count('631gdp')==1:
        basis = bas.replace('631gdp','6-31G(d,p)')
    if bas.count('6311gdp')==1:
        basis = bas.replace('6311gdp','6-311G(d,p)')
    if bas.count('cct')==1:
        basis = bas.replace('cct','cc-pVTZ')

    algorithm = 'ERROR'
    if alg.count('1a')==1:
        algorithm = alg.replace('1a','IF').upper()
    if alg.count('1b')==1:
        algorithm = alg.replace('1b','IFT').upper()
    elif alg.count('2a')==1:
        algorithm = alg.replace('2a','IF').upper()
    elif alg.count('2b')==1:
        algorithm = alg.replace('2b','IF').upper()
    elif alg.count('2d')==1:
        algorithm = alg.replace('2d','READING').upper()
    elif alg.count('3a')==1:
        algorithm = alg.replace('3a','FI').upper()
    elif alg.count('4a')==1:
        algorithm = alg.replace('4a','FI').upper()
    elif alg.count('5a')==1:
        algorithm = alg.replace('5a','FI-B8').upper()
    elif alg.count('5b')==1:
        algorithm = alg.replace('5b','FI-B2').upper()
    elif alg.count('5d')==1:
        algorithm = alg.replace('5d','ERI-TIME').upper()
    elif alg.count('5v')==1:
        algorithm = alg.replace('5d','ERI-BUF-VAL1-TIME').upper()
    elif alg.count('5g')==1:
        algorithm = alg.replace('5g','ERI-BUF-TIME').upper()
    elif alg.count('5t')==1:
        algorithm = alg.replace('5t','IFT-B2').upper()


    return theory, method, algorithm, molecule, basis, nbf, n_state, n_cpu, test_series_number

def command_line_args():
    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-i', '--input',
        type=str,
        help='Provide the inputs.log file')

    return parser.parse_args()
if __name__ == '__main__':

    arg = command_line_args()
    name_files = arg.input
    inputs=open(str(name_files),"r")
    files = inputs.read().splitlines()
    output_file = 'x'+arg.input+'.csv'


    print(output_file)


    fout = open(str(name_files)+'.log', 'w')
    fout.write('\n')
    fout.write( 'Theory'       +' '*2+
                'Method'       +' '*2+
                'Algorithm'       +' '*2+
                'Basis'       +' '*2+
                'N_bas'        +' '*2+
                'N_cpu'        +' '*2+
                'N_state'      +' '*2+
                'N_test'       +' '*2+
                'Time_ERI'     +' '*2+
                'Time_full_writing' +' '*2+
                'CPU_ERI'      +' '*2+
                'Time_flush'   +' '*2+
                'Time_Dav'     +' '*2+
                'Time_Dav_transpose'+' '*2+
                'log_file\n')
    header = ['Theory',
              'Method',
              'Algorithm',
              'Basis',
              'N_bas',
              'N_cpu',
              'N_state',
              'N_test',
              'Time_ERI',
              'Time_full_writing',
              'CPU_ERI',
              'Time_flush',
              'Time_Dav',
              'Time_Dav_transpose',
              'log_file',]
    with open(output_file, 'w', newline='', encoding='UTF8') as f:
        writer = csv.writer(f, delimiter=',')
        writer.writerow(header)

        for file in files:

            check_node(file)

            theory, method, algorithm, molecule, basis, nbf, n_state, n_cpu, n_test = extract_basis(file)
            memory = method

            data = extract_data(file)

            dirscf = False
            if method=='Direct':
                dirscf = True
            Time_full_writing = 0.0
            if not dirscf:
                # Time_ERI+Time_w+Time_flush-CPU_ERI
                Time_full_writing = round(float(data[0][0])+float(data[0][2])+float(data[0][3])-float(data[0][1]),4)

            Time_ERI     = round(data[0][0],4)
            CPU_ERI      = round(data[0][1],4)
            Time_flush   = round(data[0][3],4)
            Time_SCF     = round(data[0][4],4)
            CPU_SCF      = round(data[0][5],4)
            Time_Dav     = round(data[0][6],4)
            Time_Dav_transpose = round(data[0][8],4)
            CPU_Dav      = round(data[0][7],4)
            if Time_ERI+CPU_ERI+Time_flush+Time_SCF+CPU_SCF+Time_Dav+Time_Dav_transpose+CPU_Dav==0.0:
                print(file, "nodata")
                continue
            print(theory, method, algorithm, molecule, basis, nbf, n_state, n_cpu, n_test, Time_Dav, file)
            row = (' '+str(theory)     +' '*3+
                   ' '+str(method)     +' '*3+
                   ' '+str(algorithm)       +' '+
                   ' '+str(basis)       +' '+
                   ' '+str('%6i' % nbf)   +' '+
                   ' '+str('%6i' % n_cpu)        +' '+
                   ' '+str('%6i' % n_state)      +' '+
                   ' '+str('%6i' % n_test)      +' '+
                   ' '+str(Time_ERI)     +' '*3+
                   ' '+str(Time_full_writing)     +' '*3+
                   ' '+str(CPU_ERI)      +' '*2+
                   ' '+str(Time_flush)   +' '+
                   ' '+str(Time_Dav)     +' '+
                   ' '+str(Time_Dav_transpose)     +' '+
                   ' '+str(file))
            row_scv = [theory,
                       method,
                       algorithm,
                       basis,
                       nbf,
                       n_cpu,
                       n_state,
                       n_test,
                       Time_ERI,
                       Time_full_writing,
                       CPU_ERI,
                       Time_flush,
                       Time_Dav,
                       Time_Dav_transpose,
                       file,]
#           for j in row_scv:
            writer.writerow(row_scv)

            fout.write(row+'\n')
