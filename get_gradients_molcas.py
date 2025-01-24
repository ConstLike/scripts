import re
import sys


def extract_gradients(input_file, output_file):
    """
    Extracts gradients from a Molcas output file and writes them to a new file.
    """
    with open(input_file, 'r', encoding="utf-8") as f:
        lines = f.readlines()

    gradients = []
    in_grad_section = False

    for line in lines:
        if "Molecular gradients" in line:
            in_grad_section = True
            continue
        if in_grad_section:
            if re.match(r'-{10,}', line):
                continue

            # Extract numeric values for gradients
            match = re.match(
                r'^\s*\w+\d+\s+([\dE\+\-\.]+)\s+([\dE\+\-\.]+)\s+([\dE\+\-\.]+)', line
            )
            if match:
                gradients.append(" ".join(match.groups()))
            elif gradients:
                break

    # Write the results to the output file
    with open(output_file, 'w', encoding="utf-8") as f:
        f.write(f"{len(gradients)}\n")
        f.write("\n".join(gradients) + "\n")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 extractor.py <input_file> <output_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    extract_gradients(input_file, output_file)
