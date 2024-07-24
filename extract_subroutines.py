#!/usr/bin/env python3
import re
import os
import argparse


def extract_subroutines(fortran_file):
    with open(fortran_file, 'r') as file:
        content = file.read()

    file_base_name = os.path.splitext(os.path.basename(fortran_file))[0]

    os.makedirs(file_base_name, exist_ok=True)

    subroutine_pattern = re.compile(r'\bsubroutine\s+(\w+)\s*(\(.*?\))?\s*(.*?)\bend\s+subroutine\b', re.IGNORECASE | re.DOTALL)

    for match in subroutine_pattern.finditer(content):
        name = match.group(1)
        args = match.group(2) if match.group(2) else ""
        body = match.group(3).strip()

        subroutine_content = f"subroutine {name}{args}\n{body}\nend subroutine"

        with open(f'{file_base_name}/{name}.F90', 'w') as sub_file:
            sub_file.write(subroutine_content)


def main():
    parser = argparse.ArgumentParser(description='Extract Fortran subroutines and save them as separate .F90 files.')
    parser.add_argument('filename', type=str, help='The path to the Fortran file to process.')

    args = parser.parse_args()

    extract_subroutines(args.filename)


if __name__ == '__main__':
    main()
