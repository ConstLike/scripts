""" Sum two cube-files """
import numpy as np


def read_cube(filename):
    """ read .CUBE. """
    with open(filename, 'r', encoding="utf-8") as f:

        header = [f.readline().strip() for _ in range(7)]

        nx, dx = int(header[3].split()[0]), float(header[3].split()[1])
        ny, dy = int(header[4].split()[0]), float(header[4].split()[2])
        nz, dz = int(header[5].split()[0]), float(header[5].split()[3])
        origin = [float(x) for x in header[2].split()[1:4]]

        flat_data = []
        for line in f:
            flat_data.extend(map(float, line.split()))

        data = np.array(flat_data).reshape((nx, ny, nz))

    return data, origin, (dx, dy, dz), header


def write_cube(filename, data, origin, spacing, header):
    """ Write.CUBE """
    with open(filename, 'w', encoding="utf-8") as f:
        for line in header[:6]:
            f.write(line + "\n")

        f.write(header[6] + "\n")

        nx, ny, nz = data.shape
        for i in range(nx):
            for j in range(ny):
                for k in range(nz):
                    f.write(f"{data[i,j,k]:12.5E}")
                    if (k+1) % 6 == 0 or k == nz-1:
                        f.write("\n")


INP_FILE1 = 'vemb_ee_1_1.cube'
INP_FILE2 = 'wf_vemb_ne_1_2.cube'

OUT_FILE = 'sum.cube'

data1, origin1, spacing1, header1 = read_cube(INP_FILE1)
data2, origin2, spacing2, header2 = read_cube(INP_FILE2)

if data1.shape != data2.shape or not np.allclose(origin1, origin2) or spacing1 != spacing2:
    raise ValueError("Cube files are not compatible")

sum_data = data1 + data2

sum_header = header1.copy()
sum_header[0] = f"Sum of {INP_FILE1} and {INP_FILE2}"
sum_header[1] = "Generated by Python script"

write_cube(OUT_FILE, sum_data, origin1, spacing1, sum_header)

print(f"created:{OUT_FILE}")
