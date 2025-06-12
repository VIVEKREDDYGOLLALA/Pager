import os
import shutil
import math

def distribute_files(input_folder, max_files_per_folder=5000, max_folders_for_small_set=3, small_set_threshold=1500):
    # Check if input folder exists
    if not os.path.exists(input_folder):
        print(f"Error: Input folder '{input_folder}' does not exist.")
        return

    # Get list of all files in the input folder
    files = [f for f in os.listdir(input_folder) if os.path.isfile(os.path.join(input_folder, f))]
    total_files = len(files)

    if total_files == 0:
        print("Error: No files found in the input folder.")
        return

    # Determine number of folders and files per folder
    if total_files <= small_set_threshold:
        files_per_folder = math.ceil(total_files / max_folders_for_small_set)
        num_folders = max_folders_for_small_set
    else:
        files_per_folder = max_files_per_folder
        num_folders = math.ceil(total_files / max_files_per_folder)

    print(f"Total files: {total_files}")
    print(f"Will create {num_folders} folders with up to {files_per_folder} files each.")

    # Create output folders and distribute files
    for i in range(num_folders):
        # Create new folder
        output_folder = os.path.join(input_folder, f"output_folder_{i+1}")
        os.makedirs(output_folder, exist_ok=True)

        # Calculate start and end indices for files
        start_idx = i * files_per_folder
        end_idx = min((i + 1) * files_per_folder, total_files)

        # Copy files to the new folder
        for file_idx in range(start_idx, end_idx):
            src_path = os.path.join(input_folder, files[file_idx])
            dst_path = os.path.join(output_folder, files[file_idx])
            shutil.copy2(src_path, dst_path)
            print(f"Copied {files[file_idx]} to {output_folder}")

    print("File distribution complete.")

if __name__ == "__main__":
    input_folder = "BBOX"
    distribute_files(input_folder)