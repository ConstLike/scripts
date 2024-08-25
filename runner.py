#!/usr/bin/env python3

import os
import subprocess
import argparse
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from typing import List, Dict, Any

class Runner:
    def __init__(self,
                 runner: str,
                 input_path: str,
                 output_dir: str,
                 total_cpus: int = None,
                 omp_threads: int = None,
                 use_output_flag: bool = False):
        self.input_path = os.path.abspath(input_path)
        self.output_dir = os.path.abspath(output_dir)
        self.total_cpus = total_cpus if total_cpus is not None else os.cpu_count()
        self.omp_threads = omp_threads if omp_threads is not None else self.total_cpus
        self.max_workers = max(1, self.total_cpus // self.omp_threads)
        self.results: List[Dict[str, Any]] = []
        self.start_time = None
        self.end_time = None
        self.runner = runner
        self.use_output_flag = use_output_flag
        self.is_single_file = os.path.isfile(self.input_path)

        os.environ['OMP_NUM_THREADS'] = str(self.omp_threads)

    def log(self, message: str):
        """Simple logging function to stdout."""
        print(f"[Runner] {message}")

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
            "input_file": input_file,
            "log_file": os.path.join(output_dir, log_file),
            "status": "UNKNOWN",
            "message": "",
            "execution_time": 0
        }

        if not os.path.exists(input_file):
            result["status"] = "ERROR"
            result["message"] = f"Input file {input_file} not found"
            return result

        self.log(f"Running calculation for {input_file}")
        start_time = time.perf_counter()

        try:
            command = f"{self.runner} {os.path.basename(input_file)}"
            if self.use_output_flag:
                command = f"{self.runner} {os.path.basename(input_file)} -o {log_file}"
            completed_process = subprocess.run(
                command,
                shell=True,
                check=True,
                cwd=output_dir,
                capture_output=True,
                text=True
            )
            result["status"] = "COMPLETED"
            result["message"] = "Calculation completed successfully"
        except subprocess.CalledProcessError as e:
            result["status"] = "ERROR"
            result["message"] = f"Error: {str(e)}\nOutput: {e.output}"

        result["execution_time"] = time.perf_counter() - start_time
        return result

    def find_input_files(self, directory: str) -> List[str]:
        input_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.inp'):
                    input_files.append(os.path.join(root, file))
        return input_files

    def run_calculations(self):
        self.start_time = time.perf_counter()

        if os.path.isfile(self.input_path):
            if not self.input_path.endswith('.inp'):
                self.log(f"Error: The specified file {self.input_path} is not an .inp file.")
                return
            input_files = [self.input_path]
        else:
            input_files = self.find_input_files(self.input_path)

        input_files.sort()

        if not input_files:
            self.log("No .inp files found in the specified directory or its subdirectories.")
            return

        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_file = {executor.submit(self.run_single_calculation, input_file): input_file for input_file in input_files}
            for future in as_completed(future_to_file):
                self.results.append(future.result())

        self.results.sort(key=lambda x: x['input_file'])
        self.end_time = time.perf_counter()

    def format_time(self, seconds: float) -> str:
        hours, rem = divmod(seconds, 3600)
        minutes, seconds = divmod(rem, 60)
        return f"{int(hours):02d}:{int(minutes):02d}:{seconds:06.3f}"

    def generate_report(self) -> str:
        completed = sum(1 for result in self.results if result['status'] == 'COMPLETED')
        errors = sum(1 for result in self.results if result['status'] == 'ERROR')

        total_time = self.end_time - self.start_time
        execution_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        summary = f"""
Runner Calculations Report
--------------------------
Execution Date: {execution_date}
Total calculations: {len(self.results)}
Completed: {completed}
Errors: {errors}

Input files directory: {self.input_path}
Output files directory: {self.output_dir}

Total CPUs: {self.total_cpus}
OMP threads per calculation: {self.omp_threads}
Max parallel calculations: {self.max_workers}

Total execution time: {self.format_time(total_time)}

"""
        detailed_results = "\nDetailed Results:\n"
        for result in self.results:
            detailed_results += f"\nCalculation: {result['input_file']}\n"
            detailed_results += f"Status: {result['status']}\n"
            detailed_results += f"Execution time: {self.format_time(result['execution_time'])}\n"
            detailed_results += f"Message: {result['message']}\n"

        return summary

    def run(self) -> str:
        self.log(f"Starting Runner calculations in: {self.input_path}")
        self.run_calculations()
        report = self.generate_report()
        self.log("Runner calculations completed")
        return report

def main():
    parser = argparse.ArgumentParser(description="Run calculations in parallel")
    parser.add_argument("runner", help="Runner program")
    parser.add_argument("input_path", help="Path to input file or directory containing input files")
    parser.add_argument("--output_dir", help="Output directory containing the calculation results")
    parser.add_argument("--total_cpus", type=int, default=None, help="Total number of CPUs to use")
    parser.add_argument("--omp_threads", type=int, default=None, help="Number of OMP threads per calculation")

    args = parser.parse_args()

    if args.output_dir is None:
        if os.path.isfile(args.input_path):
            output_dir = os.path.dirname(args.input_path)
        else:
            output_dir = args.input_path
    else:
        output_dir = args.output_dir

    runner = Runner(
            runner=args.runner,
            input_path=args.input_path,
            output_dir=output_dir,
            total_cpus=args.total_cpus,
            omp_threads=args.omp_threads,
            use_output_flag=False
    )
    report = runner.run()
    print(report)

if __name__ == "__main__":
    main()
