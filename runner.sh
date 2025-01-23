#!/bin/bash

# Get system info
TOTAL_CPUS=$(lscpu | grep "^CPU(s):" | awk '{print $2}')
CORES_PER_SOCKET=$(lscpu | grep "^Core(s) per socket:" | awk '{print $4}')
SOCKETS=$(lscpu | grep "^Socket(s):" | awk '{print $2}')
THREADS_PER_CORE=$(lscpu | grep "^Thread(s) per core:" | awk '{print $4}')
NUMA_NODES=$(lscpu | grep "^NUMA node(s):" | awk '{print $3}')

# Configuration defaults
MAX_RESTARTS=3
FOLDER_CRITERION=""
REAL_CORES=0

# Help message
usage() {
    echo "Usage: $0 -i INPUT [-o OUTPUT] [-r] [-c CRITERION]"
    echo "  -i INPUT       Input path (file/directory/report)"
    echo "  -o OUTPUT      Output directory (optional)"
    echo "  -r            Use only real cores (no HT)"
    echo "  -c CRITERION   Folder name filter"
    echo
    echo "System configuration:"
    echo "  Total CPUs: $TOTAL_CPUS"
    echo "  Sockets: $SOCKETS"
    echo "  Cores per socket: $CORES_PER_SOCKET"
    echo "  Threads per core: $THREADS_PER_CORE"
    echo "  NUMA nodes: $NUMA_NODES"
    exit 1
}

# Parse arguments
while getopts "i:o:rc:" opt; do
    case $opt in
        i) INPUT_PATH="$OPTARG" ;;
        o) OUTPUT_DIR="$OPTARG" ;;
        r) REAL_CORES=1 ;;
        c) FOLDER_CRITERION="$OPTARG" ;;
        ?) usage ;;
    esac
done

if [ -z "$INPUT_PATH" ]; then
    usage
fi

# Calculate optimal configuration
if [ $REAL_CORES -eq 1 ]; then
    # Use only physical cores
    THREADS_PER_JOB=$CORES_PER_SOCKET
    MAX_JOBS=$SOCKETS
else
    # Use all threads
    THREADS_PER_JOB=$((CORES_PER_SOCKET * THREADS_PER_CORE))
    MAX_JOBS=$SOCKETS
fi

echo "Running with configuration:"
echo "  Parallel jobs: $MAX_JOBS"
echo "  Threads per job: $THREADS_PER_JOB"
echo "  Using HT: $([[ $REAL_CORES -eq 0 ]] && echo 'yes' || echo 'no')"

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
export OMP_PLACES=cores
export OMP_PROC_BIND=close

# Function to determine runner type
get_runner() {
    local folder_name="$1"
    case "${folder_name,,}" in
        *"fat-molcas"*) echo "cp2k.sdbg" ;;
        *"cp2k"*) echo "cp2k.sdbg" ;;
        *"molcas"*) echo "pymolcas" ;;
        *) echo "unknown" ;;
    esac
}

# Function to run single calculation
run_calculation() {
    local input_file="$1"
    local base_name=$(basename "$input_file" .inp)
    local dir_name=$(dirname "$input_file")
    local start_time=$(date +%s)

    # Validate input file
    if [ ! -f "$input_file" ]; then
        echo "Error: Input file not found: $input_file"
        return 1
    }

    # Set output directory
    local out_dir
    if [[ "$INPUT_PATH" == *"_report.txt" ]]; then
        out_dir="$dir_name"
    elif [ -f "$INPUT_PATH" ]; then
        out_dir="$OUTPUT_DIR"
    else
        local rel_path=${dir_name#$INPUT_PATH/}
        out_dir="$OUTPUT_DIR/$rel_path"
    fi

    mkdir -p "$out_dir" || {
        echo "Error: Failed to create output directory: $out_dir"
        return 1
    }
    cd "$out_dir" || {
        echo "Error: Failed to change to output directory: $out_dir"
        return 1
    }

    # Get runner
    local runner=$(get_runner "$dir_name")
    if [ "$runner" = "unknown" ]; then
        echo "Error: Unknown calculation type for $input_file"
        return 1
    }

    # NUMA binding
    local job_num=$((PARALLEL_SEQ - 1))
    local numa_node=$((job_num % NUMA_NODES))
    local cpu_range
    
    if [ $REAL_CORES -eq 1 ]; then
        local start_cpu=$((numa_node * CORES_PER_SOCKET))
        local end_cpu=$((start_cpu + THREADS_PER_JOB - 1))
        cpu_range="$start_cpu-$end_cpu"
    else
        cpu_range="$((numa_node * THREADS_PER_JOB))-$(((numa_node + 1) * THREADS_PER_JOB - 1))"
    fi

    # Run with retries
    local status_file="${base_name}_status.txt"
    local log_file="${base_name}.log"
    local attempt=1
    
    while [ $attempt -le $MAX_RESTARTS ]; do
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Running $input_file (Attempt $attempt)"
        echo "NUMA node: $numa_node, CPU range: $cpu_range"
        
        if numactl --cpunodebind=$numa_node --membind=$numa_node \
           $runner "$base_name.inp" > "$log_file" 2>&1; then
            local end_time=$(date +%s)
            echo "SUCCESS" > "$status_file"
            echo "TIME: $((end_time - start_time))" >> "$status_file"
            return 0
        fi

        if grep -q "Segmentation fault" "$log_file"; then
            ((attempt++))
            if [ $attempt -le $MAX_RESTARTS ]; then
                echo "Segmentation fault detected, retrying..."
                sleep 2
                continue
            fi
        fi
        
        local end_time=$(date +%s)
        echo "ERROR" > "$status_file"
        echo "TIME: $((end_time - start_time))" >> "$status_file"
        return 1
    done
}

export -f run_calculation
export -f get_runner

# Create temporary directory for logs
TEMP_DIR=$(mktemp -d)
trap 'rm -rf "$TEMP_DIR"' EXIT

# Find and run calculations
echo "Starting calculations at $(date '+%Y-%m-%d %H:%M:%S')"

if [ -f "$INPUT_PATH" ]; then
    if [[ "$INPUT_PATH" == *"_report.txt" ]]; then
        # Process failed calculations from report
        grep -B 1 "Status: ERROR" "$INPUT_PATH" | \
        grep "Calculation:" | \
        cut -d' ' -f2- | \
        parallel --joblog "$TEMP_DIR/parallel.log" \
                 -j $MAX_JOBS \
                 --line-buffer \
                 run_calculation
    else
        # Single input file
        run_calculation "$INPUT_PATH"
    fi
else
    # Process directory
    if [ -n "$FOLDER_CRITERION" ]; then
        find "$INPUT_PATH" -type f -name "*.inp" ! -name "*extern*" \
            -path "*$FOLDER_CRITERION*" | \
        sort | \
        parallel --joblog "$TEMP_DIR/parallel.log" \
                 -j $MAX_JOBS \
                 --line-buffer \
                 run_calculation
    else
        find "$INPUT_PATH" -type f -name "*.inp" ! -name "*extern*" | \
        sort | \
        parallel --joblog "$TEMP_DIR/parallel.log" \
                 -j $MAX_JOBS \
                 --line-buffer \
                 run_calculation
    fi
fi

# Generate report
{
    echo "Runner Calculations Report"
    echo "--------------------------"
    echo "Execution Date: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "System Configuration:"
    echo "  Total CPUs: $TOTAL_CPUS"
    echo "  Sockets: $SOCKETS"
    echo "  Cores per socket: $CORES_PER_SOCKET"
    echo "  Threads per core: $THREADS_PER_CORE"
    echo "  NUMA nodes: $NUMA_NODES"
    echo
    echo "Run Configuration:"
    echo "  Input Path: $INPUT_PATH"
    echo "  Output Directory: $OUTPUT_DIR"
    echo "  Parallel Jobs: $MAX_JOBS"
    echo "  Threads per Job: $THREADS_PER_JOB"
    echo "  Real Cores Only: $([[ $REAL_CORES -eq 1 ]] && echo 'yes' || echo 'no')"
    echo "  Folder Criterion: $FOLDER_CRITERION"
    echo
    echo "Detailed Results:"
    echo

    # Collect and sort results
    find "$OUTPUT_DIR" -name "*_status.txt" | while read status_file; do
        input_file=${status_file%_status.txt}.inp
        status=$(head -n 1 "$status_file")
        time=$(grep "TIME:" "$status_file" | cut -d' ' -f2)
        echo "Calculation: $input_file"
        echo "Status: $status"
        echo "Execution Time: $time seconds"
        echo
    done
} > "runner_report.txt"

echo "Report generated: runner_report.txt"
