import os
from pathlib import Path
import re
import chardet
import argparse
from multiprocessing import Pool, cpu_count

def detect_encoding(file_path):
    """Detect the encoding of a file using chardet."""
    with open(file_path, 'rb') as file:
        raw_data = file.read()
        result = chardet.detect(raw_data)
        return result['encoding'] or 'utf-8'

def process_file(txt_file):
    """Process a single .txt file to remove specified special characters."""
    special_chars = r'[~`!@#$%^&*()_+=\-{}[\]|\\:;"\'<,>.?/]'
    try:
        # Detect file encoding
        encoding = detect_encoding(txt_file)
        
        # Read the file with detected encoding
        with open(txt_file, 'r', encoding=encoding, errors='replace') as file:
            content = file.read()
        
        # Remove only the specified special characters
        cleaned_content = re.sub(special_chars, '', content)
        
        # Overwrite the original file with same encoding
        with open(txt_file, 'w', encoding=encoding, errors='replace', newline='') as file:
            file.write(cleaned_content)
            
        return f"Processed: {txt_file}"
    except Exception as e:
        return f"Error processing {txt_file}: {str(e)}"

def clean_text_files(input_folder, num_cores):
    """Process all .txt files in the input folder and its subfolders using multiple cores."""
    # Collect all .txt files
    txt_files = list(Path(input_folder).rglob("*.txt"))
    
    if not txt_files:
        print(f"No .txt files found in {input_folder} or its subfolders.")
        return
    
    # Create a process pool with specified number of cores
    with Pool(processes=num_cores) as pool:
        # Process files in parallel and collect results
        results = pool.map(process_file, txt_files)
    
    # Print results
    for result in results:
        print(result)

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Clean .txt files by removing specified special characters.")
    parser.add_argument(
        "--input-dir",
        default="1M_text",
        help="Path to the folder containing .txt files (default: 1M_text)"
    )
    parser.add_argument(
        "--cores",
        type=int,
        default=cpu_count(),
        help=f"Number of CPU cores to use (default: {cpu_count()})"
    )
    
    # Parse arguments
    args = parser.parse_args()
    input_dir = args.input_dir
    num_cores = args.cores
    
    # Validate number of cores
    max_cores = cpu_count()
    if num_cores < 1 or num_cores > max_cores:
        print(f"Error: Number of cores must be between 1 and {max_cores}. Using {max_cores} cores.")
        num_cores = max_cores
    
    # Verify input directory exists
    if not os.path.exists(input_dir):
        print(f"Error: Input folder '{input_dir}' does not exist.")
    else:
        clean_text_files(input_dir, num_cores)
        print(f"All .txt files processed and updated in {input_dir} and its subfolders using {num_cores} cores")