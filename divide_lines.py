#!/usr/bin/env python3
""" Read and split """
import argparse
import os


def split_long_line(line, max_length=79):
    """
    Splits a long line into multiple lines at spaces,
    ensuring no single line exceeds max_length.
    If the line starts with '%', each split line will also start with '%'.
    """
    prefix = '%' if line.startswith('%') else ''
    max_length -= len(prefix)  # Adjust max_length if there's a prefix

    if len(line) <= max_length + len(prefix):
        # Return the original line in a list if it's short enough
        return [line]

    # Remove the '%' before splitting into words if it exists
    words = line.lstrip('%').split(' ')
    lines = []  # To hold the resulting lines
    current_line = prefix  # Start with prefix if the original line had it

    for word in words:
        # Check if adding the next word exceeds the max length
        if len(current_line) + len(word) <= max_length:
            current_line += word + " "
        else:
            # Add the current line to the list and start a new one
            lines.append(current_line.rstrip())
            # Start new line with prefix if necessary
            current_line = prefix + word + " "

    lines.append(current_line.rstrip())  # Don't forget to add the last line
    return lines


def split_long_line2(line, max_length=79):
    """
    Splits a long line into multiple lines,
    not exceeding max_length, without breaking words.
    """
    # If the line is within the max_length, return it as is
    if len(line) <= max_length:
        return [line]

    # Split the line into words
    words = line.split()
    lines = []
    current_line = ""

    for word in words:
        # Check if adding the next word exceeds the max_length
        if len(current_line) + len(word) <= max_length:
            current_line += (word + " ")
        else:
            # If the current line is not empty, save it and start a new line
            if current_line:
                # Remove any trailing space
                lines.append(current_line.rstrip())
                current_line = word + " "
            else:
                # If a single word is longer than max_length, split the word
                while len(word) > max_length:
                    lines.append(word[:max_length])
                    word = word[max_length:]
                current_line = word + " "

    # Add the last line if it's not empty
    if current_line:
        lines.append(current_line.rstrip())

    return lines


def process_file(filename):
    """ process file """
    splited = filename.split('.')
    new_filename = splited[0] + '_updated.' + splited[1]

    if not os.path.exists(filename):
        print(f"Error: The file '{filename}' does not exist.")
        return

    with open(filename, 'r', encoding='utf-8') as infile, \
         open(new_filename, 'w', encoding='utf-8') as outfile:
        for line in infile:
            # Only split the line if it's longer than the max_length
            if len(line.rstrip()) > 79:
                # Use rstrip to remove trailing newline
                new_lines = split_long_line(line.rstrip())
                for new_line in new_lines:
                    outfile.write(new_line + '\n')
            else:
                # Write the original line if it's not too long
                outfile.write(line)


def process_file2(filename):
    """ process file """
    splited = filename.split('.')
    new_filename = splited[0] + '_updated.' + splited[1]
    print(new_filename)
#   new_filename = os.path.splitext(filename)[0] + '.log'

    with open(filename, 'r', encoding='utf-8') as infile, \
         open(new_filename, 'w', encoding='utf-8') as outfile:
        for line in infile:
            new_lines = split_long_line(line)
            for new_line in new_lines:
                outfile.write(new_line + '\n')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
            description='Divide long lines in a file.')
    parser.add_argument('filename',
                        type=str,
                        help='The name of the file to process.')

    args = parser.parse_args()

    process_file(args.filename)
