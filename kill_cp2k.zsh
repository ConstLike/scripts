#!/usr/bin/env zsh

PROCESS_NAMES=("cp2k.sdbg" "cp2k.ssmp" "cp2k.psmp" "cp2k.pdbg", "pymolcas")

for PROCESS_NAME in "${PROCESS_NAMES[@]}"; do
    echo "Checking for processes with the name: ${PROCESS_NAME}"

    PIDS=$(pgrep -f ${PROCESS_NAME})

    if [[ -z "$PIDS" ]]; then
        echo "No processes found with the name ${PROCESS_NAME}."
    else
        echo "Killing all processes with the name ${PROCESS_NAME}."
        PIDS_ARRAY=("${(@f)PIDS}")

        for PID in "${PIDS_ARRAY[@]}"; do
            echo "Killing process ${PROCESS_NAME} with PID ${PID}."
            kill ${PID}
            if [[ $? -eq 0 ]]; then
                echo "Process ${PID} killed successfully."
            else
                echo "Failed to kill process ${PID}."
            fi
        done

        echo "Killing all child processes of ${PROCESS_NAME}."
        for PID in "${PIDS_ARRAY[@]}"; do
            pkill -P ${PID}
            if [[ $? -eq 0 ]]; then
                echo "Child processes of PID ${PID} killed successfully."
            else
                echo "Failed to kill child processes of PID ${PID}."
            fi
        done
    fi
done

echo "All processes and child processes from the list have been handled."

