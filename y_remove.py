#!/usr/bin/env python3.6
import fileinput
import numpy as np
import sys
import os

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
    file_dir = os.path.dirname(os.path.realpath('__file__'))
    file_names = os.path.join(file_dir, name_files)
    inputs = open(str(file_names),"r").read()
    files = inputs.splitlines()

for file in files:
    input_file = file
    output_file = 'new_' + file
    string_to_remove = 'WARNING: THIS STATE HAS BROKEN SYMMETRY, CHECK MOS'
    string_to_remove2 = 'THIS IS A NON-ABELIAN POINT GROUP, AS A RESULT,'
    string_to_remove3 = 'SOME STATE SYMMETRY LABELS MAY NOT BE CORRECTLY PRINTED BELOW'
    with open(input_file, 'r', encoding='latin-1') as infile, open(output_file, 'w') as outfile:
         skip_line = False  # Flag to skip the next line
         skip_lines = 0
         for line in infile:
             if skip_lines > 0:
                skip_lines -= 1
                continue  # Skip this line and move to the next iteration
             if skip_line:
                skip_line = False
                continue  # Skip this line and move to the next iteration
             if string_to_remove in line:
                skip_line = True  # Set the flag to skip the next line
                continue  # Skip this line and move to the next iteration
             if string_to_remove2 in line:
                skip_lines = 3  # Set the flag to skip the next line
                continue  # Skip this line and move to the next iteration
             stripped_line = line.strip('\n')
             outfile.write(stripped_line)
             outfile.write('\n')
    os.rename(output_file, input_file)

#   for file in files:
#       input_file = file
#       output_file = 'new_'+file
#       string_to_remove = 'WARNING: THIS STATE HAS BROKEN SYMMETRY, CHECK MOS'
#       with open(input_file, 'r', encoding='latin-1') as infile, open(output_file, 'w') as outfile:
#           for line in infile:
#               if string_to_remove not in line:
#                  stripped_line = line.strip('\n')
#                  outfile.write(stripped_line)
#                  outfile.write('\n')
