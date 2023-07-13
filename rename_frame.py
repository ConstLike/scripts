#!/usr/bin/env python3.6

# Read the data from a file

def command_line_args():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input',
                        type=str,
                        help='Provide the input.log file')
    return parser.parse_args()

def rename_frame(file_name):
    import re

    with open(file_name, 'r') as file:
      data = file.read()

    # Split the data into frames
    frames = re.split(r'\n\d+\n', data.strip())

    # Rename the "Frame 0" labels with increasing numbers
    for i, frame in enumerate(frames):
       line_count = len(re.findall(r'\n\d+\.\d+\s\d+\.\d+\s\d+\.\d+\n', frame))
       frame = re.sub(r'Frame \d+', f'Frame {line_count}', frame)
       frame_number = str(i)
       frame = re.sub(r'Frame 0', 'Frame ' + frame_number, frame)
       frames[i] = frame
#   frame_counter = 0
#   for i, frame in enumerate(frames):
#       # Count the lines with numbers
#       line_count = len(re.findall(r'\n\d+\.\d+\s\d+\.\d+\s\d+\.\d+\n', frame))
#       # Update the "Frame" label
#       frame = re.sub(r'Frame 0', f'Frame {frame_counter}', frame)
#       frames[i] = frame
#       frame_counter += 1

    # Join the frames back together
    result = '\n'.join(frames)

    # Write the updated data to a new file
    with open(file_name+'_out', 'w') as file:
      file.write(result)

if __name__ == '__main__':

    arg = command_line_args()
    rename_frame(arg.input)

#   %s/\v(frame)/14\r\1/g

