#!/bin/bash

# Configuration defaults
THREADS_PER_JOB=12  # OMP threads per job
MAX_JOBS=4          # Max parallel jobs
REAL_CORES=0        # Use only real cores (no HT)
MAX_RESTARTS=3      # Max restart attempts
FOLDER_CRITERION="" # Folder name filter

# Help message
usage() {
  echo "Usage: $0 -i INPUT [-o OUTPUT] [-j JOBS] [-t THREADS] [-r] [-c CRITERION]"
  echo "  -i INPUT       Input path (file/directory/report)"
  echo "  -o OUTPUT      Output directory (optional)"
  echo "  -j JOBS        Number of parallel jobs (default: 4)"
  echo "  -t THREADS     Threads per job (default: 12)"
  echo "  -r             Use only real cores (no HT)"
  echo "  -c CRITERION   Folder name filter"
  exit 1
}

# Parse arguments
while getopts "i:o:j:t:rc:" opt; do
  case $opt in
  i) INPUT_PATH="$OPTARG" ;;
  o) OUTPUT_DIR="$OPTARG" ;;
  j) MAX_JOBS="$OPTARG" ;;
  t) THREADS_PER_JOB="$OPTARG" ;;
  r) REAL_CORES=1 ;;
  c) FOLDER_CRITERION="$OPTARG" ;;
  ?) usage ;;
  esac
done

if [ -z "$INPUT_PATH" ]; then
  usage
fi

# Set default output directory
if [ -z "$OUTPUT_DIR" ]; then
  if [ -f "$INPUT_PATH" ]; then
    OUTPUT_DIR=$(dirname "$INPUT_PATH")
  else
    OUTPUT_DIR="$INPUT_PATH"
  fi
fi

# Setup environment
export OMP_NUM_THREADS=$THREADS_PER_JOB
export MKL_NUM_THREADS=$THREADS_PER_JOB

# Function to determine runner
get_runner() {
  local folder_name="$1"
  if [[ $folder_name == *"fat-molcas"* ]]; then
    echo "cp2k.sdbg"
  elif [[ $folder_name == *"cp2k"* ]]; then
    echo "cp2k.sdbg"
  else
    echo "pymolcas"
  fi
}

# Function to run single calculation
run_calculation() {
  local input_file="$1"
  local base_name=$(basename "$input_file" .inp)
  local dir_name=$(dirname "$input_file")
  local rel_path
  local out_dir
  local runner
  local numa_node
  local cpu_list

  # Set output directory
  if [[ "$INPUT_PATH" == *"_report.txt" ]]; then
    out_dir="$dir_name"
  elif [ -f "$INPUT_PATH" ]; then
    out_dir="$OUTPUT_DIR"
  else
    rel_path=${dir_name#$INPUT_PATH/}
    out_dir="$OUTPUT_DIR/$rel_path"
  fi

  mkdir -p "$out_dir"
  cd "$out_dir"

  runner=$(get_runner "$dir_name")

  # Get NUMA node and CPU list based on job number
  local job_num=$((PARALLEL_SEQ - 1))
  if [ $REAL_CORES -eq 1 ]; then
    numa_node=$((job_num % 2))
    start_cpu=$((numa_node * 12 + (job_num / 2) * 6))
    cpu_list=""
    for ((i = 0; i < 6; i++)); do
      if [ -n "$cpu_list" ]; then
        cpu_list="$cpu_list,"
      fi
      cpu_list="$cpu_list$((start_cpu + i))"
    done
  else
    numa_node=$((job_num % 2))
    cpu_list="$numa_node"
  fi

  # Run with retries
  local attempt=1
  while [ $attempt -le $MAX_RESTARTS ]; do
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Running $input_file (Attempt $attempt)"

    if numactl --cpunodebind=$numa_node --membind=$numa_node \
      $runner "$base_name.inp" >"$base_name.log" 2>&1; then
      echo "SUCCESS" >"${base_name}_status.txt"
      return 0
    fi

    if grep -q "Segmentation fault" "$base_name.log"; then
      ((attempt++))
      if [ $attempt -le $MAX_RESTARTS ]; then
        echo "Segmentation fault detected, retrying..."
        continue
      fi
    fi

    echo "ERROR" >"${base_name}_status.txt"
    return 1
  done
}

export -f run_calculation
export -f get_runner

# Find and run calculations
if [ -f "$INPUT_PATH" ]; then
  if [[ "$INPUT_PATH" == *"_report.txt" ]]; then
    # Process failed calculations from report
    grep -B 1 "Status: ERROR" "$INPUT_PATH" |
      grep "Calculation:" |
      cut -d' ' -f2- |
      parallel -j $MAX_JOBS --line-buffer run_calculation
  else
    # Single input file
    run_calculation "$INPUT_PATH"
  fi
else
  # Process directory
  if [ -n "$FOLDER_CRITERION" ]; then
    find "$INPUT_PATH" -type f -name "*.inp" ! -name "*extern*" \
      -path "*$FOLDER_CRITERION*" |
      parallel -j $MAX_JOBS --line-buffer run_calculation
  else
    find "$INPUT_PATH" -type f -name "*.inp" ! -name "*extern*" |
      parallel -j $MAX_JOBS --line-buffer run_calculation
  fi
fi

# Generate report
{
  echo "Runner Calculations Report"
  echo "--------------------------"
  echo "Execution Date: $(date '+%Y-%m-%d %H:%M:%S')"
  echo "Input Path: $INPUT_PATH"
  echo "Output Directory: $OUTPUT_DIR"
  echo "Parallel Jobs: $MAX_JOBS"
  echo "Threads per Job: $THREADS_PER_JOB"
  echo "Real Cores Only: $REAL_CORES"
  echo "Folder Criterion: $FOLDER_CRITERION"
  echo
  echo "Detailed Results:"
  echo

  find "$OUTPUT_DIR" -name "*_status.txt" | while read status_file; do
    input_file=${status_file%_status.txt}.inp
    status=$(cat "$status_file")
    echo "Calculation: $input_file"
    echo "Status: $status"
    echo
  done
} >"runner_report.txt"

echo "Report generated: runner_report.txt"
