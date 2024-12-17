#!/usr/bin/env python3
"""
cube_dens_analyze.py
"""
from typing import Dict, List, Tuple
import sys
import numpy as np
from scipy import fft
import matplotlib.pyplot as plt


class DensityAnalyzer:
    """Analyze and align electron density cube files."""

    def __init__(self, config: Dict):
        """Initialize with configuration settings."""
        self.config = config
        self.config.setdefault('cube1', 'kkk_rho0_frag2_2.cube')
        self.config.setdefault('cube2', 'kkk_rho0_frag2_2_ext.cube')
        self.config.setdefault('aligned_cube', 'density_aligned.cube')
        self.config.setdefault('diff_cube', 'density_difference.cube')
        self.config.setdefault('aligned_diff_cube',
                               'density_aligned_difference.cube')

        # Add plot configuration
        self.config['plot'] = {
            'font family': 'Times New Roman',
            'font size': 22,
            'title size': 22,
            'label size': 18,
            'tick size': 22,
            'legend size': 22,
            'figure size': (15, 15),
            'dpi': 300,
            'padding': 3.0,
            'alpha': 0.7,
            'grid style': '--'
        }

    def read_cube(self, filename: str) -> Tuple[np.ndarray,
                                                List[float],
                                                Tuple[float, float, float],
                                                List[str]]:
        """Read cube file and return its components."""
        with open(filename, 'r', encoding="utf-8") as f:
            # Read header
            header = [next(f).strip() for _ in range(2)]

            # Read number of atoms and origin
            atoms_line = next(f).strip()
            n_atoms = int(atoms_line.split()[0])
            origin = [float(x) for x in atoms_line.split()[1:4]]
            header.append(atoms_line)

            # Read grid dimensions and spacing
            nx_line = next(f).strip()
            ny_line = next(f).strip()
            nz_line = next(f).strip()
            header.extend([nx_line, ny_line, nz_line])

            nx = int(nx_line.split()[0])
            ny = int(ny_line.split()[0])
            nz = int(nz_line.split()[0])

            dx = float(nx_line.split()[1])
            dy = float(ny_line.split()[2])
            dz = float(nz_line.split()[3])

            # Read atoms coordinates
            atoms_data = []
            for _ in range(n_atoms):
                line = next(f).strip()
                atoms_data.append(line)
            header.extend(atoms_data)

            # Read volumetric data
            values = []
            for line in f:
                values.extend(float(x) for x in line.split())

            data = np.array(values).reshape((nx, ny, nz))

        return data, origin, (dx, dy, dz), header

    def write_cube(self, filename: str, data: np.ndarray, origin: List[float],
                  spacing: Tuple[float, float, float], header: List[str]) -> None:
        """Write data to cube file format."""
        with open(filename, 'w', encoding="utf-8") as f:
            # Write header
            for line in header:
                f.write(f"{line}\n")

            # Write volumetric data
            nx, ny, nz = data.shape
            for i in range(nx):
                for j in range(ny):
                    for k in range(nz):
                        f.write(f"{data[i,j,k]:12.5E}")
                        if (k + 1) % 6 == 0 or k == nz - 1:
                            f.write("\n")

    def cube_analyze(self, data1: np.ndarray, data2: np.ndarray) -> Dict:
        """Analyze cube data and compute statistics."""
        # Global analysis
        max_val1 = np.max(np.abs(data1))
        max_val2 = np.max(np.abs(data2))
        min_val1 = np.min(data1)
        min_val2 = np.min(data2)

        diff = data1 - data2
        max_diff = np.max(np.abs(diff))
        min_diff = np.min(diff)
        mean_abs_diff = np.mean(np.abs(diff))
        rms_diff = np.sqrt(np.mean(diff**2))

        # Analysis along axes
        axes_stats = []
        for axis in range(3):
            # Average along other axes
            slice1 = np.mean(data1, axis=tuple(i for i in range(3) if i != axis))
            slice2 = np.mean(data2, axis=tuple(i for i in range(3) if i != axis))
            slice_diff = slice1 - slice2

            axes_stats.append({
                'axis': ['X', 'Y', 'Z'][axis],
                'max_val1': np.max(np.abs(slice1)),
                'max_val2': np.max(np.abs(slice2)),
                'min_val1': np.min(slice1),
                'min_val2': np.min(slice2),
                'max_diff': np.max(np.abs(slice_diff)),
                'min_diff': np.min(slice_diff),
                'mean_abs_diff': np.mean(np.abs(slice_diff)),
                'rms_diff': np.sqrt(np.mean(slice_diff**2))
            })

        return {
            'global': {
                'max_val1': max_val1,
                'max_val2': max_val2,
                'min_val1': min_val1,
                'min_val2': min_val2,
                'max_diff': max_diff,
                'min_diff': min_diff,
                'mean_abs_diff': mean_abs_diff,
                'rms_diff': rms_diff
            },
            'axes': axes_stats
        }

    def cube_analyze_fft(self, data1: np.ndarray, data2: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Analyze and align cube data using FFT phase correlation."""
        # Compute FFT of both densities
        fft1 = fft.fftn(data1)
        fft2 = fft.fftn(data2)

        # Compute normalized cross-power spectrum
        cross_power = fft1 * np.conj(fft2)
        normalized_cross_power = cross_power / (np.abs(cross_power)+1.0e-10)

        # Compute inverse FFT of normalized cross-power spectrum
        correlation = np.real(fft.ifftn(normalized_cross_power))

        # Find peak in correlation
        peak_idx = np.unravel_index(np.argmax(correlation), correlation.shape)

        # Calculate fractional shifts
        shifts = []
        for i, sz in zip(peak_idx, data1.shape):
            if i > sz // 2:
                shifts.append(i - sz)
            else:
                shifts.append(i)

        # Apply shift in frequency domain
        nx, ny, nz = data1.shape
        kx = fft.fftfreq(nx)
        ky = fft.fftfreq(ny)
        kz = fft.fftfreq(nz)

        Kx, Ky, Kz = np.meshgrid(kx, ky, kz, indexing='ij')
        phase_shift = -2j * np.pi * (Kx*shifts[0] + Ky*shifts[1] + Kz*shifts[2])

        # Apply shift to second density
        shifted_fft = fft2 * np.exp(phase_shift)
        aligned_density = np.real(fft.ifftn(shifted_fft))

        # Analyze and plot Fourier space representations
        self.plot_fourier_space(fft1, fft2, shifted_fft, 'fourier_space_analysis.png')
        self.analyze_fourier_differences(fft1, fft2, shifted_fft)

        return aligned_density, np.array(shifts)

    def plot_density_profiles(self, data1: np.ndarray, data2: np.ndarray,
                              aligned_data: np.ndarray, output_file: str) -> None:
        """Plot density profiles along axes and diagonal."""
        plt.rcParams.update({
            'font.family': self.config['plot']['font family'],
            'font.size': self.config['plot']['font size'],
            'axes.titlesize': self.config['plot']['title size'],
            'axes.labelsize': self.config['plot']['label size'],
            'xtick.labelsize': self.config['plot']['tick size'],
            'ytick.labelsize': self.config['plot']['tick size'],
            'legend.fontsize': self.config['plot']['legend size'],
            'figure.titlesize': self.config['plot']['title size']
        })

        fig, axes = plt.subplots(2, 2, figsize=self.config['plot']['figure size'])
        axes = axes.flatten()

        for ax in axes:
            ax.ticklabel_format(style='sci', scilimits=(-2,2), axis='y')

        # Plot along X, Y, Z axes
        for i, axis in enumerate(['X', 'Y', 'Z']):
            profile1 = np.mean(data1, axis=tuple(j for j in range(3) if j != i))
            profile2 = np.mean(data2, axis=tuple(j for j in range(3) if j != i))

            axes[i].plot(profile1, 'b-',
                        label=r'$\rho(r)_\mathrm{cp2k}$',
                        alpha=self.config['plot']['alpha'])
            axes[i].plot(profile2, 'r--',
                        label=r'$\rho(r)_\mathrm{molcas}$',
                        alpha=self.config['plot']['alpha'])

            axes[i].set_title(f'Density Profile Along {axis}-axis', pad=15)
            axes[i].set_xlabel('Grid point index')
            axes[i].set_ylabel(r'$\rho(r)$')
            axes[i].grid(True, linestyle=self.config['plot']['grid style'],
                        alpha=self.config['plot']['alpha'])
            axes[i].legend()

        # Plot along diagonal
        diag1 = np.array([data1[i,i,i] for i in range(min(data1.shape))])
        diag2 = np.array([data2[i,i,i] for i in range(min(data2.shape))])

        axes[3].plot(diag1, 'b-',
                    label=r'$\rho(r)_\mathrm{cp2k}$',
                    alpha=self.config['plot']['alpha'])
        axes[3].plot(diag2, 'r--',
                    label=r'$\rho(r)_\mathrm{molcas}$',
                    alpha=self.config['plot']['alpha'])

        axes[3].set_title('Density Profile Along Diagonal', pad=15)
        axes[3].set_xlabel('Grid point index')
        axes[3].set_ylabel(r'Electron density (e/Bohr$^3$)')
        axes[3].grid(True, linestyle=self.config['plot']['grid style'],
                    alpha=self.config['plot']['alpha'])
        axes[3].legend()

        plt.tight_layout(pad=self.config['plot']['padding'])
        plt.savefig(output_file, dpi=self.config['plot']['dpi'], bbox_inches='tight')
        plt.close()

    def process_densities(self):
        """Main processing function."""
        # Read cube files
        data1, origin1, spacing1, header1 = self.read_cube(self.config['cube1'])
        data2, origin2, spacing2, header2 = self.read_cube(self.config['cube2'])

        # Initial analysis
        print("\nInitial analysis:")
        stats = self.cube_analyze(data1, data2)
        self._print_stats(stats)

        # FFT analysis and alignment
        print("\nPerforming FFT analysis and alignment...")
        aligned_data, shifts = self.cube_analyze_fft(data1, data2)
        print(f"Detected shifts (grid points): {shifts}")

        # Analysis after alignment
        print("\nAnalysis after alignment:")
        aligned_stats = self.cube_analyze(data1, aligned_data)
        self._print_stats(aligned_stats)

        # Calculate differences
        diff = data1 - data2
        aligned_diff = data1 - aligned_data

        # Save results
        self.write_cube(self.config['aligned_cube'], aligned_data, origin1, spacing1, header1)
        self.write_cube(self.config['diff_cube'], diff, origin1, spacing1, header1)
        self.write_cube(self.config['aligned_diff_cube'], aligned_diff, origin1, spacing1, header1)

        # Plot profiles
        self.plot_density_profiles(data1, data2, aligned_data, 'density_profiles.png')

    def _print_stats(self, stats: Dict) -> None:
        """Helper function to print statistics."""
        print("\nGlobal statistics:")
        print(f"Max abs value (cube 1): {stats['global']['max_val1']:.6e}")
        print(f"Max abs value (cube 2): {stats['global']['max_val2']:.6e}")
        print(f"Min value (cube 1): {stats['global']['min_val1']:.6e}")
        print(f"Min value (cube 2): {stats['global']['min_val2']:.6e}")
        print(f"Max abs difference: {stats['global']['max_diff']:.6e}")
        print(f"Min difference: {stats['global']['min_diff']:.6e}")
        print(f"Mean abs difference: {stats['global']['mean_abs_diff']:.6e}")
        print(f"RMS difference: {stats['global']['rms_diff']:.6e}")

        print("\nStatistics along axes:")
        for axis_stats in stats['axes']:
            print(f"\n{axis_stats['axis']}-axis:")
            print(f"Max abs value (cube 1): {axis_stats['max_val1']:.6e}")
            print(f"Max abs value (cube 2): {axis_stats['max_val2']:.6e}")
            print(f"Min value (cube 1): {axis_stats['min_val1']:.6e}")
            print(f"Min value (cube 2): {axis_stats['min_val2']:.6e}")
            print(f"Max abs difference: {axis_stats['max_diff']:.6e}")
            print(f"Min difference: {axis_stats['min_diff']:.6e}")
            print(f"Mean abs difference: {axis_stats['mean_abs_diff']:.6e}")
            print(f"RMS difference: {axis_stats['rms_diff']:.6e}")

    def plot_fourier_space(self, fft1: np.ndarray, fft2: np.ndarray,
                              fft_aligned: np.ndarray, output_file: str) -> None:
        """Plot density distributions in Fourier space."""
        plt.rcParams.update({
            'font.family': self.config['plot']['font family'],
            'font.size': self.config['plot']['font size'],
            'axes.titlesize': self.config['plot']['title size'],
            'axes.labelsize': self.config['plot']['label size'],
            'xtick.labelsize': self.config['plot']['tick size'],
            'ytick.labelsize': self.config['plot']['tick size'],
            'legend.fontsize': self.config['plot']['legend size'],
            'figure.titlesize': self.config['plot']['title size']
        })

        # Calculate amplitudes
        amp1 = np.log10(np.abs(fft1) + 1e-10)
        amp2 = np.log10(np.abs(fft2) + 1e-10)
        amp_aligned = np.log10(np.abs(fft_aligned) + 1e-10)

        # Calculate phases
        phase1 = np.angle(fft1)
        phase2 = np.angle(fft2)
        phase_aligned = np.angle(fft_aligned)

        fig, axes = plt.subplots(2, 3, figsize=(18, 12))

        # Plot amplitudes
        for i, (amp, title) in enumerate([
            (amp1, 'cp2k Density'),
            (amp2, 'molcas Density'),
            (amp_aligned, 'Aligned Density')
        ]):
            # Get central slices
            slice_xy = amp[amp.shape[0]//2, :, :]

            # Plot amplitude in XY plane
            im = axes[0, i].imshow(slice_xy, cmap='viridis')
            axes[0, i].set_title(f'{title}\nAmplitude (XY plane)')
            plt.colorbar(im, ax=axes[0, i])

            # Plot phase in XY plane
            phase_slice = locals()[f'phase{i+1 if i<2 else "_aligned"}'][amp.shape[0]//2, :, :]
            im = axes[1, i].imshow(phase_slice, cmap='twilight', vmin=-np.pi, vmax=np.pi)
            axes[1, i].set_title(f'{title}\nPhase (XY plane)')
            plt.colorbar(im, ax=axes[1, i])

        plt.tight_layout(pad=self.config['plot']['padding'])
        plt.savefig(output_file, dpi=self.config['plot']['dpi'], bbox_inches='tight')
        plt.close()

        # Create additional plots for frequency profiles
        fig, axes = plt.subplots(2, 2, figsize=self.config['plot']['figure size'])
        axes = axes.flatten()

        # Enable scientific notation
        for ax in axes:
            ax.ticklabel_format(style='sci', scilimits=(-4,4), axis='y')

        def get_profiles(data, axis):
            if axis == 0:  # X-axis
                return np.mean(np.mean(data, axis=2), axis=1)
            elif axis == 1:  # Y-axis
                return np.mean(np.mean(data, axis=2), axis=0)
            else:  # Z-axis
                return np.mean(np.mean(data, axis=1), axis=0)

        # Plot frequency profiles along main axes
        for i, axis in enumerate(['X', 'Y', 'Z']):
            profile1 = get_profiles(fft1, i)
            profile2 = get_profiles(fft2, i)
#           profile_aligned = get_profiles(fft_aligned, i)

            profile1_amp = np.log10(np.abs(profile1) + 1e-10)
            profile2_amp = np.log10(np.abs(profile2) + 1e-10)
#           profile_aligned_amp = np.log10(np.abs(profile_aligned) + 1e-10)

            axes[i].plot(profile1_amp, 'b-',
                        label=r'$\rho(G)_\mathrm{cp2k}$',
                        alpha=self.config['plot']['alpha'])
            axes[i].plot(profile2_amp, 'r--',
                        label=r'$\rho(G)_\mathrm{molcas}$',
                        alpha=self.config['plot']['alpha'])
#           axes[i].plot(profile_aligned_amp, 'g:',
#                       label=r'$\rho(G)_\mathrm{molcas}$ aligned',
#                       alpha=self.config['plot']['alpha'])
            axes[i].set_title(f'Frequency Profile Along {axis}-axis')
            axes[i].set_xlabel('Frequency index')
            axes[i].set_ylabel('Log amplitude')
            axes[i].grid(True, linestyle=self.config['plot']['grid style'],
                        alpha=self.config['plot']['alpha'])
            axes[i].legend()

        # Plot radially averaged frequency profile
        def radial_profile(data):
            center = np.array(data.shape) // 2
            y, x, z = np.ogrid[-center[0]:data.shape[0]-center[0],
                              -center[1]:data.shape[1]-center[1],
                              -center[2]:data.shape[2]-center[2]]
            r = np.sqrt(x*x + y*y + z*z)
            r = r.astype(int)

            tbin = np.bincount(r.ravel(), np.abs(data.ravel()))
            nr = np.bincount(r.ravel())
            radialprofile = tbin / nr
            return np.log10(radialprofile + 1e-10)

        r_profile1 = radial_profile(fft1)
        r_profile2 = radial_profile(fft2)
#       r_profile_aligned = radial_profile(fft_aligned)

        axes[3].plot(r_profile1, 'b-', label='cp2k',
                    alpha=self.config['plot']['alpha'])
        axes[3].plot(r_profile2, 'r--', label='molcas',
                    alpha=self.config['plot']['alpha'])
#       axes[3].plot(r_profile_aligned, 'g:', label='Aligned',
#                   alpha=self.config['plot']['alpha'])
        axes[3].set_title('Radially Averaged Frequency Profile')
        axes[3].set_xlabel('Radial frequency')
        axes[3].set_ylabel('Log amplitude')
        axes[3].grid(True, linestyle=self.config['plot']['grid style'],
                    alpha=self.config['plot']['alpha'])
        axes[3].legend()

        plt.tight_layout(pad=self.config['plot']['padding'])
        plt.savefig(output_file.replace('.png', '_profiles.png'),
                    dpi=self.config['plot']['dpi'],
                    bbox_inches='tight')
        plt.close()

    def analyze_fourier_differences(self, fft1: np.ndarray, fft2: np.ndarray, fft_aligned: np.ndarray) -> None:
        """
        Analyze differences between densities in Fourier space.

        Args:
            fft1: FFT of first density
            fft2: FFT of second density
            fft_aligned: FFT of aligned density
        """
        # Calculate amplitude differences
        amp_diff_original = np.abs(np.abs(fft1) - np.abs(fft2))
        amp_diff_aligned = np.abs(np.abs(fft1) - np.abs(fft_aligned))

        # Calculate phase differences
        phase_diff_original = np.abs(np.angle(fft1) - np.angle(fft2))
        phase_diff_aligned = np.abs(np.angle(fft1) - np.angle(fft_aligned))

        print("\nFourier Space Analysis:")
        print("\nAmplitude differences:")
        print(f"Original  - Max: {np.max(amp_diff_original):.6e}, "
              f"Mean: {np.mean(amp_diff_original):.6e}, "
              f"RMS: {np.sqrt(np.mean(amp_diff_original**2)):.6e}")
        print(f"Aligned   - Max: {np.max(amp_diff_aligned):.6e}, "
              f"Mean: {np.mean(amp_diff_aligned):.6e}, "
              f"RMS: {np.sqrt(np.mean(amp_diff_aligned**2)):.6e}")

        print("\nPhase differences (radians):")
        print(f"Original  - Max: {np.max(phase_diff_original):.6f}, "
              f"Mean: {np.mean(phase_diff_original):.6f}, "
              f"RMS: {np.sqrt(np.mean(phase_diff_original**2)):.6f}")
        print(f"Aligned   - Max: {np.max(phase_diff_aligned):.6f}, "
              f"Mean: {np.mean(phase_diff_aligned):.6f}, "
              f"RMS: {np.sqrt(np.mean(phase_diff_aligned**2)):.6f}")


def main():
    """Main execution function."""
#       'cube1': 'kkk_rho0_tot.cube',
    config = {
        'cube1': sys.argv[1],
        'cube2': sys.argv[2],
        'aligned_cube': 'density_aligned.cube',
        'diff_cube': 'density_difference.cube',
        'aligned_diff_cube': 'density_aligned_difference.cube'
    }

    analyzer = DensityAnalyzer(config)
    analyzer.process_densities()


if __name__ == "__main__":
    main()
