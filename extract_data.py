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

    times = []
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
    row = (t_of_ERI,
           t_cpu_ERI,
           int_of_ERI,
           skip_of_ERI,
           t_write,
           t_flush,
           t_of_scf,
           t_cpu_scf,
           t_util_scf,
           int_of_scf,
           skip_of_scf,
           scf_iter,
           davidson_int,
           davidson_skip,
           t_of_davidson,
           t_cpu_davidson,
           t_util_davidson,
           file,
          )
    data_row.append(row)
    return  data_row
#       if disk:
#           row = (
#                   )



#   if dirscf | i==1:
#       print("T_SCF CPU_SCF Tot_util_SCF Two_e_int Skiped_2e_int N_SCF_steps T_Davids CPU_David Tot_Util_David")
#   if disk:
#       scf_iter = scf_iter-3
#   if Disk:
#    print( "time SCF:", t_of_scf,'\n',
#            "Step CPU time:", t_cpu_scf,'\n',
#            "Total util scf:", t_util_scf,'\n',
#             "2e int:",int_of_scf,'\n',
#      "2e int skiped:",skip_of_scf,'\n',
#"number of SCF steps:",scf_iter,'\n',
#     "Timing Davidson",t_of_davidson)

#       if "step wall" in l:
#           step_time  = float(out[il].split()[4])
#           times.append(step_time)
#   return times


if __name__ == '__main__':

#   files=('mrsf_2a_c60_r01_q___c4_t0.log',)
    files=(
# 5d new code + buffer + kind=2 Timing ERI
'mrsf_5d_q___c1_t0.log',
'mrsf_5d_qq__c1_t0.log',
'mrsf_5d_qqq_c1_t0.log',
'mrsf_5d_q___c4_t0.log',
'mrsf_5d_qq__c4_t0.log',
'mrsf_5d_qqq_c4_t0.log',
'mrsf_5d_q___c8_t0.log',
'mrsf_5d_qq__c8_t0.log',
'mrsf_5d_qqq_c8_t0.log',
'mrsf_5d_q___c9_t0.log',
'mrsf_5d_qq__c9_t0.log',
'mrsf_5d_qqq_c9_t0.log',
# HDD
# 2a old code + disk + r01
'mrsf_2a_r01_q___c1_t0.log',
'mrsf_2a_r01_qq__c1_t0.log',
'mrsf_2a_r01_qqq_c1_t0.log',
'mrsf_2a_r01_q___c4_t0.log',
'mrsf_2a_r01_qq__c4_t0.log',
'mrsf_2a_r01_qqq_c4_t0.log',
'mrsf_2a_r01_q___c8_t0.log',
'mrsf_2a_r01_qq__c8_t0.log',
'mrsf_2a_r01_qqq_c8_t0.log',
'mrsf_2a_r01_q___c9_t0.log',
'mrsf_2a_r01_qq__c9_t0.log',
'mrsf_2a_r01_qqq_c9_t0.log',
 # 2b old code + disk + r01
'mrsf_2b_r01_q___c1_t0.log',
'mrsf_2b_r01_qq__c1_t0.log',
'mrsf_2b_r01_qqq_c1_t0.log',
'mrsf_2b_r01_q___c4_t0.log',
'mrsf_2b_r01_qq__c4_t0.log',
'mrsf_2b_r01_qqq_c4_t0.log',
'mrsf_2b_r01_q___c8_t0.log',
'mrsf_2b_r01_qq__c8_t0.log',
'mrsf_2b_r01_qqq_c8_t0.log',
'mrsf_2b_r01_q___c9_t0.log',
'mrsf_2b_r01_qq__c9_t0.log',
'mrsf_2b_r01_qqq_c9_t0.log',
# 4a new code + disk + r01
'mrsf_4a_r01_q___c1_t0.log',
'mrsf_4a_r01_qq__c1_t0.log',
'mrsf_4a_r01_qqq_c1_t0.log',
'mrsf_4a_r01_q___c4_t0.log',
'mrsf_4a_r01_qq__c4_t0.log',
'mrsf_4a_r01_qqq_c4_t0.log',
'mrsf_4a_r01_q___c8_t0.log',
'mrsf_4a_r01_qq__c8_t0.log',
'mrsf_4a_r01_qqq_c8_t0.log',
'mrsf_4a_r01_q___c9_t0.log',
'mrsf_4a_r01_qq__c9_t0.log',
'mrsf_4a_r01_qqq_c9_t0.log',
# SSD
# 2a old code + disk + r05
'mrsf_2a_r05_q___c1_t0.log',
'mrsf_2a_r05_qq__c1_t0.log',
'mrsf_2a_r05_qqq_c1_t0.log',
'mrsf_2a_r05_q___c4_t0.log',
'mrsf_2a_r05_qq__c4_t0.log',
'mrsf_2a_r05_qqq_c4_t0.log',
'mrsf_2a_r05_q___c8_t0.log',
'mrsf_2a_r05_qq__c8_t0.log',
'mrsf_2a_r05_qqq_c8_t0.log',
'mrsf_2a_r05_q___c9_t0.log',
'mrsf_2a_r05_qq__c9_t0.log',
'mrsf_2a_r05_qqq_c9_t0.log',
# 2b old code + disk + r05
'mrsf_2b_r05_q___c1_t0.log',
'mrsf_2b_r05_qq__c1_t0.log',
'mrsf_2b_r05_qqq_c1_t0.log',
'mrsf_2b_r05_q___c4_t0.log',
'mrsf_2b_r05_qq__c4_t0.log',
'mrsf_2b_r05_qqq_c4_t0.log',
'mrsf_2b_r05_q___c8_t0.log',
'mrsf_2b_r05_qq__c8_t0.log',
'mrsf_2b_r05_qqq_c8_t0.log',
'mrsf_2b_r05_q___c9_t0.log',
'mrsf_2b_r05_qq__c9_t0.log',
'mrsf_2b_r05_qqq_c9_t0.log',
# 4a new code + disk + r05
'mrsf_4a_r05_q___c1_t0.log',
'mrsf_4a_r05_qq__c1_t0.log',
'mrsf_4a_r05_qqq_c1_t0.log',
'mrsf_4a_r05_q___c4_t0.log',
'mrsf_4a_r05_qq__c4_t0.log',
'mrsf_4a_r05_qqq_c4_t0.log',
'mrsf_4a_r05_q___c8_t0.log',
'mrsf_4a_r05_qq__c8_t0.log',
'mrsf_4a_r05_qqq_c8_t0.log',
'mrsf_4a_r05_q___c9_t0.log',
'mrsf_4a_r05_qq__c9_t0.log',
'mrsf_4a_r05_qqq_c9_t0.log',
# DRAM
# 2a old code + disk + r0M
'mrsf_2a_r0M_q___c1_t0.log',
'mrsf_2a_r0M_qq__c1_t0.log',
'mrsf_2a_r0M_qqq_c1_t0.log',
'mrsf_2a_r0M_q___c4_t0.log',
'mrsf_2a_r0M_qq__c4_t0.log',
'mrsf_2a_r0M_qqq_c4_t0.log',
'mrsf_2a_r0M_q___c8_t0.log',
'mrsf_2a_r0M_qq__c8_t0.log',
'mrsf_2a_r0M_qqq_c8_t0.log',
'mrsf_2a_r0M_q___c9_t0.log',
'mrsf_2a_r0M_qq__c9_t0.log',
'mrsf_2a_r0M_qqq_c9_t0.log',
# 2b old code + disk + r0M
'mrsf_2b_r0M_q___c1_t0.log',
'mrsf_2b_r0M_qq__c1_t0.log',
'mrsf_2b_r0M_qqq_c1_t0.log',
'mrsf_2b_r0M_q___c4_t0.log',
'mrsf_2b_r0M_qq__c4_t0.log',
'mrsf_2b_r0M_qqq_c4_t0.log',
'mrsf_2b_r0M_q___c8_t0.log',
'mrsf_2b_r0M_qq__c8_t0.log',
'mrsf_2b_r0M_qqq_c8_t0.log',
'mrsf_2b_r0M_q___c9_t0.log',
'mrsf_2b_r0M_qq__c9_t0.log',
'mrsf_2b_r0M_qqq_c9_t0.log',
# 4a new code + disk + r0M
'mrsf_4a_r0M_q___c1_t0.log',
'mrsf_4a_r0M_qq__c1_t0.log',
'mrsf_4a_r0M_qqq_c1_t0.log',
'mrsf_4a_r0M_q___c4_t0.log',
'mrsf_4a_r0M_qq__c4_t0.log',
'mrsf_4a_r0M_qqq_c4_t0.log',
'mrsf_4a_r0M_q___c8_t0.log',
'mrsf_4a_r0M_qq__c8_t0.log',
'mrsf_4a_r0M_qqq_c8_t0.log',
'mrsf_4a_r0M_q___c9_t0.log',
'mrsf_4a_r0M_qq__c9_t0.log',
'mrsf_4a_r0M_qqq_c9_t0.log',
# DIRECT
# 1a old code + direct
'mrsf_1a_q___c1_t0.log',
'mrsf_1a_qq__c1_t0.log',
'mrsf_1a_qqq_c1_t0.log',
'mrsf_1a_q___c4_t0.log',
'mrsf_1a_qq__c4_t0.log',
'mrsf_1a_qqq_c4_t0.log',
'mrsf_1a_q___c8_t0.log',
'mrsf_1a_qq__c8_t0.log',
'mrsf_1a_qqq_c8_t0.log',
'mrsf_1a_q___c9_t0.log',
'mrsf_1a_qq__c9_t0.log',
'mrsf_1a_qqq_c9_t0.log',
# 1b old code+ transpose + direct
'mrsf_1b_q___c1_t0.log',
'mrsf_1b_qq__c1_t0.log',
'mrsf_1b_qqq_c1_t0.log',
'mrsf_1b_q___c4_t0.log',
'mrsf_1b_qq__c4_t0.log',
'mrsf_1b_qqq_c4_t0.log',
'mrsf_1b_q___c8_t0.log',
'mrsf_1b_qq__c8_t0.log',
'mrsf_1b_qqq_c8_t0.log',
'mrsf_1b_q___c9_t0.log',
'mrsf_1b_qq__c9_t0.log',
'mrsf_1b_qqq_c9_t0.log',
# 3a new code + direct
'mrsf_3a_q___c1_t0.log',
'mrsf_3a_qq__c1_t0.log',
'mrsf_3a_qqq_c1_t0.log',
'mrsf_3a_q___c4_t0.log',
'mrsf_3a_qq__c4_t0.log',
'mrsf_3a_qqq_c4_t0.log',
'mrsf_3a_q___c8_t0.log',
'mrsf_3a_qq__c8_t0.log',
'mrsf_3a_qqq_c8_t0.log',
'mrsf_3a_q___c9_t0.log',
'mrsf_3a_qq__c9_t0.log',
'mrsf_3a_qqq_c9_t0.log',
# 5a new code + buffer
'mrsf_5a_q___c1_t0.log',
'mrsf_5a_qq__c1_t0.log',
'mrsf_5a_qqq_c1_t0.log',
'mrsf_5a_q___c4_t0.log',
'mrsf_5a_qq__c4_t0.log',
'mrsf_5a_qqq_c4_t0.log',
'mrsf_5a_q___c8_t0.log',
'mrsf_5a_qq__c8_t0.log',
'mrsf_5a_qqq_c8_t0.log',
'mrsf_5a_q___c9_t0.log',
'mrsf_5a_qq__c9_t0.log',
'mrsf_5a_qqq_c9_t0.log',
# 5b new code + buffer + kind=2
'mrsf_5b_q___c1_t0.log',
'mrsf_5b_qq__c1_t0.log',
'mrsf_5b_qqq_c1_t0.log',
'mrsf_5b_q___c4_t0.log',
'mrsf_5b_qq__c4_t0.log',
'mrsf_5b_qqq_c4_t0.log',
'mrsf_5b_q___c8_t0.log',
'mrsf_5b_qq__c8_t0.log',
'mrsf_5b_qqq_c8_t0.log',
'mrsf_5b_q___c9_t0.log',
'mrsf_5b_qq__c9_t0.log',
'mrsf_5b_qqq_c9_t0.log',
)

    fout = open('output_file.log', 'w')
    fout.write('\n')
    fout.write(' '*3+'Time_ERI'+' '*7+
               'CPU_ERI'        +' '*11+
               'Num_ERI'        +' '*6+
               'Skip_ERI'       +' '*6+
               'Time_w'         +' '*3+
               'Time_flush'     +' '*4+
               'Time_SCF'       +' '*5+
               'CPU_SCF'        +' '*2+
               'Util_CPU_SCF'   +' '*8+
               'SCF_N_int'      +' '*2+
               'SCF_skip_int'   +' '*2+
               'N_SCF_steps'    +' '*4+
               'David_int'      +' '*5+
               'David_skip'     +' '*5+
               'Time_Dav'       +' '*5+
               'CPU_Dav'        +' '*2+
               'Util_CPU_Dav'   +' '*2+
               'N_bas'          +' '*2+
               'N_cpu'          +' '*2+
               'Scheme'         +' '*2+
               'N_state'        +' '*2+
               'log_file\n')
    data = []
    data2 = []
    for i in files:
        data =  extract_data(i)
        strii = i.split('_')
        if int(i.count('n'))==0:
            n_state = 10
            name_cpu = str(strii[len(strii)-2])
        if int(i.count('n'))==1:
            if strii[len(strii)-2]==str('n1'):
                n_state = 1
            elif strii[len(strii)-2]==str('n5'):
                n_state = 5
            name_cpu = str(strii[len(strii)-3])
        name_scheme = str(strii[1])
        if int(i.count('6'))==0:
            disk_scheme = str(strii[2])
        elif int(i.count('6'))==1:
            disk_scheme = str(strii[3])
        dirscf = False

        if name_scheme==str('1a'):
            scheme = str('DIF')
        elif name_scheme==str('1b'):
            scheme = str('DIFT')
        elif name_scheme==str('3a'):
            scheme = str('DFI')
        elif name_scheme==str('5a'):
            scheme = str('DFIB')
        elif name_scheme==str('5b'):
            scheme = str('DFIBk')
        elif name_scheme==str('5d'):
            scheme = str('SkipThis')

        if name_scheme==str('2a') and disk_scheme==str('r01'):
            scheme = str('SIFH')
        elif name_scheme==str('2b') and disk_scheme==str('r01'):
            scheme = str('SIFTH')
        elif name_scheme==str('2a') and disk_scheme==str('r05'):
            scheme = str('SIFS')
        elif name_scheme==str('2b') and disk_scheme==str('r05'):
            scheme = str('SIFTS')
        elif name_scheme==str('2a') and disk_scheme==str('r0M'):
            scheme = str('SIFM')
        elif name_scheme==str('2b') and disk_scheme==str('r0M'):
            scheme = str('SIFTM')
        elif name_scheme==str('4a') and disk_scheme==str('r01'):
            scheme = str('SFIH')
        elif name_scheme==str('4a') and disk_scheme==str('r05'):
            scheme = str('SFIS')
        elif name_scheme==str('4a') and disk_scheme==str('r0M'):
            scheme = str('SFIM')


        if name_scheme==str('1a') or name_scheme==str('1b') or name_scheme==str('1c') or name_scheme==str('3a') or name_scheme==str('5a') or name_scheme==str('5b') or name_scheme==str('5c') or name_scheme==str('5d') :
            dirscf = True
        if int(i.count('6'))==0:
            sss = str('c1')
        elif int(i.count('6'))==1:
            sss = str('c4')
        if name_cpu == sss:
            n_cpu = 1
            if name_scheme==str('5d') and int(i.count('6'))==0 and int(i.count('q'))==1:
                n_bas_int_1 =  '%15i' % data[0][12]
                n_bas_skip_1 =  '%12i' % data[0][13]
            elif name_scheme==str('5d') and int(i.count('6'))==0 and int(i.count('q'))==2:
                n_bas_int_2 =  '%15i' % data[0][12]
                n_bas_skip_2 =  '%12i' % data[0][13]
            elif name_scheme==str('5d') and int(i.count('6'))==0 and int(i.count('q'))==3:
                n_bas_int_3 =  '%15i' % data[0][12]
                n_bas_skip_3 =  '%12i' % data[0][13]
            elif name_scheme==str('5d') and int(i.count('6'))==1 and int(i.count('q'))==1:
                n_bas_int_4 =  '%15i' % data[0][12]
                n_bas_skip_4 =  '%12i' % data[0][13]
            elif name_scheme==str('5d') and int(i.count('6'))==1 and int(i.count('q'))==2:
                n_bas_int_5 =  '%15i' % data[0][12]
                n_bas_skip_5 =  '%12i' % data[0][13]
        elif name_cpu == str('c4'):
            n_cpu = 4
        elif name_cpu == str('c8'):
            n_cpu = 8
        elif name_cpu == str('c9'):
            n_cpu = 16

        David_int = '%15i' % 0
        David_skip = '%12i' % 0
        if int(i.count('6'))==0 and int(i.count('q'))==1:
            n_bas = 193
            if dirscf:
                David_int    = n_bas_int_1
                David_skip   = n_bas_skip_1
        elif int(i.count('6'))==0 and int(i.count('q'))==2:
            n_bas = 340
            if dirscf:
                David_int    = n_bas_int_2
                David_skip   = n_bas_skip_2
        elif int(i.count('6'))==0 and int(i.count('q'))==3:
            n_bas = 427
            if dirscf:
                David_int    = n_bas_int_3
                David_skip   = n_bas_skip_3
        elif int(i.count('6'))==1 and int(i.count('q'))==1:
            n_bas = 540
            if dirscf:
                David_int    = n_bas_int_4
                David_skip   = n_bas_skip_4
        elif int(i.count('6'))==1 and int(i.count('q'))==2:
            n_bas = 900
            if dirscf:
                David_int    = n_bas_int_5
                David_skip   = n_bas_skip_5

        Time_ERI     = '%10.2f' % round(data[0][0],2)
        CPU_ERI      = '%10.2f' % round(data[0][1],2)
        Num_ERI      = '%15i' % data[0][2]
        Skip_ERI     = '%12i' % data[0][3]
        Time_w       = '%10.4f' % round(data[0][4],4)
        Time_flush   = '%10.4f' % round(data[0][5],4)
        Time_SCF     = '%10.2f' % round(data[0][6],2)
        CPU_SCF      = '%10.2f' % round(data[0][7],2)
        Util_CPU_SCF = '%10.2f' % round(float(data[0][8].split('%')[0]),2)
        SCF_N_int    = '%15i' % data[0][9]
        SCF_skip_int = '%12i' % data[0][10]
        N_SCF_steps  = '%3i' % data[0][11]
#       David_int    = '%15i' % data[0][12]
#       David_skip   = '%12i' % data[0][13]
        Time_Dav     = '%10.2f' % round(data[0][14],2)
        CPU_Dav      = '%10.2f' % round(data[0][15],2)
        Util_CPU_Dav = '%10.2f' % round(float(data[0][16].split('%')[0]),2)
        log_file     = data[0][17]
        row = (' '+str(Time_ERI)     +' '*3+
               ' '+str(CPU_ERI)      +' '*2+
               ' '+str(Num_ERI)      +' '+
               ' '+str(Skip_ERI)     +' '+
               ' '+str(Time_w)       +' '*2+
               ' '+str(Time_flush)   +' '+
               ' '+str(Time_SCF)     +' '+
               ' '+str(CPU_SCF)      +' '+
               ' '+str(Util_CPU_SCF) +' '+
               ' '+str(SCF_N_int)    +' '+
               ' '+str(SCF_skip_int) +' '*9+
               ' '+str(N_SCF_steps)  +' '+
               ' '+str(David_int)    +' '+
               ' '+str(David_skip)   +' '+
               ' '+str(Time_Dav)     +' '+
               ' '+str(CPU_Dav)      +' '+
               ' '+str(Util_CPU_Dav) +' '+
               ' '+str(n_bas)        +' '+
               ' '+str(n_cpu)        +' '+
               ' '+str(scheme)       +' '+
               ' '+str(n_state)      +' '+
               ' '+str(log_file))

        fout.write(row+'\n')



    for i in enumerate(data2):
        print(i[1][2])


#   for f in files:
#       q = str(f.count('q'))
#       fout = open(f, 'w')
#       fout.write(' $contrl scftyp=rohf runtyp=energy dfttyp=bhhlyp icharg=0\n')
#       fout.write(' coord=unique tddft=mrsf maxit=200 mult=3 $end\n')
#       fout.write(' $tddft nstate=10 iroot=1  mult=1 $end\n')
#       fout.write(' $scf dirscf=.t. soscf=.f. diis=.t. swdiis=1e-4 damp=.t. $end\n')
#       if q=='1' in f:
#           fout.write(' $basis gbasis=n31 ngauss=6 $end\n')
#       elif q=='2':
#           fout.write(' $basis gbasis=n31 ngauss=6 ndfunc=1 npfunc=1 $end\n')
#       elif q=='3':
#           fout.write(' $basis gbasis=n311 ngauss=6 ndfunc=1 npfunc=1 $end\n')
#       fout.write(' $system timlim=999999100 mwords=1000 $end\n')
#       fout.write(' $data\n')
#       fout.write(' C4N3H5O\n')
#       fout.write(' C1\n')
#       fout.write(' NITROGEN    7.0  -0.0196704359  -2.9127146110  -2.6547223065\n')
#       fout.write(' CARBON      6.0  -0.0186110100  -3.7207358002  -3.7245317930\n')
#       fout.write(' NITROGEN    7.0  -0.0154742344  -3.3690707058  -5.0016803975\n')
#       fout.write(' CARBON      6.0  -0.0130183319  -2.0527838331  -5.1443063814\n')
#       fout.write(' CARBON      6.0  -0.0137521409  -1.1028192250  -4.1345104801\n')
#       fout.write(' CARBON      6.0  -0.0173536584  -1.5954449653  -2.8141697224\n')
#       fout.write(' NITROGEN    7.0  -0.0092877571  -1.3198577569  -6.2977090971\n')
#       fout.write(' CARBON      6.0  -0.0078603737   0.0005330868  -5.9259711733\n')
#       fout.write(' NITROGEN    7.0  -0.0104384739   0.1712612473  -4.6422642634\n')
#       fout.write(' NITROGEN    7.0  -0.0185155179  -0.7928608979  -1.7520516098\n')
#       fout.write(' HYDROGEN    1.0  -0.0205082085  -4.7749583598  -3.5004389854\n')
#       fout.write(' HYDROGEN    1.0  -0.0076510414  -1.6900092700  -7.2270323696\n')
#       fout.write(' HYDROGEN    1.0  -0.0047777606   0.7883504402  -6.6553945627\n')
#       fout.write(' HYDROGEN    1.0  -0.0154025989   0.1967177324  -1.8899365280\n')
#       fout.write(' HYDROGEN    1.0  -0.0195013360  -1.1760861723  -0.8170305192\n')
#       fout.write(' NITROGEN    7.0  -0.0173003103  -4.1710147104  -0.0651494083\n')
#       fout.write(' CARBON      6.0  -0.0147866384  -5.5398831145  -0.0633542013\n')
#       fout.write(' NITROGEN    7.0  -0.0112183311  -6.0877904918   1.1999096435\n')
#       fout.write(' CARBON      6.0  -0.0100099499  -5.3394652660   2.3469754911\n')
#       fout.write(' CARBON      6.0  -0.0125109984  -4.0006454867   2.3329139223\n')
#       fout.write(' CARBON      6.0  -0.0163911424  -3.3404577072   1.0315418963\n')
#       fout.write(' OXYGEN      8.0  -0.0186481313  -2.1287948060   0.8991093601\n')
#       fout.write(' OXYGEN      8.0  -0.0156025619  -6.2161571586  -1.0630381200\n')
#       fout.write(' CARBON      6.0  -0.0115923245  -3.1465966796   3.5580984141\n')
#       fout.write(' HYDROGEN    1.0  -0.0193579284  -3.7241793650  -0.9929669859\n')
#       fout.write(' HYDROGEN    1.0  -0.0093020146  -7.0882525243   1.2332302067\n')
#       fout.write(' HYDROGEN    1.0  -0.0069318826  -5.9052837780   3.2631105486\n')
#       fout.write(' HYDROGEN    1.0   0.8573458044  -2.4937424480   3.5746213068\n')
#       fout.write(' HYDROGEN    1.0  -0.0036789407  -3.7549517801   4.4579939768\n')
#       fout.write(' HYDROGEN    1.0  -0.8878392202  -2.5037694166   3.5834492655\n')
#       fout.write(' $end\n')







##kegms = []
##ikegms = 'kegms -q trd '
#
##kegms.append('#!/bin/bash')
#
#filedata = None
#for file in files:
#    f = open(file, 'r')
#    inp = 'so-O-'
#    filedata = f.read()
#    f.close()
#    ii=0
#    for l in GBASIS_O:
#        j = GBASIS_out_O[ii]
#        ii+=1
#        for k in DFTTYP_data:
#            outdata = filedata.replace('CCD', l).replace('BHHLYP', k)
#            outp = inp+k+'-'+j
#            out = inp+k+'-'+j+'.inp'
#            kegms.append( ikegms+outp )
#            fout = open(out,'w')
#            fout.write(outdata)
#            fout.close()
#
#    filedata = None
#    d = open('mrsf-soc-O-SBKJC.inp', 'r')
#    inp = 'so-O-'
#    filedata = d.read()
#    d.close()
#    for k in DFTTYP_data:
#        outdata = filedata.replace('BHHLYP', k)
#        outp = inp+k+'-SBKJC'
#        out = inp+k+'-SBKJC.inp'
#        kegms.append( ikegms+outp )
#        fout = open(out,'w')
#        fout.write(outdata)
#        fout.close()
#
#    for k in kegms:
#        print(k, sep='\n')
#
#    #filedata = None
#    #f = open('mrsf-soc-Sn-draft2.inp', 'r')
#    #inp = 'so-Sn-'
#    #filedata = f.read()
#    #f.close()
#    #ii=0
#    #for l in GBASIS_Sn:
#    #    j = GBASIS_out_Sn[ii]
#    #    ii+=1
#    #    for k in DFTTYP_data:
#    #        outdata = filedata.replace('CCD', l).replace('BHHLYP', k)
#    #        outp = inp+k+'-'+j+'-DK'
#    #        out = inp+k+'-'+j+'-DK.inp'
#    #        print (outp)
#    #        fout = open(out,'w')
#    #        fout.write(outdata)
#    #        fout.close()
#    #
#    #
#    #filedata = None
#    #f = open('mrsf-soc-Ge-draft.inp', 'r')
#    #inp = 'so-Ge-'
#    #filedata = f.read()
#    #f.close()
#    #ii=0
#    #for l in GBASIS_Ge:
#    #    j = GBASIS_out_Ge[ii]
#    #    ii+=1
#    #    for k in DFTTYP_data:
#    #        outdata = filedata.replace('CCD', l).replace('BHHLYP', k)
#    #        outp = inp+k+'-'+j
#    #        out = inp+k+'-'+j+'.inp'
#    #        print (outp)
#    #        fout = open(out,'w')
#    #        fout.write(outdata)
#    #        fout.close()
#    #
#    #filedata = None
#    #d = open('mrsf-soc-Si-SBKJC.inp', 'r')
#    #inp = 'so-Si-'
#    #filedata = d.read()
#    #d.close()
#    #for k in DFTTYP_data:
#    #    outdata = filedata.replace('BHHLYP', k)
#    #    outp = inp+k+'-SBKJC'
#    #    out = inp+k+'-SBKJC.inp'
#    #    print (outp)
#    #    fout = open(out,'w')
#    #    fout.write(outdata)
#    #    fout.close()
#    #
#    #filedata = None
#    #d = open('mrsf-soc-Ge-SBKJC.inp', 'r')
#    #inp = 'so-Ge-'
#    #filedata = d.read()
#    #d.close()
#    #for k in DFTTYP_data:
#    #    outdata = filedata.replace('BHHLYP', k)
#    #    outp = inp+k+'-SBKJC'
#    #    out = inp+k+'-SBKJC.inp'
#    #    print (outp)
#    #    fout = open(out,'w')
#    #    fout.write(outdata)
#    #    fout.close()
#    #
#    #filedata = None
#    #d = open('mrsf-soc-Sn-SBKJC.inp', 'r')
#    #inp = 'so-Sn-'
#    #filedata = d.read()
#    #d.close()
#    #for k in DFTTYP_data:
#    #    outdata = filedata.replace('BHHLYP', k)
#    #    outp = inp+k+'-SBKJC'
#    #    out = inp+k+'-SBKJC.inp'
#    #    print (outp)
#    #    fout = open(out,'w')
#    #    fout.write(outdata)
#    #    fout.close
#    #
#    #filedata = None
#    #d = open('mrsf-soc-Sn-def2-TZVPP.inp', 'r')
#    #inp = 'so-Sn-'
#    #filedata = d.read()
#    #d.close()
#    #for k in DFTTYP_data:
#    #    outdata = filedata.replace('BHHLYP', k)
#    #    outp = inp+k+'-def2-TZVPP'
#    #    out = inp+k+'-def2-TZVPP.inp'
#    #    print (outp)
#    #    fout = open(out,'w')
#    #    fout.write(outdata)
#    #    fout.close
#    #
#    #filedata = None
#    #f = open('mrsf-soc-Sn-def2-TZVPP.inp', 'r')
#    #inp = 'so-Sn-'
#    #filedata = f.read()
#    #f.close()
#    #ii=0
#    #for l in GBASIS_def:
#    #    j = GBASIS_out_def[ii]
#    #    ii+=1
#    #    for k in DFTTYP_data:
#    #        outdata = filedata.replace('df2TZVPP', l).replace('BHHLYP', k)
#    #        outp = inp+k+'-'+j
#    #        out = inp+k+'-'+j+'.inp'
#    #        print (outp)
#    #        fout = open(out,'w')
#    #        fout.write(outdata)
#    #        fout.close()
#    #
#    #filedata = None
#    #f = open('mrsf-soc-Ge-cc-pVDZ-pp.inp', 'r')
#    #inp = 'so-Ge-'
#    #filedata = f.read()
#    #f.close()
#    #ii=0
#    #for l in GBASIS_PP:
#    #    j = GBASIS_out_PP[ii]
#    #    ii+=1
#    #    for k in DFTTYP_data:
#    #        outdata = filedata.replace('ccpVDZpp', l).replace('BHHLYP', k)
#    #        outp = inp+k+'-'+j
#    #        out = inp+k+'-'+j+'.inp'
#    #        print (outp)
#    #        fout = open(out,'w')
#    #        fout.write(outdata)
#    #        fout.close()
#    #
#    #filedata = None
#    #f = open('mrsf-soc-Sn-cc-pVDZ-pp.inp', 'r')
#    #inp = 'so-Sn-'
#    #filedata = f.read()
#    #f.close()
#    #ii=0
#    #for l in GBASIS_PP:
#    #    j = GBASIS_out_PP[ii]
#    #    ii+=1
#    #    for k in DFTTYP_data:
#    #        outdata = filedata.replace('ccpVDZpp', l).replace('BHHLYP', k)
#    #        outp = inp+k+'-'+j
#    #        out = inp+k+'-'+j+'.inp'
#    #        print (outp)
#    #        fout = open(out,'w')
#    #        fout.write(outdata)
#    #        fout.close()
#    #
#    #filedata = None
#    #d = open('mrsf-soc-Si-LANL2DZ.inp', 'r')
#    #inp = 'so-Si-'
#    #filedata = d.read()
#    #d.close()
#    #for k in DFTTYP_data:
#    #    outdata = filedata.replace('BHHLYP', k)
#    #    outp = inp+k+'-LANL2DZ'
#    #    out = inp+k+'-LANL2DZ.inp'
#    #    print (outp)
#    #    fout = open(out,'w')
#    #    fout.write(outdata)
#    #    fout.close()
#    #
#    #filedata = None
#    #d = open('mrsf-soc-Ge-LANL2DZ.inp', 'r')
#    #inp = 'so-Ge-'
#    #filedata = d.read()
#    #d.close()
#    #for k in DFTTYP_data:
#    #    outdata = filedata.replace('BHHLYP', k)
#    #    outp = inp+k+'-LANL2DZ'
#    #    out = inp+k+'-LANL2DZ.inp'
#    #    print (outp)
#    #    fout = open(out,'w')
#    #    fout.write(outdata)
#    #    fout.close()
#    ##
#    #filedata = None
#    #d = open('mrsf-soc-Sn-LANL2DZ.inp', 'r')
#    #inp = 'so-Sn-'
#    #filedata = d.read()
#    #d.close()
#    #for k in DFTTYP_data:
#    #    outdata = filedata.replace('BHHLYP', k)
#    #    outp = inp+k+'-LANL2DZ'
#    #    out = inp+k+'-LANL2DZ.inp'
#    #    print (outp)
#    #    fout = open(out,'w')
#    #    fout.write(outdata)
#    #    fout.close
#    #
