#!/bin/bash

PYTHON_ENV=/home/luca/Documenti/Tesi/comic1111generator/env/bin/python

# Set the target directory to search within
target_dir="$1"

# Check if the target directory is provided
if [ -z "$target_dir" ]; then
  echo "Usage: $0 <target_directory>"
  exit 1
fi

# Find all JSON files recursively within the target directory
find "$target_dir" -type f -name "fumetto_*" -print0 | while IFS= read -r -d $'\0' json_file; do
  # Inside the for loop, you can now work with each found JSON file
  echo "Processing JSON file: \"$json_file\""

  rm -rf $json_file


  echo "--------------------"
done

echo "Finished processing all JSON files."

exit 0