#!/usr/bin/env python

import argparse
import re

elements = {
        'H'  :  1.0,
        'He' :  2.0,
        'Li' :  3.0,
        'Be' :  4.0,
        'B'  :  5.0,
        'C'  :  6.0,
        'N'  :  7.0,
        'O'  :  8.0,
        'F'  :  9.0,
        'Ne' : 10.0,
        'Na' : 11.0,
        'Mg' : 12.0,
        'Al' : 13.0,
        'Si' : 14.0,
        'P'  : 15.0,
        'S'  : 16.0,
        'Cl' : 17.0,
        'Ar' : 18.0,
        }

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("file")
    args = parser.parse_args()

    filename = args.file

    what = 0
    natom = 0

    print(' $DATA')
    with open(filename, "r") as f:

        for linenum, line in enumerate(f):
            # get number of atoms
            if linenum == 0:
                natom = int(line)
            elif linenum == 1:
                print(line.strip())
                print('C1')
            elif linenum == natom + 2:
                break
            else:
                elem, x, y, z = line.split()
                q = elements[elem]
                x = float(x)
                y = float(y)
                z = float(z)
                print(f'{elem:10s}{q:5.1f}{x:20.10f}{y:20.10f}{z:20.10f}')
    print(' $END')
