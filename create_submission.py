#!/usr/bin/env python3
"""
Script to create a submission zip file for the project.
Excludes: .git, docs, data, training_checkpoints
Includes: everything else including the keras model and seed_sequence.npy
"""

import zipfile
import os
from pathlib import Path

def create_submission_zip():
    # Define what to exclude
    exclude_dirs = {'.git', 'docs', 'data', 'training_checkpoints', '__pycache__', '.pytest_cache'}
    exclude_files = {'.DS_Store', 'create_submission.py'}  # Exclude this script itself

    # Output zip file name
    output_zip = 'submission.zip'

    # Get the current directory
    root_dir = Path('.')

    print(f"Creating {output_zip}...")
    print(f"Excluding directories: {', '.join(exclude_dirs)}")
    print(f"Excluding files: {', '.join(exclude_files)}")
    print()

    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        file_count = 0

        for root, dirs, files in os.walk('.'):
            # Remove excluded directories from the walk
            dirs[:] = [d for d in dirs if d not in exclude_dirs]

            # Skip if we're in the root and current dir is excluded
            root_path = Path(root)
            if any(excluded in root_path.parts for excluded in exclude_dirs):
                continue

            for file in files:
                if file in exclude_files:
                    continue

                file_path = os.path.join(root, file)
                arcname = file_path.lstrip('./')

                # Add file to zip
                zipf.write(file_path, arcname)
                print(f"Added: {arcname}")
                file_count += 1

    print()
    print(f"✓ Successfully created {output_zip}")
    print(f"✓ Total files: {file_count}")

    # Show zip file size
    zip_size = os.path.getsize(output_zip)
    print(f"✓ Zip file size: {zip_size / 1024 / 1024:.2f} MB")

if __name__ == '__main__':
    create_submission_zip()
