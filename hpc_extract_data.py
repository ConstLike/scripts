#!/usr/bin/env python3.6
import fileinput
import os
import sys
import numpy as np
import argparse

def extract_data(file):
    filedata = None
    f = open(file, 'r')
    filedata = f.read()
    f.close()
    out = filedata.splitlines()

    dirscf = False
    disk = False

    t_of_ERI = 0.0
    t_cpu_ERI = 0.0
    t_write = 0.0
    t_flush = 0.0
    int_of_ERI = 0
    skip_of_ERI = 0
    t_of_scf = 0.0
    t_cpu_scf = 0.0
    t_util_scf = str(0)
    int_of_scf = 0
    skip_of_scf = 0
    scf_iter = 0
    buf_ncur =0
    buf_j = 0
    buf_size = 0
    t_of_davidson = 0.0
    t_cpu_davidson = 0.0
    t_util_davidson = str(0)
    davidson_int = 0
    davidson_skip = 0
    data_row = []
    i=0
    for il, l in enumerate(out):
        if "dirscf=.t." in l:
            i+=1
            dirscf=True
        elif "dirscf=.f." in l:
            i+=1
            disk=True
        if disk and "Flushing page cache" in l:
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
            # Mount of 2e integrals
            int_of_ERI = int(out[il-6].split()[7])
            # Skiped integrals
            skip_of_ERI = int(out[il-7].split()[4])
        if disk and "DENSITY CHANGE" in l:
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
#           # Total CPU utilization of the first  SCF
            t_util_scf = str(out[il+2].split()[9])
#           # Mount of 2e integrals calc in first SCF stap
        if dirscf and "DENSITY CHANGE" in l:
            # Timing of the first SCF stap
            t_of_scf = float(out[il+3].split()[4])
            # Total CPU time of the first  SCF
            if (str(out[il+1].split()[5])==str("TOTAL")):
                t_cpu_scf = float(out[il+1].split()[4])
            else:
                t_cpu_scf = float(out[il+1].split()[5])
            # Total CPU utilization of the first  SCF
            t_util_scf = str(out[il+2].split()[9])
            # Mount of 2e integrals calc in first SCF stap
            int_of_scf = int(out[il+5].split()[6])
            # Skiped integrals
            skip_of_scf = int(out[il+5].split()[7])

        if disk and "ddd step wall" in l:
            # calc number of SCF iterations
            scf_iter += 1
        if dirscf and "ddd step wall" in l:
            # calc number of SCF iterations
            scf_iter += 1

        if disk and "kkk step wall time:" in l:
            # Timing of the first Devidson iteration
            t_of_davidson = float(out[il].split()[4])
            # CPU time on step
            if (str(out[il-2].split()[5])==str("TOTAL")):
                t_cpu_davidson = float(out[il-2].split()[4])
            else:
                t_cpu_davidson = float(out[il-2].split()[5])
            # CPU utilization of Davidson
            t_util_davidson = str(out[il-1].split()[9])
        if dirscf and "lll total number of" in l:
            # ncur+j*mxbuf
            buf_ncur = int(out[il].split()[6])
            buf_size = int(out[il].split()[7])
            davidson_int = buf_ncur
            davidson_skip = buf_size
        if dirscf and "kkk step wall time:" in l:
            # Timing of the first Devidson iteration
            t_of_davidson = float(out[il].split()[4])
            # CPU time on step
            if (str(out[il-2].split()[5])==str("TOTAL")):
                t_cpu_davidson = float(out[il-2].split()[4])
            else:
                t_cpu_davidson = float(out[il-2].split()[5])
            # CPU utilization of Davidson
            t_util_davidson = str(out[il-1].split()[9])
    row = (t_of_ERI,       #0
           t_cpu_ERI,      #1
           int_of_ERI,     #2
           skip_of_ERI,    #3
           t_write,        #4
           t_flush,        #5
           t_of_scf,       #6
           t_cpu_scf,      #7
           t_util_scf,     #8
           int_of_scf,     #9
           skip_of_scf,    #11
           scf_iter,       #12
           davidson_int,   #13
           davidson_skip,  #14
           t_of_davidson,  #15
           t_cpu_davidson, #16
           t_util_davidson)#17
    data_row.append(row)
    return  data_row

def extract_n_state(file):
    filedata = None
    f = open(file, 'r')
    filedata = f.read()
    f.close()
    out = filedata.splitlines()
    for il, l in enumerate(out):
        if "NSTATE=" in l:
            n_state = out[il].split()[1]
            return n_state

def extract_cpu(file):
    filedata = None
    f = open(file, 'r')
    filedata = f.read()
    f.close()
    out = filedata.splitlines()
    for il, l in enumerate(out):
        if "Initiating" in l:
            cpu = out[il].split()[1]
            return cpu

def extract_basis(file):

    theory = str(file.split("_")[0])
    molecule = file.count('c60')
    bas = file.count('q')
    n_state = extract_n_state(file)
    m_type = file.count('r0')

    cpu = extract_cpu(file)

    if m_type==0:
        memory = str('Direct ')
    elif m_type==1:
        memory = str('Storage')

    ad = False
    c60 = False
    if molecule == 0:
        ad = True
    elif molecule == 1 :
        c60 = True

    n_of_bas_func = 0
    if ad:
        if bas == 1:
            n_of_bas_func = 193
        elif bas == 2:
            n_of_bas_func = 340
        elif bas == 3:
            n_of_bas_func = 427
    elif c60:
        if bas == 1:
            n_of_bas_func = 540
        elif bas == 2:
            n_of_bas_func = 900
    n_cpu = 0
    if file.count('c1')==1:
        n_cpu = 1
    elif file.count('c4')==1:
        n_cpu = 4
    elif file.count('c8')==1:
        n_cpu = 8
    elif file.count('c9')==1:
        n_cpu = 16

    erre_cpu = 0
    if int(cpu) != int(n_cpu):
        erre_cpu = 1
        print("Warning: cpu does not match",file, cpu, n_cpu)


    return theory, n_of_bas_func, n_state, memory, n_cpu

if __name__ == '__main__':

    fout = open('output_file.log', 'w')
    fout.write('\n')
    fout.write( ' '*1+
                'Theory'       +' '*7+
                'Memory'       +' '*7+
                'Time_ERI'     +' '*7+
                'Time_writing' +' '*7+
                'CPU_ERI'      +' '*11+
                'Num_ERI'      +' '*6+
                'Skip_ERI'     +' '*6+
#               'Time_w'       +' '*3+
#               'Time_flush'   +' '*4+
                'Time_SCF'     +' '*5+
                'CPU_SCF'      +' '*2+
                'Util_CPU_SCF' +' '*8+
                'SCF_N_int'    +' '*2+
                'SCF_skip_int' +' '*2+
                'David_int'    +' '*5+
                'David_skip'   +' '*5+
                'Time_Dav_contr'+' '*5+
                'Time_contraction'+' '*5+
                'Time_Dav'     +' '*5+
                'CPU_Dav'      +' '*2+
                'Util_CPU_Dav' +' '*2+
                'N_bas'        +' '*2+
                'N_cpu'        +' '*2+
                'Scheme'       +' '*2+
                'N_state'      +' '*2+
                'log_file\n')

    inputs=open("inputs.log","r")
    files = inputs.readlines()
    for ifile in files:

        file = ifile.split()[0]
        theory, n_bas_func, n_state, memory, n_cpu = extract_basis(file)

        data = extract_data(file)

        print(file)

        strii = file.split('_')
        name_scheme = str(strii[1])

        mol = file.count('c60')
        disk_scheme = str()
        if int(mol)==0:
            disk_scheme = str(strii[2])
        elif int(mol)==1:
            disk_scheme = str(strii[3])
        dirscf = False

        if name_scheme==str('1a'):
            scheme = str('IF-D')
        elif name_scheme==str('1b'):
            scheme = str('IFT-D')
        elif name_scheme==str('3a'):
            scheme = str('FI-D')
        elif name_scheme==str('5a'):
            scheme = str('FI-DB')
        elif name_scheme==str('5b'):
            scheme = str('FI-DBk')
        elif name_scheme==str('5t'):
            scheme = str('IFT-DBk')
        elif name_scheme==str('5d'):
            scheme = str('SkipThis')
        elif name_scheme==str('2a') and disk_scheme==str('r01'):
            scheme = str('IF-SH')
        elif name_scheme==str('2b') and disk_scheme==str('r01'):
            scheme = str('IFT-SH')
        elif name_scheme==str('2a') and disk_scheme==str('r05'):
            scheme = str('IF-SS')
        elif name_scheme==str('2b') and disk_scheme==str('r05'):
            scheme = str('IFT-SS')
        elif name_scheme==str('2a') and disk_scheme==str('r0M'):
            scheme = str('IF-SM')
        elif name_scheme==str('2b') and disk_scheme==str('r0M'):
            scheme = str('IFT-SM')
        elif name_scheme==str('4a') and disk_scheme==str('r01'):
            scheme = str('FI-SH')
        elif name_scheme==str('4a') and disk_scheme==str('r05'):
            scheme = str('FI-SS')
        elif name_scheme==str('4a') and disk_scheme==str('r0M'):
            scheme = str('FI-SM')

        if name_scheme==str('1a') or name_scheme==str('1b') or name_scheme==str('1c') or name_scheme==str('3a') or name_scheme==str('5a') or name_scheme==str('5b') or name_scheme==str('5c') or name_scheme==str('5d') or name_scheme==str('5t'):
            dirscf = True
        n_bas_int_1 =0
        n_bas_int_2 =0
        n_bas_int_3 =0
        n_bas_int_4 =0
        n_bas_int_5 =0
        n_bas_skip_1=0
        n_bas_skip_2=0
        n_bas_skip_3=0
        n_bas_skip_4=0
        n_bas_skip_5=0
        if name_scheme==str('5d') and int(mol)==0 and int(file.count('q'))==1:
            n_bas_int_1 =  '%15i' % data[0][12]
            n_bas_skip_1 =  '%12i' % data[0][13]
        elif name_scheme==str('5d') and int(mol)==0 and int(file.count('q'))==2:
            n_bas_int_2 =  '%15i' % data[0][12]
            n_bas_skip_2 =  '%12i' % data[0][13]
        elif name_scheme==str('5d') and int(mol)==0 and int(file.count('q'))==3:
            n_bas_int_3 =  '%15i' % data[0][12]
            n_bas_skip_3 =  '%12i' % data[0][13]
        elif name_scheme==str('5d') and int(mol)==1 and int(file.count('q'))==1:
            n_bas_int_4 =  '%15i' % data[0][12]
            n_bas_skip_4 =  '%12i' % data[0][13]
        elif name_scheme==str('5d') and int(mol)==1 and int(file.count('q'))==2:
            n_bas_int_5 =  '%15i' % data[0][12]
            n_bas_skip_5 =  '%12i' % data[0][13]

        David_int = '%15i' % 0
        David_skip = '%12i' % 0
        if int(mol)==0 and int(file.count('q'))==1:
            if dirscf:
                David_int    = n_bas_int_1
                David_skip   = n_bas_skip_1
        elif int(mol)==0 and int(file.count('q'))==2:
            if dirscf:
                David_int    = n_bas_int_2
                David_skip   = n_bas_skip_2
        elif int(mol)==0 and int(file.count('q'))==3:
            if dirscf:
                David_int    = n_bas_int_3
                David_skip   = n_bas_skip_3
        elif int(mol)==1 and int(file.count('q'))==1:
            if dirscf:
                David_int    = n_bas_int_4
                David_skip   = n_bas_skip_4
        elif int(mol)==1 and int(file.count('q'))==2:
            if dirscf:
                David_int    = n_bas_int_5
                David_skip   = n_bas_skip_5

        time_contr_1_c1 = '%10.2f' % 0.0
        time_contr_2_c1 = '%10.2f' % 0.0
        time_contr_3_c1 = '%10.2f' % 0.0
        time_contr_4_c1 = '%10.2f' % 0.0
        time_contr_5_c1 = '%10.2f' % 0.0
        time_contr_1_c4 = '%10.2f' % 0.0
        time_contr_2_c4 = '%10.2f' % 0.0
        time_contr_3_c4 = '%10.2f' % 0.0
        time_contr_4_c4 = '%10.2f' % 0.0
        time_contr_5_c4 = '%10.2f' % 0.0
        time_contr_1_c8 = '%10.2f' % 0.0
        time_contr_2_c8 = '%10.2f' % 0.0
        time_contr_3_c8 = '%10.2f' % 0.0
        time_contr_4_c8 = '%10.2f' % 0.0
        time_contr_5_c8 = '%10.2f' % 0.0
        time_contr_1_c9 = '%10.2f' % 0.0
        time_contr_2_c9 = '%10.2f' % 0.0
        time_contr_3_c9 = '%10.2f' % 0.0
        time_contr_4_c9 = '%10.2f' % 0.0
        time_contr_5_c9 = '%10.2f' % 0.0
        if n_cpu==1:
            if name_scheme==str('5d') and int(mol)==0 and int(file.count('q'))==1:
                time_contr_1_c1 = '%10.2f' % round(data[0][14],2)
            elif name_scheme==str('5d') and int(mol)==0 and int(file.count('q'))==2:
                time_contr_2_c1 = '%10.2f' % round(data[0][14],2)
            elif name_scheme==str('5d') and int(mol)==0 and int(file.count('q'))==3:
                time_contr_3_c1 = '%10.2f' % round(data[0][14],2)
            elif name_scheme==str('5d') and int(mol)==1 and int(file.count('q'))==1:
                time_contr_4_c1 = '%10.2f' % round(data[0][14],2)
            elif name_scheme==str('5d') and int(mol)==1 and int(file.count('q'))==2:
                time_contr_5_c1 = '%10.2f' % round(data[0][14],2)
        if n_cpu==4:
            if name_scheme==str('5d') and int(mol)==0 and int(file.count('q'))==1:
                time_contr_1_c4 = '%10.2f' % round(data[0][14],2)
            elif name_scheme==str('5d') and int(mol)==0 and int(file.count('q'))==2:
                time_contr_2_c4 = '%10.2f' % round(data[0][14],2)
            elif name_scheme==str('5d') and int(mol)==0 and int(file.count('q'))==3:
                time_contr_3_c4 = '%10.2f' % round(data[0][14],2)
            elif name_scheme==str('5d') and int(mol)==1 and int(file.count('q'))==1:
                time_contr_4_c4 = '%10.2f' % round(data[0][14],2)
            elif name_scheme==str('5d') and int(mol)==1 and int(file.count('q'))==2:
                time_contr_5_c4 = '%10.2f' % round(data[0][14],2)
        if n_cpu==8:
            if name_scheme==str('5d') and int(mol)==0 and int(file.count('q'))==1:
                time_contr_1_c8 = '%10.2f' % round(data[0][14],2)
            elif name_scheme==str('5d') and int(mol)==0 and int(file.count('q'))==2:
                time_contr_2_c8 = '%10.2f' % round(data[0][14],2)
            elif name_scheme==str('5d') and int(mol)==0 and int(file.count('q'))==3:
                time_contr_3_c8 = '%10.2f' % round(data[0][14],2)
            elif name_scheme==str('5d') and int(mol)==1 and int(file.count('q'))==1:
                time_contr_4_c8 = '%10.2f' % round(data[0][14],2)
            elif name_scheme==str('5d') and int(mol)==1 and int(file.count('q'))==2:
                time_contr_5_c8 = '%10.2f' % round(data[0][14],2)
        if n_cpu==16:
            if name_scheme==str('5d') and int(mol)==0 and int(file.count('q'))==1:
                time_contr_1_c9 = '%10.2f' % round(data[0][14],2)
            elif name_scheme==str('5d') and int(mol)==0 and int(file.count('q'))==2:
                time_contr_2_c9 = '%10.2f' % round(data[0][14],2)
            elif name_scheme==str('5d') and int(mol)==0 and int(file.count('q'))==3:
                time_contr_3_c9 = '%10.2f' % round(data[0][14],2)
            elif name_scheme==str('5d') and int(mol)==1 and int(file.count('q'))==1:
                time_contr_4_c9 = '%10.2f' % round(data[0][14],2)
            elif name_scheme==str('5d') and int(mol)==1 and int(file.count('q'))==2:
                time_contr_5_c9 = '%10.2f' % round(data[0][14],2)

        Dav_get_ERI = '%10.2f' % 0.0
        if n_cpu==1:
            if int(mol)==0 and int(file.count('q'))==1:
                if dirscf:
                    Dav_get_ERI= time_contr_1_c1
            elif int(mol)==0 and int(file.count('q'))==2:
                if dirscf:
                    Dav_get_ERI= time_contr_2_c1
            elif int(mol)==0 and int(file.count('q'))==3:
                if dirscf:
                    Dav_get_ERI= time_contr_3_c1
            elif int(mol)==1 and int(file.count('q'))==1:
                if dirscf:
                    Dav_get_ERI= time_contr_4_c1
            elif int(mol)==1 and int(file.count('q'))==2:
                if dirscf:
                    Dav_get_ERI= time_contr_5_c1
        if n_cpu==4:
            if int(mol)==0 and int(file.count('q'))==1:
                if dirscf:
                    Dav_get_ERI= time_contr_1_c4
            elif int(mol)==0 and int(file.count('q'))==2:
                if dirscf:
                    Dav_get_ERI= time_contr_2_c4
            elif int(mol)==0 and int(file.count('q'))==3:
                if dirscf:
                    Dav_get_ERI= time_contr_3_c4
            elif int(mol)==1 and int(file.count('q'))==1:
                if dirscf:
                    Dav_get_ERI= time_contr_4_c4
            elif int(mol)==1 and int(file.count('q'))==2:
                if dirscf:
                    Dav_get_ERI= time_contr_5_c4
        if n_cpu==8:
            if int(mol)==0 and int(file.count('q'))==1:
                if dirscf:
                    Dav_get_ERI= time_contr_1_c8
            elif int(mol)==0 and int(file.count('q'))==2:
                if dirscf:
                    Dav_get_ERI= time_contr_2_c8
            elif int(mol)==0 and int(file.count('q'))==3:
                if dirscf:
                    Dav_get_ERI= time_contr_3_c8
            elif int(mol)==1 and int(file.count('q'))==1:
                if dirscf:
                    Dav_get_ERI= time_contr_4_c8
            elif int(mol)==1 and int(file.count('q'))==2:
                if dirscf:
                    Dav_get_ERI= time_contr_5_c8
        if n_cpu==16:
            if int(mol)==0 and int(file.count('q'))==1:
                if dirscf:
                    Dav_get_ERI= time_contr_1_c9
            elif int(mol)==0 and int(file.count('q'))==2:
                if dirscf:
                    Dav_get_ERI= time_contr_2_c9
            elif int(mol)==0 and int(file.count('q'))==3:
                if dirscf:
                    Dav_get_ERI= time_contr_3_c9
            elif int(mol)==1 and int(file.count('q'))==1:
                if dirscf:
                    Dav_get_ERI= time_contr_4_c9
            elif int(mol)==1 and int(file.count('q'))==2:
                if dirscf:
                    Dav_get_ERI= time_contr_5_c9

        Time_Dav_conv= '%10.2f' % 0.0
        Time_full_writing = '%10.2f' % 0.0
        if dirscf:
            Time_Dav_conv = '%10.2f' % round(float(data[0][14])-float(Dav_get_ERI),2)
        if dirscf==False:
            # Time_ERI+Time_w+Time_flush-CPU_ERI
            Time_full_writing = '%10.2f' % round(float(data[0][0])+float(data[0][4])+float(data[0][5])-float(data[0][1]),2)


        Time_ERI     = '%10.2f' % round(data[0][0],2)
        CPU_ERI      = '%10.2f' % round(data[0][1],2)
        Num_ERI      = '%15i' % data[0][2]
        Skip_ERI     = '%12i' % data[0][3]
#       Time_w       = '%10.4f' % round(data[0][4],4)
#       Time_flush   = '%10.4f' % round(data[0][5],4)
        Time_SCF     = '%10.2f' % round(data[0][6],2)
        CPU_SCF      = '%10.2f' % round(data[0][7],2)
        Util_CPU_SCF = '%10.2f' % round(float(data[0][8].split('%')[0]),2)
        SCF_N_int    = '%15i' % data[0][9]
        SCF_skip_int = '%12i' % data[0][10]
#       N_SCF_steps  = '%3i' % data[0][11]
#       David_int    = '%15i' % data[0][12]
#       David_skip   = '%12i' % data[0][13]
        Time_Dav     = '%10.2f' % round(data[0][14],2)
        CPU_Dav      = '%10.2f' % round(data[0][15],2)
        Util_CPU_Dav = '%10.2f' % round(float(data[0][16].split('%')[0]),2)
        row = (' '+str(theory)     +' '*3+
               ' '+str(memory)     +' '*3+
               ' '+str(Time_ERI)     +' '*3+
               ' '+str(Time_full_writing)     +' '*3+
               ' '+str(CPU_ERI)      +' '*2+
               ' '+str(Num_ERI)      +' '+
               ' '+str(Skip_ERI)     +' '+
#              ' '+str(Time_w)       +' '*2+
#              ' '+str(Time_flush)   +' '+
               ' '+str(Time_SCF)     +' '+
               ' '+str(CPU_SCF)      +' '+
               ' '+str(Util_CPU_SCF) +' '+
               ' '+str(SCF_N_int)    +' '+
               ' '+str(SCF_skip_int) +' '*9+
#              ' '+str(N_SCF_steps)  +' '+
               ' '+str(David_int)    +' '+
               ' '+str(David_skip)   +' '+
               ' '+str(Dav_get_ERI)+' '+
               ' '+str(Time_Dav_conv)+' '+
               ' '+str(Time_Dav)     +' '+
               ' '+str(CPU_Dav)      +' '+
               ' '+str(Util_CPU_Dav) +' '+
               ' '+str(n_bas_func)   +' '+
               ' '+str(n_cpu)        +' '+
               ' '+str(scheme)       +' '+
               ' '+str(n_state)      +' '+
               ' '+str(file))

        fout.write(row+'\n')
