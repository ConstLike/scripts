#!/usr/bin/env python3

import argparse
import os
import subprocess
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from typing import Any, Dict, List
import threading


class Runner:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._setup_numa_config()
        self._numa_counter = 0
        self._numa_lock = threading.Lock()

        self.config.update({
            'total cpus': self.config.get('total cpus', os.cpu_count()),
            'omp threads': self.config.get('omp threads', 12),
            'max restarts': self.config.get('max restarts', 3),
            'max workers': 2,
            'output to log': self.config.get('output to log', False),
            'folder criterion': self.config.get('folder criterion', ''),
            'input files': [],
            'results': []
        })

        os.environ['OMP_NUM_THREADS'] = str(self.config['omp threads'])
        os.environ['OMP_PLACES'] = 'cores'
        os.environ['OMP_PROC_BIND'] = 'close'

        if isinstance(self.config['input path'], str):
            if os.path.isfile(self.config['input path']):
                if self.config['input path'].endswith('.inp'):
                    self.config['input files'] = [self.config['input path']]
                elif self.config['input path'].endswith('_report.txt'):
                    self._load_failed_from_report()
            else:
                self.config['input files'] = self._find_input_files()

    def _setup_numa_config(self):
        """Setup NUMA configuration."""
        try:
            numa_info = subprocess.check_output(
                ['lscpu', '-p=NODE,CORE,CPU'],
                text=True
            ).strip().split('\n')

            cpu_map = {}
            cores_seen = set()

            for line in numa_info:
                if line.startswith('#'):
                    continue
                node, core, cpu = map(int, line.split(','))
                if core in cores_seen:
                    continue
                cores_seen.add(core)

                if node not in cpu_map:
                    cpu_map[node] = []
                cpu_map[node].append(cpu)

            self.config.update({
                'numa nodes': len(cpu_map),
                'cpu map': cpu_map
            })
        except subprocess.CalledProcessError:
            self.config.update({
                'numa nodes': 1,
                'cpu map': {0: list(range(0, os.cpu_count(), 2))}
            })

    def _get_next_numa_node(self) -> int:
        """Get next NUMA node in round-robin fashion."""
        with self._numa_lock:
            node = self._numa_counter % self.config['numa nodes']
            self._numa_counter += 1
            return node

    def _log(self, message: str):
        """Simple logging function to stdout."""
        print(f"[Runner] {message}")

    def _determine_runner(self, folder_name: str) -> str:
        """Determines the appropriate runner based on folder name."""
        folder_lower = folder_name.lower()

        if folder_lower.startswith('fat-molcas'):
            return 'cp2k.sdbg'
        elif folder_lower.startswith('fat-cp2k') or folder_lower.startswith('cp2k'):
            return 'cp2k.sdbg'
        elif folder_lower.startswith('molcas'):
            return 'pymolcas'
        elif folder_lower.startswith('openqp'):
            return 'openqp'
        else:
            raise ValueError(f"Unable to determine runner for folder: {folder_name}")

    def _find_input_files(self) -> List[str]:
        """Find all input files in directory that match criteria."""
        input_files = []
        input_path = self.config['input path']
        criterion = self.config['folder criterion']

        for root, _, files in os.walk(input_path):
            if criterion and criterion not in root:
                continue
            for file in files:
                if file.endswith('.inp') and 'extern' not in file:
                    input_files.append(os.path.join(root, file))

        return sorted(input_files)

    def _run_single_calculation(self, input_file: str) -> Dict[str, Any]:
        """Run a single calculation with automatic restarts on segfaults."""
        numa_node = self._get_next_numa_node()
        cpu_list = self.config['cpu map'][numa_node]
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        input_dir = os.path.dirname(input_file)

        # For retry from report, use original directory structure
        if self.config['input path'].endswith('_report.txt'):
            output_dir = os.path.dirname(input_file)
        # For single file input
        elif os.path.isfile(self.config['input path']):
            output_dir = self.config['output dir']
        # For directory input
        else:
            output_subdir = os.path.relpath(input_dir, self.config['input path'])
            output_dir = os.path.join(self.config['output dir'], output_subdir)

        os.makedirs(output_dir, exist_ok=True)
        log_file = f"{base_name}.log"

        result = {
            "input file": input_file,
            "log file": os.path.join(output_dir, log_file),
            "status": "UNKNOWN",
            "message": "",
            "execution time": 0,
            "restarts": 0
        }

        if not os.path.exists(input_file):
            result["status"] = "ERROR"
            result["message"] = f"Input file {input_file} not found"
            return result

        runner = self._determine_runner(os.path.basename(input_dir))

        env = os.environ.copy()
        env.update({
            'GOMP_CPU_AFFINITY': f"{cpu_list[0]}-{cpu_list[-1]}"
        })

        for attempt in range(self.config['max restarts'] + 1):
            self._log(f"Running calculation for {os.path.abspath(input_file)} "
                     f"(Attempt {attempt + 1}/{self.config['max restarts'] + 1})")
            start_time = time.perf_counter()

            try:
                command = f"numactl --cpunodebind={numa_node} --membind={numa_node} {runner} {os.path.basename(input_file)}"
                if self.config['output to log']:
                    with open(os.path.join(output_dir, log_file), 'w') as log_f:
                        subprocess.run(
                            command,
                            shell=True,
                            check=True,
                            cwd=output_dir,
                            stdout=log_f,
                            stderr=subprocess.STDOUT,
                            text=True,
                            env=env
                        )
                else:
                    subprocess.run(
                        command,
                        shell=True,
                        check=True,
                        cwd=output_dir,
                        capture_output=True,
                        text=True,
                        env=env
                    )

                with open(os.path.join(output_dir, log_file), 'r') as log_f:
                    log_content = log_f.read()
                    if "Segmentation fault" in log_content:
                        raise subprocess.CalledProcessError(
                            1, command, output="Segmentation fault detected")

                result["status"] = "COMPLETED"
                result["message"] = "Calculation completed successfully"
                break
            except subprocess.CalledProcessError as e:
                if e.returncode == 139:
                    result["status"] = "ERROR"
                    result["message"] = f"Error: {str(e)}\nOutput: {e.output}"
                    result["restarts"] += 1
                    if attempt < self.config['max restarts']:
                        self._log(f"Segmentation fault detected. Restarting "
                                f"(Attempt {attempt + 2}/"
                                f"{self.config['max restarts'] + 1})")
                        continue
                    else:
                        result["message"] += "\nMax restarts reached."
                else:
                    result["status"] = "ERROR"
                    result["message"] = f"Error: {str(e)}\nOutput: {e.output}"
                break

        result["execution time"] = time.perf_counter() - start_time
        return result

    def _format_time(self, seconds: float) -> str:
        """Format time duration in HH:MM:SS.mmm format."""
        hours, rem = divmod(seconds, 3600)
        minutes, seconds = divmod(rem, 60)
        return f"{int(hours):02d}:{int(minutes):02d}:{seconds:06.3f}"

    def _run_calculations(self) -> None:
        """Run all calculations in parallel."""
        self.config['start time'] = time.perf_counter()

        if not self.config['input files']:
            self._log("No input files to process.")
            return

        with ProcessPoolExecutor(max_workers=self.config['max workers']) as executor:
            future_to_file = {
                executor.submit(self._run_single_calculation, f): f
                for f in self.config['input files']
            }
            for future in as_completed(future_to_file):
                self.config['results'].append(future.result())

        self.config['results'].sort(key=lambda x: x['input file'])
        self.config['end time'] = time.perf_counter()


    def _generate_report(self) -> str:
        """Generate and save detailed execution report."""
        is_retry = self.config['input path'].endswith('_report.txt')
        report_name = "retry_report.txt" if is_retry else "runner_report.txt"

        completed = sum(1 for r in self.config['results']
                       if r['status'] == 'COMPLETED')
        errors = sum(1 for r in self.config['results'] if r['status'] == 'ERROR')
        total_time = self.config['end time'] - self.config['start time']

        summary = f"""
Runner Calculations Report
--------------------------
Execution Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Total calculations: {len(self.config['results'])}
Completed: {completed}
Errors: {errors}

Folder criterion: {self.config['folder criterion']}

Input files directory: {self.config['input path']}
Output files directory: {self.config['output dir']}

Total CPUs: {self.config['total cpus']}
OMP threads per calculation: {self.config['omp threads']}
Max parallel calculations: {self.config['max workers']}

Total execution time: {self._format_time(total_time)}
"""

        detailed = "\nDetailed Results:\n"
        for result in self.config['results']:
            detailed += f"\nCalculation: {result['input file']}\n"
            detailed += f"Status: {result['status']}\n"
            detailed += f"Execution time: {self._format_time(result['execution time'])}\n"
            detailed += f"Restarts: {result['restarts']}\n"
            detailed += f"Message: {result['message']}\n"

        report = summary + detailed
        with open("runner_report.txt", 'w') as f:
            f.write(report)

        self._log("Report written to runner_report.txt")
        return summary

    def _load_failed_from_report(self) -> None:
        """Load failed calculations from previous report."""
        try:
            with open(self.config['input path'], 'r', encoding="utf-8") as f:
                lines = f.readlines()

            current_input = None
            current_status = None
            failed_inputs = []

            for line in lines:
                if line.startswith("Calculation: "):
                    current_input = line.split(": ")[1].strip()
                elif line.startswith("Status: "):
                    current_status = line.split(": ")[1].strip()
                    if current_input and current_status == "ERROR":
                        failed_inputs.append(current_input)

            self.config['input files'] = failed_inputs

        except FileNotFoundError:
            self._log("No previous runner report found")

    def run(self) -> str:
        """Main execution method that runs calculations and generates report."""
        self._log(f"Starting Runner calculations")
        self._run_calculations()
        return self._generate_report()


def parse_args():
    parser = argparse.ArgumentParser(description="Run calculations in parallel")
    parser.add_argument("input_path", help="Path to input file/dir or report")
    parser.add_argument("--log", action="store_true", help="Write output to log")
    parser.add_argument("--output_dir", help="Output directory for results")
    parser.add_argument("--total_cpus", type=int, default=16,
                        help="Total number of CPUs")
    parser.add_argument("--omp_threads", type=int, default=16,
                        help="OMP threads per calc")
    parser.add_argument("--max_restarts", type=int, default=1,
                        help="Max restarts for segmentation faults")
    parser.add_argument("--spec", type=str, default='',
                        help="Criterion for folder names")
    return parser.parse_args()


def main():
    args = parse_args()

    if args.output_dir is None:
        if os.path.isfile(args.input_path):
            output_dir = os.path.dirname(args.input_path)
        else:
            output_dir = args.input_path
    else:
        output_dir = args.output_dir

    config = {
        'input path': args.input_path,
        'output dir': output_dir,
        'total cpus': args.total_cpus,
        'omp threads': args.omp_threads,
        'max restarts': args.max_restarts,
        'output to log': args.log,
        'folder criterion': args.spec
    }

    runner = Runner(config)
    report = runner.run()
    print(report)


if __name__ == "__main__":
    main()
