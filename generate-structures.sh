#!/bin/bash

# Create a directory named after current date and time
directory="results/$(date '+%Y_%m_%d-%H_%M_%S')"
mkdir -p $directory
# Run the script with 'nohup' in the background. Pass the generated directory's
# path to the script
nohup python3 enumerate-structures.py "$directory" &> "$directory/output.txt" &
# Save the PID number of the script to a file
echo $! > "$directory/ai_birds.pid"
