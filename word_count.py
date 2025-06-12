import os
from pathlib import Path
from multiprocessing import Pool
import argparse
from collections import defaultdict

def read_lines_generator(file_path, max_lines=None):
    """Generator to read lines from a file, yielding one line at a time."""
    lines_read = 0
    with open(file_path, 'r', encoding='utf-8') as f:
        while True:
            if max_lines and lines_read >= max_lines:
                break
            line = f.readline()
            if not line:  # End of file
                break
            yield line.rstrip('\n')
            lines_read += 1

def get_next_folder_number(base_path, language):
    """Find the next available folder number for a given language."""
    folder_num = 1
    while True:
        folder_path = Path(base_path) / f"input_{folder_num}"
        file_path = folder_path / f"{language}.txt"
        if not file_path.exists():
            return folder_num
        folder_num += 1

def process_single_file(args):
    """
    Process a single text file, splitting it into 1000-line chunks.
    Args: (file_path, base_output_path, lines_per_file)
    """
    file_path, base_output_path, lines_per_file = args
    language = Path(file_path).stem
    
    # Get the next available folder number for this language
    current_folder_num = get_next_folder_number(base_output_path, language)
    
    current_lines = []
    line_count = 0
    total_lines_processed = 0
    
    # Read lines using generator
    for line in read_lines_generator(file_path):
        current_lines.append(line)
        line_count += 1
        total_lines_processed += 1
        
        # When we reach the target lines per file, save the current batch
        if line_count >= lines_per_file:
            # Create output folder
            output_folder = Path(base_output_path) / f"input_{current_folder_num}"
            output_folder.mkdir(parents=True, exist_ok=True)
            
            # Write file
            output_file = output_folder / f"{language}.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(current_lines) + '\n')
            
            print(f"Created {output_file} with {line_count} lines")
            
            # Reset for next batch
            current_lines = []
            line_count = 0
            current_folder_num += 1
    
    # Write any remaining lines to the final file
    if current_lines:
        output_folder = Path(base_output_path) / f"input_{current_folder_num}"
        output_folder.mkdir(parents=True, exist_ok=True)
        
        output_file = output_folder / f"{language}.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(current_lines) + '\n')
        
        print(f"Created {output_file} with {line_count} lines (final chunk)")
    
    return total_lines_processed, language

def collect_all_text_files(input_base_path):
    """Collect all text files from all input_* folders."""
    input_path = Path(input_base_path)
    all_files = []
    
    # Look for input_* folders
    for folder in sorted(input_path.glob('input_*')):
        if folder.is_dir():
            # Get all .txt files in this folder
            txt_files = list(folder.glob('*.txt'))
            all_files.extend(txt_files)
            print(f"Found {len(txt_files)} text files in {folder}")
    
    return all_files

def group_files_by_language(file_list):
    """Group files by language to maintain order."""
    language_files = defaultdict(list)
    
    for file_path in file_list:
        language = file_path.stem
        language_files[language].append(file_path)
    
    # Sort files within each language group by their parent folder number
    for language in language_files:
        language_files[language].sort(key=lambda x: int(x.parent.name.split('_')[1]))
    
    return language_files

def process_language_files_sequentially(language, file_list, base_output_path, lines_per_file):
    """Process all files for a single language sequentially to maintain order."""
    print(f"Processing {len(file_list)} files for language: {language}")
    
    # Get the next available folder number for this language
    current_folder_num = get_next_folder_number(base_output_path, language)
    
    current_lines = []
    line_count = 0
    total_lines_processed = 0
    
    # Process each file in order
    for file_path in file_list:
        print(f"  Reading from {file_path}")
        
        # Read all lines from current file
        for line in read_lines_generator(file_path):
            current_lines.append(line)
            line_count += 1
            total_lines_processed += 1
            
            # When we reach the target lines per file, save the current batch
            if line_count >= lines_per_file:
                # Create output folder
                output_folder = Path(base_output_path) / f"input_{current_folder_num}"
                output_folder.mkdir(parents=True, exist_ok=True)
                
                # Write file
                output_file = output_folder / f"{language}.txt"
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(current_lines) + '\n')
                
                print(f"    Created {output_file} with {line_count} lines")
                
                # Reset for next batch
                current_lines = []
                line_count = 0
                current_folder_num += 1
    
    # Write any remaining lines to the final file
    if current_lines:
        output_folder = Path(base_output_path) / f"input_{current_folder_num}"
        output_folder.mkdir(parents=True, exist_ok=True)
        
        output_file = output_folder / f"{language}.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(current_lines) + '\n')
        
        print(f"    Created {output_file} with {line_count} lines (final chunk)")
    
    return total_lines_processed

def process_text_files(input_base_path, output_base_path=None, lines_per_file=1000, cores=None):
    """
    Process all text files from input_* folders, splitting each language's files
    into 1000-line chunks while preserving order.
    """
    if output_base_path is None:
        output_base_path = input_base_path
    
    # Collect all text files
    all_files = collect_all_text_files(input_base_path)
    if not all_files:
        print(f"No text files found in {input_base_path}/input_* folders")
        return
    
    print(f"Found {len(all_files)} total text files")
    
    # Group files by language
    language_files = group_files_by_language(all_files)
    
    print(f"Found {len(language_files)} languages: {list(language_files.keys())}")
    
    # Process each language separately to maintain order
    total_lines_all = 0
    for language, file_list in language_files.items():
        total_lines = process_language_files_sequentially(
            language, file_list, output_base_path, lines_per_file
        )
        total_lines_all += total_lines
        print(f"Processed {total_lines} lines for {language}")
    
    print(f"Total lines processed across all languages: {total_lines_all}")

def main():
    parser = argparse.ArgumentParser(
        description='Split text files from input_* folders into 1000-line chunks while preserving order and folder structure.'
    )
    parser.add_argument(
        '--input-path',
        type=str,
        default='1M_texts',
        help='Base path containing input_* folders with text files. Default: 1M_texts'
    )
    parser.add_argument(
        '--output-path',
        type=str,
        default=None,
        help='Base path for output. If not specified, uses same as input-path'
    )
    parser.add_argument(
        '--lines-per-file',
        type=int,
        default=1000,
        help='Number of lines per output file. Default: 1000'
    )
    parser.add_argument(
        '--cores',
        type=int,
        default=None,
        help='Number of CPU cores to use (currently not used due to order preservation requirement)'
    )
    
    args = parser.parse_args()
    
    process_text_files(
        input_base_path=args.input_path,
        output_base_path=args.output_path,
        lines_per_file=args.lines_per_file,
        cores=args.cores
    )

if __name__ == "__main__":
    main()