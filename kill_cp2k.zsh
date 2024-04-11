#!/usr/bin/env zsh

# Name of the process to be killed
PROCESS_NAME="cp2k.ssmp"

# Find the process ID (PID) of the process
PIDS=$(pgrep ${PROCESS_NAME})

# Check if any PIDs were found
if [[ -z "$PIDS" ]]; then
    echo "No processes found with the name ${PROCESS_NAME}."
else
    # Kill each process found
    for PID in $PIDS; do
        echo "Killing process ${PROCESS_NAME} with PID ${PID}."
        kill ${PID}  # Use 'kill -9 ${PID}' to forcefully kill the process if needed
        # Check if the kill command was successful
        if [[ $? -eq 0 ]]; then
           echo "Process ${PID} killed successfully."
        else
           echo "Failed to kill process ${PID}."
        fi
    done
fi
echo " "
