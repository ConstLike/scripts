#!/bin/bash

# Specify the path to the file where you want to save the information
output_file="system_info.txt"

# Get Linux distribution and version information
echo "=== Linux Distribution Information ===" > $output_file
lsb_release -a >> $output_file 2>/dev/null || cat /etc/*release >> $output_file

# Get CPU architecture information
echo -e "\n=== CPU Information ===" >> $output_file
lscpu >> $output_file

# Get memory information
echo -e "\n=== Memory Information ===" >> $output_file
free -h >> $output_file

# Get disk space information
echo -e "\n=== Disk Space Information ===" >> $output_file
df -h >> $output_file

# Get PCI devices information
echo -e "\n=== PCI Devices Information ===" >> $output_file
lspci >> $output_file

# Get network interfaces information
echo -e "\n=== Network Interfaces Information ===" >> $output_file
ip a >> $output_file

# Get loaded kernel modules information
echo -e "\n=== Loaded Kernel Modules Information ===" >> $output_file
lsmod >> $output_file

# Get user accounts information
echo -e "\n=== User Accounts Information ===" >> $output_file
cat /etc/passwd >> $output_file

# Get system uptime
echo -e "\n=== System Uptime ===" >> $output_file
uptime >> $output_file

echo "System information has been saved to $output_file"
