#!/usr/bin/env python3

import os
import subprocess
import argparse
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from typing import List, Dict, Any

class MolcasRunner:
    def __init__(self,
                 base_dir: str,
                 output_dir: str = 'molcas_runs_tmp',
                 total_cpus: int = None,
                 omp_threads: int = None):
        self.base_dir = os.path.abspath(base_dir)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.output_dir = os.path.abspath(f"{output_dir}_{timestamp}")
        self.total_cpus = total_cpus if total_cpus is not None else os.cpu_count()
        self.omp_threads = omp_threads if omp_threads is not None else self.total_cpus
        self.max_workers = max(1, self.total_cpus // self.omp_threads)
        self.results: List[Dict[str, Any]] = []
        self.start_time = None
        self.end_time = None

        os.environ['OMP_NUM_THREADS'] = str(self.omp_threads)

    def log(self, message: str):
        """Simple logging function to stdout."""
        print(f"[MolcasRunner] {message}")

    def run_single_calculation(self, calc_dir: str) -> Dict[str, Any]:
        input_file = f"{os.path.basename(calc_dir)}.input"
        log_file = f"{os.path.basename(calc_dir)}.log"
        input_path = os.path.join(calc_dir, input_file)

        result = {
            "calc_dir": calc_dir,
            "input_file": input_file,
            "log_file": log_file,
            "status": "UNKNOWN",
            "message": "",
            "execution_time": 0
        }

        if not os.path.exists(input_path):
            result["status"] = "ERROR"
            result["message"] = f"Input file {input_file} not found"
            return result

        self.log(f"Running calculation in {calc_dir}")
        start_time = time.perf_counter()

        try:
            completed_process = subprocess.run(
                f"pymolcas {input_file} -o {log_file}",
                shell=True,
                check=True,
                cwd=calc_dir,
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

    def run_calculations(self):
        self.start_time = time.perf_counter()

        calc_dirs = [
            os.path.join(self.base_dir, d) for d in os.listdir(self.base_dir)
            if os.path.isdir(os.path.join(self.base_dir, d)) and '_' in d and '-' in d.split('_')[-1]
        ]
        calc_dirs.sort()

        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_dir = {executor.submit(self.run_single_calculation, calc_dir): calc_dir for calc_dir in calc_dirs}
            for future in as_completed(future_to_dir):
                self.results.append(future.result())

        self.results.sort(key=lambda x: x['calc_dir'])
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
Molcas Calculations Report
--------------------------
Execution Date: {execution_date}
Total calculations: {len(self.results)}
Completed: {completed}
Errors: {errors}

Total CPUs: {self.total_cpus}
OMP threads per calculation: {self.omp_threads}
Max parallel calculations: {self.max_workers}

Total execution time: {self.format_time(total_time)}

"""
        detailed_results = "\nDetailed Results:\n"
        for result in self.results:
            detailed_results += f"\nCalculation: {result['calc_dir']}\n"
            detailed_results += f"Status: {result['status']}\n"
            detailed_results += f"Execution time: {self.format_time(result['execution_time'])}\n"
            detailed_results += f"Message: {result['message']}\n"

        return summary

    def run(self) -> str:
        self.log(f"Starting Molcas calculations in: {self.base_dir}")
        self.run_calculations()
        report = self.generate_report()
        self.log("Molcas calculations completed")
        return report

def main():
    parser = argparse.ArgumentParser(description="Run Molcas calculations in parallel")
    parser.add_argument("base_dir", help="Base directory containing the calculation folders")
    parser.add_argument("--total_cpus", type=int, default=None, help="Total number of CPUs to use")
    parser.add_argument("--omp_threads", type=int, default=None, help="Number of OMP threads per calculation")

    args = parser.parse_args()

    runner = MolcasRunner(args.base_dir, total_cpus=args.total_cpus, omp_threads=args.omp_threads)
    report = runner.run()
    print(report)

if __name__ == "__main__":
    main()
