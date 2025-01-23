#!/bin/bash

# Debug mode flag
DEBUG=0

# Debug print function
debug_print() {
    if [ $DEBUG -eq 1 ]; then
        echo "[DEBUG] $(date '+%Y-%m-%d %H:%M:%S') - $*" >&2
    fi
}

debug_print "Report generated: runner_report.txt"
echo "Report generated: runner_report.txt" "[DEBUG] $(date '+%Y-%m-%d %H:%M:%S') - $*" >&2
    fi
}

# Get system info with validation
get_system_info() {
    debug_print "Collecting system information..."

    TOTAL_CPUS=$(lscpu | grep "^CPU(s):" | awk '{print $2}')
    CORES_PER_SOCKET=$(lscpu | grep "^Core(s) per socket:" | awk '{print $4}')
    SOCKETS=$(lscpu | grep "^Socket(s):" | awk '{print $2}')
    THREADS_PER_CORE=$(lscpu | grep "^Thread(s) per core:" | awk '{print $4}')
    NUMA_NODES=$(lscpu | grep "^NUMA node(s):" | awk '{print $3}')

    # Ensure minimum values and validate
    TOTAL_CPUS=${TOTAL_CPUS:-1}
    CORES_PER_SOCKET=${CORES_PER_SOCKET:-1}
    SOCKETS=${SOCKETS:-1}
    THREADS_PER_CORE=${THREADS_PER_CORE:-1}
    NUMA_NODES=${NUMA_NODES:-1}

    debug_print "System configuration detected:"
    debug_print "  Total CPUs: $TOTAL_CPUS"
    debug_print "  Sockets: $SOCKETS"
    debug_print "  Cores per socket: $CORES_PER_SOCKET"
    debug_print "  Threads per core: $THREADS_PER_CORE"
    debug_print "  NUMA nodes: $NUMA_NODES"
}

# Configuration validation
validate_config() {
    debug_print "Validating configuration..."

    local errors=0

    if [ "$TOTAL_CPUS" -lt 1 ]; then
        echo "Error: Invalid CPU count: $TOTAL_CPUS"
        errors=$((errors + 1))
    fi

    if [ "$CORES_PER_SOCKET" -lt 1 ]; then
        echo "Error: Invalid cores per socket: $CORES_PER_SOCKET"
        errors=$((errors + 1))
    fi

    if [ "$THREADS_PER_CORE" -lt 1 ]; then
        echo "Error: Invalid threads per core: $THREADS_PER_CORE"
        errors=$((errors + 1))
    fi

    if [ "$NUMA_NODES" -lt 1 ]; then
        echo "Warning: No NUMA nodes detected, setting to 1"
        NUMA_NODES=1
    fi

    if [ $errors -gt 0 ]; then
        echo "Found $errors configuration errors"
        exit 1
    fi

    debug_print "Configuration validation complete"
}

# Check required tools
check_requirements() {
    debug_print "Checking required tools..."
    local missing_tools=()

    if ! command -v parallel >/dev/null 2>&1; then
        missing_tools+=("parallel (sudo apt-get install parallel)")
    fi

    if ! command -v numactl >/dev/null 2>&1; then
        missing_tools+=("numactl (sudo apt-get install numactl)")
    fi

    if [ ${#missing_tools[@]} -ne 0 ]; then
        echo "Error: Required tools are missing:"
        printf '%s\n' "${missing_tools[@]}"
        exit 1
    fi

    debug_print "All required tools are available"
}

# Path resolution
get_output_dir() {
    local input="$1"
    local output="$2"

    debug_print "Resolving output directory..."
    debug_print "Input path: $input"
    debug_print "Specified output: $output"

    if [ -n "$output" ]; then
        debug_print "Using specified output directory: $output"
        echo "$output"
        return
    fi

    if [ -f "$input" ]; then
        local dir=$(dirname "$(realpath "$input")")
        debug_print "Using input file directory: $dir"
        echo "$dir"
    else
        local dir=$(realpath "$input")
        debug_print "Using input directory: $dir"
        echo "$dir"
    fi
}

# Help message
usage() {
    echo "Usage: $0 -i INPUT [-o OUTPUT] [-r] [-c CRITERION] [-d]"
    echo "  -i INPUT       Input path (file/directory/report)"
    echo "  -o OUTPUT      Output directory (optional)"
    echo "  -r            Use only real cores (no HT)"
    echo "  -c CRITERION   Folder name filter"
    echo "  -d            Enable debug output"
    echo
    echo "System configuration:"
    echo "  Total CPUs: $TOTAL_CPUS"
    echo "  Sockets: $SOCKETS"
    echo "  Cores per socket: $CORES_PER_SOCKET"
    echo "  Threads per core: $THREADS_PER_CORE"
    echo "  NUMA nodes: $NUMA_NODES"
    exit 1
}

# Function to determine runner type
get_runner() {
    local folder_name="$1"
    debug_print "Determining runner for: $folder_name"

    if [[ "${folder_name,,}" == *"fat-molcas"* ]]; then
        debug_print "Selected runner: cp2k.sdbg"
        echo "cp2k.sdbg"
    elif [[ "${folder_name,,}" == *"cp2k"* ]]; then
        debug_print "Selected runner: cp2k.sdbg"
        echo "cp2k.sdbg"
    elif [[ "${folder_name,,}" == *"molcas"* ]]; then
        debug_print "Selected runner: pymolcas"
        echo "pymolcas"
    else
        debug_print "Unknown runner type"
        echo "unknown"
    fi
}

# Function to run single calculation
run_calculation() {
    local input_file="$1"
    local base_name=$(basename "$input_file" .inp)
    local dir_name=$(dirname "$(realpath "$input_file")")
    local start_time=$(date +%s)

    debug_print "Starting calculation for: $input_file"
    debug_print "Base name: $base_name"
    debug_print "Directory: $dir_name"

    # Validate input file
    if [ ! -f "$input_file" ]; then
        echo "Error: Input file not found: $input_file"
        debug_print "Input file not found: $input_file"
        return 1
    fi

    # Set output directory
    local out_dir
    if [[ "$INPUT_PATH" == *"_report.txt" ]]; then
        out_dir="$dir_name"
    elif [ -f "$INPUT_PATH" ]; then
        out_dir="$(realpath "$OUTPUT_DIR")"
    else
        local input_base="$(realpath "$INPUT_PATH")"
        local rel_path=${dir_name#$input_base}
        out_dir="$(realpath "$OUTPUT_DIR")${rel_path}"
    fi

    debug_print "Output directory: $out_dir"

    mkdir -p "$out_dir" || {
        echo "Error: Failed to create output directory: $out_dir"
        debug_print "Failed to create directory: $out_dir"
        return 1
    }

    cd "$out_dir" || {
        echo "Error: Failed to change to output directory: $out_dir"
        debug_print "Failed to change directory to: $out_dir"
        return 1
    }

    # Get runner
    local runner=$(get_runner "$dir_name")
    if [ "$runner" = "unknown" ]; then
        echo "Error: Unknown calculation type for $input_file"
        debug_print "Unknown runner type for: $input_file"
        return 1
    fi

    # NUMA binding
    local job_num=$((PARALLEL_SEQ - 1))
    local numa_node=0

    if [ "$NUMA_NODES" -gt 1 ]; then
        numa_node=$((job_num % NUMA_NODES))
    fi

    debug_print "Job number: $job_num"
    debug_print "NUMA node: $numa_node"

    local cpu_range
    if [ $REAL_CORES -eq 1 ]; then
        local start_cpu=$((numa_node * CORES_PER_SOCKET))
        local end_cpu=$((start_cpu + THREADS_PER_JOB - 1))
        cpu_range="$start_cpu-$end_cpu"
        debug_print "Real cores mode: CPU range $cpu_range"
    else
        local cpus_per_node=$((TOTAL_CPUS / NUMA_NODES))
        local start_cpu=$((numa_node * cpus_per_node))
        local end_cpu=$((start_cpu + THREADS_PER_JOB - 1))
        cpu_range="$start_cpu-$end_cpu"
        debug_print "HT mode: CPU range $cpu_range"
    fi

    # Run with retries
    local status_file="${base_name}_status.txt"
    local log_file="${base_name}.log"
    local attempt=1

    while [ $attempt -le $MAX_RESTARTS ]; do
        debug_print "Starting attempt $attempt for $input_file"
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Running $input_file (Attempt $attempt)"
        echo "NUMA node: $numa_node, CPU range: $cpu_range"

        if numactl --cpunodebind=$numa_node --membind=$numa_node \
            $runner "$base_name.inp" >"$log_file" 2>&1; then
            local end_time=$(date +%s)
            echo "SUCCESS" >"$status_file"
            echo "TIME: $((end_time - start_time))" >>"$status_file"
            debug_print "Calculation successful"
            return 0
        fi

        if grep -q "Segmentation fault" "$log_file"; then
            ((attempt++))
            if [ $attempt -le $MAX_RESTARTS ]; then
                debug_print "Segmentation fault detected, retrying..."
                echo "Segmentation fault detected, retrying..."
                sleep 2
                continue
            fi
        fi

        local end_time=$(date +%s)
        echo "ERROR" >"$status_file"
        echo "TIME: $((end_time - start_time))" >>"$status_file"
        debug_print "Calculation failed"
        return 1
    done
}

# Main script execution starts here
debug_print "Script started"

# Get system info and validate
get_system_info
validate_config
check_requirements

# Configuration defaults
MAX_RESTARTS=3
FOLDER_CRITERION=""
REAL_CORES=0

# Parse arguments
while getopts "i:o:rc:d" opt; do
    case $opt in
    i) INPUT_PATH="$OPTARG" ;;
    o) OUTPUT_DIR="$OPTARG" ;;
    r) REAL_CORES=1 ;;
    c) FOLDER_CRITERION="$OPTARG" ;;
    d) DEBUG=1 ;;
    ?) usage ;;
    esac
done

if [ -z "$INPUT_PATH" ]; then
    usage
fi

debug_print "Arguments parsed:"
debug_print "INPUT_PATH: $INPUT_PATH"
debug_print "OUTPUT_DIR: $OUTPUT_DIR"
debug_print "REAL_CORES: $REAL_CORES"
debug_print "FOLDER_CRITERION: $FOLDER_CRITERION"

# Validate input path
if [ ! -e "$INPUT_PATH" ]; then
    echo "Error: Input path does not exist: $INPUT_PATH"
    exit 1
fi

# Calculate optimal configuration
if [ $REAL_CORES -eq 1 ]; then
    THREADS_PER_JOB=$CORES_PER_SOCKET
    MAX_JOBS=$SOCKETS
else
    THREADS_PER_JOB=$((CORES_PER_SOCKET * THREADS_PER_CORE))
    MAX_JOBS=$SOCKETS
fi

debug_print "Calculated configuration:"
debug_print "THREADS_PER_JOB: $THREADS_PER_JOB"
debug_print "MAX_JOBS: $MAX_JOBS"

# Set output directory
OUTPUT_DIR=$(get_output_dir "$INPUT_PATH" "$OUTPUT_DIR")
debug_print "Final output directory: $OUTPUT_DIR"

# Setup environment
export OMP_NUM_THREADS=$THREADS_PER_JOB
export MKL_NUM_THREADS=$THREADS_PER_JOB
export OMP_PLACES=cores
export OMP_PROC_BIND=close

debug_print "Environment variables set:"
debug_print "OMP_NUM_THREADS: $OMP_NUM_THREADS"
debug_print "MKL_NUM_THREADS: $MKL_NUM_THREADS"

export -f run_calculation
export -f get_runner
export -f debug_print

# Create temporary directory for logs
TEMP_DIR=$(mktemp -d)
trap 'rm -rf "$TEMP_DIR"' EXIT

debug_print "Temporary directory created: $TEMP_DIR"

# Find and run calculations
echo "Starting calculations at $(date '+%Y-%m-%d %H:%M:%S')"

if [ -f "$INPUT_PATH" ]; then
    if [[ "$INPUT_PATH" == *"_report.txt" ]]; then
        debug_print "Processing failed calculations from report"
        grep -B 1 "Status: ERROR" "$INPUT_PATH" |
            grep "Calculation:" |
            cut -d' ' -f2- |
            parallel --joblog "$TEMP_DIR/parallel.log" \
                -j $MAX_JOBS \
                --line-buffer \
                run_calculation
    else
        debug_print "Processing single input file"
        run_calculation "$INPUT_PATH"
    fi
else
    debug_print "Processing directory with criterion: $FOLDER_CRITERION"
    if [ -n "$FOLDER_CRITERION" ]; then
        find "$INPUT_PATH" -type f -name "*.inp" ! -name "*extern*" \
            -path "*$FOLDER_CRITERION*" |
            sort |
            parallel --joblog "$TEMP_DIR/parallel.log" \
                -j $MAX_JOBS \
                --line-buffer \
                run_calculation
    else
        find "$INPUT_PATH" -type f -name "*.inp" ! -name "*extern*" |
            sort |
            parallel --joblog "$TEMP_DIR/parallel.log" \
                -j $MAX_JOBS \
                --line-buffer \
                run_calculation
    fi
fi

debug_print "All calculations completed"

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
} >"runner_report.txt"

debug_print "Report generated: runner_report.txt"
echo "Report generated: runner_report.txt"
