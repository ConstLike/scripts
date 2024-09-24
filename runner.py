#!/usr/bin/env python3

import argparse
import os
import subprocess
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from typing import Any, Dict, List


class Runner:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.input_path = os.path.abspath(config['input path'])
        self.output_dir = os.path.abspath(config['output dir'])
        self.total_cpus = config.get('total cpus', os.cpu_count())
        self.omp_threads = config.get('omp threads', self.total_cpus)
        self.max_workers = max(1, self.total_cpus // self.omp_threads)
        self.results: List[Dict[str, Any]] = []
        self.start_time = None
        self.end_time = None

        self.output_to_log = config.get('output to log', False)
        self.is_single_file = os.path.isfile(self.input_path)
        self.max_restarts = config.get('max restarts', 3)
        self.folder_criterion = config.get('folder criterion', '')

        os.environ['OMP_NUM_THREADS'] = str(self.omp_threads)

    def log(self, message: str):
        """Simple logging function to stdout."""
        print(f"[Runner] {message}")

    def determine_runner(self, folder_name: str) -> str:
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

    def run_single_calculation(self, input_file: str) -> Dict[str, Any]:
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        log_file = f"{base_name}.log"

        if self.is_single_file:
            output_dir = self.output_dir
        else:
            input_dir = os.path.dirname(input_file)
            output_subdir = os.path.relpath(input_dir, self.input_path)
            output_dir = os.path.join(self.output_dir, output_subdir)

        os.makedirs(output_dir, exist_ok=True)

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

        runner = self.determine_runner(os.path.basename(os.path.dirname(input_file)))

        for attempt in range(self.max_restarts + 1):
            self.log(f"Running calculation for {input_file} "
                     f"(Attempt {attempt + 1}/{self.max_restarts + 1})")
            start_time = time.perf_counter()

            try:
                command = f"{runner} {os.path.basename(input_file)}"
                if self.output_to_log:
                    with open(os.path.join(output_dir, log_file), 'w') as log_f:
                        subprocess.run(
                            command,
                            shell=True,
                            check=True,
                            cwd=output_dir,
                            stdout=log_f,
                            stderr=subprocess.STDOUT,
                            text=True
                        )
                else:
                    subprocess.run(
                        command,
                        shell=True,
                        check=True,
                        cwd=output_dir,
                        capture_output=True,
                        text=True
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
                    if attempt < self.max_restarts:
                        self.log(f"Segmentation fault detected. Restarting "
                                 f"(Attempt {attempt + 2}/{self.max_restarts + 1})")
                        continue
                    else:
                        result["message"] += "\nMax restarts reached."
                else:
                    result["status"] = "ERROR"
                    result["message"] = f"Error: {str(e)}\nOutput: {e.output}"
                break

        result["execution time"] = time.perf_counter() - start_time
        return result

    def find_input_files(self, directory: str) -> List[str]:
        input_files = []
        for root, dirs, files in os.walk(directory):
            if self.folder_criterion and self.folder_criterion not in root:
                continue
            for file in files:
                if file.endswith('.inp'):
                    input_files.append(os.path.join(root, file))
        return input_files

    def run_calculations(self):
        self.start_time = time.perf_counter()

        if os.path.isfile(self.input_path):
            if not self.input_path.endswith('.inp'):
                self.log(f"Error: The file {self.input_path} is not .inp")
                return
            input_files = [self.input_path]
        else:
            input_files = self.find_input_files(self.input_path)

        filtered_files = [f for f in input_files if "extern" not in f]
        filtered_files.sort()

        if not filtered_files:
            self.log("No .inp files found in the specified directory.")
            return

        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_file = {executor.submit(self.run_single_calculation, f): f
                              for f in filtered_files}
            for future in as_completed(future_to_file):
                self.results.append(future.result())

        self.results.sort(key=lambda x: x['input file'])
        self.end_time = time.perf_counter()

    def format_time(self, seconds: float) -> str:
        hours, rem = divmod(seconds, 3600)
        minutes, seconds = divmod(rem, 60)
        return f"{int(hours):02d}:{int(minutes):02d}:{seconds:06.3f}"

    def generate_report(self) -> str:
        completed = sum(1 for r in self.results if r['status'] == 'COMPLETED')
        errors = sum(1 for r in self.results if r['status'] == 'ERROR')

        total_time = self.end_time - self.start_time
        execution_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        summary = f"""
Runner Calculations Report
--------------------------
Execution Date: {execution_date}
Total calculations: {len(self.results)}
Completed: {completed}
Errors: {errors}

Folder criterion: {self.folder_criterion}

Input files directory: {self.input_path}
Output files directory: {self.output_dir}

Total CPUs: {self.total_cpus}
OMP threads per calculation: {self.omp_threads}
Max parallel calculations: {self.max_workers}

Total execution time: {self.format_time(total_time)}

"""
        detailed_results = "\nDetailed Results:\n"
        for result in self.results:
            detailed_results += f"\nCalculation: {result['input file']}\n"
            detailed_results += f"Status: {result['status']}\n"
            detailed_results += f"Execution time: "
            detailed_results += f"{self.format_time(result['execution time'])}\n"
            detailed_results += f"Restarts: {result['restarts']}\n"
            detailed_results += f"Message: {result['message']}\n"

        full_report = summary + detailed_results

        report_filename = "runner_report.txt"
        with open(report_filename, 'w') as report_file:
            report_file.write(full_report)

        self.log(f"Report written to {report_filename}")

        return summary

    def run(self) -> str:
        self.log(f"Starting Runner calculations in: {self.input_path}")
        self.run_calculations()
        report = self.generate_report()
        self.log("Runner calculations completed")
        return report


def parse_args():
    parser = argparse.ArgumentParser(description="Run calculations in parallel")
    parser.add_argument("input_path", help="Path to input file or directory")
    parser.add_argument("--log", action="store_true", help="Write output to log")
    parser.add_argument("--output_dir", help="Output directory for results")
    parser.add_argument("--total_cpus", type=int, default=16, help="Total number of CPUs")
    parser.add_argument("--omp_threads", type=int, default=16, help="OMP threads per calc")
    parser.add_argument("--max_restarts", type=int, default=5,
                        help="Max restarts for segmentation faults")
    parser.add_argument("--spec", type=str, default='', help="Criterion for folder names")
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
