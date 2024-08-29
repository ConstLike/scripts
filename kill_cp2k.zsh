#!/usr/bin/env zsh

PROCESS_NAME="cp2k.sdbg"

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
 echo "All processes and child processes of ${PROCESS_NAME} have been killed."
