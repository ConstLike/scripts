#!/usr/bin/env zsh

# Name of the process to be killed
PROCESS_NAME="cp2k"

# Find the process ID (PID) of the process
PIDS=$(pgrep -f ${PROCESS_NAME})

# Check if any PIDs were found
if [[ -z "$PIDS" ]]; then
    echo "No processes found with the name ${PROCESS_NAME}."
    else
echo "Killing all processes with the name ${PROCESS_NAME}."
    # Convert the newline-separated PIDs into an array
    PIDS_ARRAY=("${(@f)PIDS}")

    # Kill each process found
    for PID in "${PIDS_ARRAY[@]}"; do
       echo "Killing process ${PROCESS_NAME} with PID ${PID}."
       kill ${PID}  # Use 'kill -9 ${PID}' to forcefully kill the process if needed
       # Check if the kill command was successful
       if [[ $? -eq 0 ]]; then
          echo "Process ${PID} killed successfully."
       else
          echo "Failed to kill process ${PID}."
       fi
    done

    # Optional: Kill all child processes (if any)
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
