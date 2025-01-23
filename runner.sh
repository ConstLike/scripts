#!/bin/bash

DEBUG=0

debug_print() {
  if [ $DEBUG -eq 1 ]; then
    echo "[DEBUG] $(date '+%Y-%m-%d %H:%M:%S') - $*" >&2
  fi
}

get_system_info() {
  debug_print "Collecting system information..."
  TOTAL_CPUS=$(lscpu | grep "^CPU(s):" | awk '{print $2}')
  CORES_PER_SOCKET=$(lscpu | grep "^Core(s) per socket:" | awk '{print $4}')
  SOCKETS=$(lscpu | grep "^Socket(s):" | awk '{print $2}')
  THREADS_PER_CORE=$(lscpu | grep "^Thread(s) per core:" | awk '{print $4}')
  NUMA_NODES=$(lscpu | grep "^NUMA node(s):" | awk '{print $3}')

  TOTAL_CPUS=${TOTAL_CPUS:-1}
  CORES_PER_SOCKET=${CORES_PER_SOCKET:-1}
  SOCKETS=${SOCKETS:-1}
  THREADS_PER_CORE=${THREADS_PER_CORE:-1}
  NUMA_NODES=${NUMA_NODES:-1}
}

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
  if [ $errors -gt 0 ]; then
    echo "Found $errors configuration errors"
    exit 1
  fi
}

get_output_dir() {
  local input="$1"
  local output="$2"

  if [ -n "$output" ]; then
    echo "$output"
    return
  fi

  if [ -f "$input" ]; then
    echo "$(dirname "$(realpath "$input")")"
  else
    echo "$(realpath "$input")"
  fi
}

usage() {
  echo "Usage: $0 -i INPUT [-o OUTPUT] [-d]"
  echo "  -i INPUT       Input path (file/directory)"
  echo "  -o OUTPUT      Output directory (optional)"
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

run_calculation() {
  local input_file="$1"
  local base_name=$(basename "$input_file" .inp)
  local dir_name=$(dirname "$(realpath "$input_file")")
  local start_time=$(date +%s)

  debug_print "Starting calculation for: $input_file"
  debug_print "Base name: $base_name"
  debug_print "Directory: $dir_name"

  # Проверка запущенных процессов
  local full_path="$(realpath "$input_file")"
  if pgrep -f "cp2k.ssmp.*$full_path" >/dev/null; then
    debug_print "Skip: Process already running for $full_path"
    return 0
  fi

  # Проверка входного файла
  if [ ! -f "$input_file" ]; then
    echo "Error: Input file not found: $input_file"
    return 1
  fi

  # Создание lockfile
  local lockfile="${dir_name}/${base_name}.lock"
  if ! mkdir "$lockfile" 2>/dev/null; then
    debug_print "Skip: Lock exists for $base_name"
    return 0
  fi
  trap 'rm -rf "$lockfile"' EXIT

  # Настройка переменных окружения
  export OMP_NUM_THREADS=$TOTAL_CPUS
  export OMP_STACKSIZE=128M
  export OMP_PLACES=cores
  export OMP_PROC_BIND=close
  export OMP_WAIT_POLICY=active

  local log_file="${base_name}.log"
  local status_file="${base_name}_status.txt"

  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Running $input_file"
  if cp2k.ssmp -i "$base_name.inp" >"$log_file" 2>&1; then
    local end_time=$(date +%s)
    echo "SUCCESS" >"$status_file"
    echo "TIME: $((end_time - start_time))" >>"$status_file"
    return 0
  else
    local end_time=$(date +%s)
    echo "ERROR" >"$status_file"
    echo "TIME: $((end_time - start_time))" >>"$status_file"
    return 1
  fi
}

# Основная часть скрипта
get_system_info
validate_config

# Парсинг аргументов
while getopts "i:o:c:d" opt; do
  case $opt in
  i) INPUT_PATH="$OPTARG" ;;
  o) OUTPUT_DIR="$OPTARG" ;;
  c) FOLDER_CRITERION="$OPTARG" ;;
  d) DEBUG=1 ;;
  ?) usage ;;
  esac
done

if [ -z "$INPUT_PATH" ]; then
  usage
fi

OUTPUT_DIR=$(get_output_dir "$INPUT_PATH" "$OUTPUT_DIR")
export -f run_calculation
export -f debug_print

echo "Starting calculations at $(date '+%Y-%m-%d %H:%M:%S')"

# Запуск расчетов
if [ -f "$INPUT_PATH" ]; then
  run_calculation "$INPUT_PATH"
else
  if [ -n "$FOLDER_CRITERION" ]; then
    find "$INPUT_PATH" -type f -name "*.inp" ! -name "*extern*" \
      -path "*$FOLDER_CRITERION*" | sort | while read -r input; do
      run_calculation "$input"
    done
  else
    find "$INPUT_PATH" -type f -name "*.inp" ! -name "*extern*" |
      sort | while read -r input; do
      run_calculation "$input"
    done
  fi
fi

# Генерация отчета
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
  echo "  Folder Criterion: $FOLDER_CRITERION"
  echo
  echo "Detailed Results:"
  echo

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

echo "Report generated: runner_report.txt"
