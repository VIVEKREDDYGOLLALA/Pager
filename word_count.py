import os
from pathlib import Path
from multiprocessing import Pool
import argparse

def read_lines_generator(file_path, max_lines):
    """Generator to read lines from a file up to max_lines, yielding one line at a time."""
    lines_read = 0
    with open(file_path, 'r', encoding='utf-8') as f:
        while lines_read < max_lines:
            line = f.readline()
            if not line:  # End of file
                break
            yield line.rstrip('\n')
            lines_read += 1

def process_single_text_file(args):
    """
    Process a single text file, splitting it into 10 files with up to max_lines_per_file lines each.
    Args: (file_path, output_base_folder, max_lines_per_file, total_max_lines)
    """
    file_path, output_base_folder, max_lines_per_file, total_max_lines = args
    language = Path(file_path).stem
    
    # Create base output folder
    Path(output_base_folder).mkdir(parents=True, exist_ok=True)
    
    # Initialize variables
    folder_count = 100  # Fixed number of output folders
    lines_per_folder = max_lines_per_file  # 15,000 lines per file
    current_lines = []
    line_count = 0
    folder_index = 1
    total_lines_processed = 0
    
    # Read lines using generator to minimize memory usage
    for line in read_lines_generator(file_path, total_max_lines):
        if total_lines_processed >= total_max_lines:
            break
            
        if line_count >= lines_per_folder:
            # Save current batch
            output_subfolder = Path(output_base_folder) / f"input_{folder_index}"
            output_subfolder.mkdir(parents=True, exist_ok=True)
            output_file = output_subfolder / f"{language}.txt"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(current_lines) + '\n')
            
            print(f"Created {output_file} with {line_count} lines")
            
            # Reset for next batch
            current_lines = []
            line_count = 0
            folder_index += 1
            
            # Stop if we've created 10 folders
            if folder_index > folder_count:
                break
        
        current_lines.append(line)
        line_count += 1
        total_lines_processed += 1
    
    # Write any remaining lines to the final folder (up to folder 10)
    if current_lines and folder_index <= folder_count:
        output_subfolder = Path(output_base_folder) / f"input_{folder_index}"
        output_subfolder.mkdir(parents=True, exist_ok=True)
        output_file = output_subfolder / f"{language}.txt"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(current_lines) + '\n')
        
        print(f"Created {output_file} with {line_count} lines")
    
    # Fill remaining folders with empty files if needed
    while folder_index <= folder_count:
        output_subfolder = Path(output_base_folder) / f"input_{folder_index}"
        output_subfolder.mkdir(parents=True, exist_ok=True)
        output_file = output_subfolder / f"{language}.txt"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('')  # Create empty file
        
        print(f"Created empty {output_file}")
        folder_index += 1
    
    return total_lines_processed, language, folder_count

def process_text_files(input_folder, output_base_folder, max_lines_per_file=1_000, total_max_lines=100_000, cores=None):
    """
    Process all text files in input_folder using multiple CPU cores,
    splitting each into 10 files with up to max_lines_per_file lines.
    """
    input_path = Path(input_folder)
    
    # Get list of text files
    text_files = list(input_path.glob('*.txt'))
    if not text_files:
        print(f"No text files found in {input_folder}")
        return
    
    # Determine number of CPU cores to use
    if cores is None:
        cores = os.cpu_count()
    cores = min(cores, len(text_files))  # Don't use more cores than files
    
    print(f"Using {cores} CPU cores to process {len(text_files)} files")
    
    # Prepare arguments for each file
    tasks = [(file_path, output_base_folder, max_lines_per_file, total_max_lines) for file_path in text_files]
    
    # Process files in parallel
    with Pool(processes=cores) as pool:
        results = pool.map(process_single_text_file, tasks)
    
    # Summarize results
    total_lines_processed = 0
    for total_lines, language, folder_count in results:
        total_lines_processed += total_lines
        print(f"Processed {total_lines} lines from {language}.txt into {folder_count} subfolders")
    
    print(f"Total lines processed: {total_lines_processed} into {output_base_folder}")

def main():
    parser = argparse.ArgumentParser(
        description='Split large text files into 10 subfolders with up to 15,000 lines per file using multiple CPU cores.'
    )
    parser.add_argument(
        '--input-folder',
        type=str,
        default='input_texts',
        help='Folder containing input text files (e.g., hindi.txt, urdu.txt). Default: input_texts'
    )
    parser.add_argument(
        '--output-folder',
        type=str,
        default='input_folder',
        help='Base folder for output subfolders (input_1 to input_10). Default: input_folder'
    )
    parser.add_argument(
        '--cores',
        type=int,
        default=None,
        help='Number of CPU cores to use. Defaults to number of available cores.'
    )
    
    args = parser.parse_args()
    
    process_text_files(
        input_folder=args.input_folder,
        output_base_folder=args.output_folder,
        max_lines_per_file=1_000,
        total_max_lines=100_000,
        cores=args.cores
    )

if __name__ == "__main__":
    main()