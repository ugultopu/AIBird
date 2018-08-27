#!/bin/bash
# Run this script from one level above PonyGE2 and AIBird projects. For that,
# symlink this script to one level above PonyGE2 and AIBird projects

# Create output directories named after current date and time
directory="results/$(date '+%Y_%m_%d-%H_%M_%S')"
mkdir -p "PonyGE2/$directory"
mkdir -p "AIBird/$directory"

# Run PonyGE2 script
cd PonyGE2/src
python3 ponyge.py --parameters ai_birds.txt --file_path "$directory" &> "../$directory/output.txt"
# Pass the generated directory's path to the script. Also pass 'positions.txt'
# from the last run of PonyGE2
cd ../..
python3 AIBird/src/python/enumerate-structures.py "AIBird/$directory" "PonyGE2/$directory/positions.txt" &> "AIBird/$directory/output.txt" &
# Save the PID number of the script to a file
echo $! > "AIBird/$directory/ai_birds.pid"
