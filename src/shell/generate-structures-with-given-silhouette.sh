#!/bin/bash
# Run this script from one level above PonyGE2 and AIBird projects. For that,
# symlink this script to one level above PonyGE2 and AIBird projects

# The path to the file that contains the silhouette
silhouette="$1"

# Create output directories named after current date and time
directory="results/$(date '+%Y_%m_%d-%H_%M_%S')"
mkdir -p "AIBird/$directory"

python3 AIBird/src/python/enumerate-structures.py "AIBird/$directory" "$silhouette" &> "AIBird/$directory/output.txt" &
# Save the PID number of the script to a file
echo $! > "AIBird/$directory/ai_birds.pid"
