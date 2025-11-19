#!/usr/bin/env python3
"""
Script to create a submission zip file for the project.
Excludes: .git, docs, data, training_checkpoints
Includes: everything else including the keras model and seed_sequence.npy
"""

import zipfile
import os
import sys
from pathlib import Path

def create_submission_zip():
    # Output zip file name
    output_zip = 'submission.zip'

    # Define what to exclude
    exclude_dirs = {'.git', 'docs', 'data', 'training_checkpoints', '__pycache__', '.pytest_cache'}
    exclude_files = {'.DS_Store', 'create_submission.py', output_zip}  # Exclude this script and the output zip

    print(f"Creating {output_zip}...")
    print(f"Excluding directories: {', '.join(sorted(exclude_dirs))}")
    print()

    try:
        # Use ZIP_STORED (no compression) for faster processing
        with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_STORED) as zipf:
            file_count = 0
            files_added = []

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
                    try:
                        print(f"Adding: {arcname}...", end='\r')
                        sys.stdout.flush()
                        zipf.write(file_path, arcname)
                        files_added.append(arcname)
                        file_count += 1
                    except Exception as e:
                        print(f"\nWarning: Could not add {arcname}: {e}")

        print(f"\n\nFiles added to zip:")
        for f in sorted(files_added):
            print(f"  - {f}")

        print()
        print(f"✓ Successfully created {output_zip}")
        print(f"✓ Total files: {file_count}")

        # Show zip file size
        zip_size = os.path.getsize(output_zip)
        print(f"✓ Zip file size: {zip_size / 1024 / 1024:.2f} MB")

    except Exception as e:
        print(f"\n✗ Error creating zip file: {e}")
        sys.exit(1)

if __name__ == '__main__':
    create_submission_zip()
