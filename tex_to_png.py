import os
import subprocess
from pdf2image import convert_from_path
import multiprocessing
from functools import partial
import time
import shutil

def convert_tex_to_png(tex_file_path, input_folder=None, output_folder=None, timeout=20, dpi=300):
    """
    Convert a TeX file to PNG format.
    
    Args:
        tex_file_path: Path to the TeX file
        input_folder: Base input folder to maintain relative directory structure
        output_folder: Custom output folder (if None, use the input file directory)
        timeout: Maximum time in seconds for compilation
        dpi: Resolution of the output image
        
    Returns:
        Tuple with (success_status, file_path, error_message)
    """
    # Define file names and paths
    base_name = os.path.basename(tex_file_path)
    file_name, _ = os.path.splitext(base_name)
    
    # Get the directory where the tex file is located for temporary files
    temp_folder = os.path.dirname(tex_file_path)
    
    # Determine output folder with subdirectory structure preserved
    if output_folder is not None and input_folder is not None:
        # Get the relative path from the input folder
        rel_path = os.path.relpath(temp_folder, input_folder)
        # Create the same subdirectory structure in the output folder
        if rel_path != '.':  # Only if there's actually a subdirectory
            specific_output_folder = os.path.join(output_folder, rel_path)
        else:
            specific_output_folder = output_folder
    else:
        specific_output_folder = temp_folder
    
    # Create output directory if it doesn't exist
    os.makedirs(specific_output_folder, exist_ok=True)
    
    # Remove '_0000' only if it appears at the end of the file name
    if file_name.endswith('_0000'):
        file_name = file_name[:-5]
    
    # Define output paths
    pdf_file_path = os.path.join(temp_folder, f"{file_name}.pdf")
    png_file_path = os.path.join(specific_output_folder, f"{file_name}.png")

    try:
        # Print which process is handling this file
        print(f"Process {multiprocessing.current_process().name} processing {tex_file_path}")
        print(f"  Output will be saved to {png_file_path}")
        
        # Compile .tex to .pdf using XeLaTeX in non-stop mode with a timeout
        result = subprocess.run(
            ['xelatex', '-interaction=nonstopmode', '-output-directory', temp_folder, tex_file_path],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, text=True
        )

        # Check if there were errors during compilation
        if result.returncode != 0:
            stderr_output = result.stderr if result.stderr else ""
            if "! Package tikz Error:" in stderr_output:
                raise Exception(f"LaTeX compilation failed for {tex_file_path} with TikZ error.")
            else:
                raise Exception(f"LaTeX compilation failed for {tex_file_path} with return code {result.returncode}")

        # Convert .pdf to .png with higher DPI for better resolution
        if os.path.exists(pdf_file_path):
            # Increased DPI for higher resolution
            images = convert_from_path(pdf_file_path, dpi=dpi)
            
            # Check if PDF has at least 2 pages (to access the second page)
            if len(images) >= 2:
                # Save the second page as PNG (index 1)
                images[1].save(png_file_path, 'PNG')
            elif len(images) == 1:
                # If only one page, use that page but log a warning
                print(f"Warning: PDF {pdf_file_path} only has one page. Using the first page instead of second.")
                images[0].save(png_file_path, 'PNG')
            else:
                raise Exception(f"PDF conversion generated no images for {pdf_file_path}")
        else:
            raise Exception(f"PDF file not found: {pdf_file_path}")

        return (True, tex_file_path, None)  # Indicate success

    except subprocess.TimeoutExpired:
        print(f"Timeout expired for {tex_file_path}. Skipping this file.")
        return (False, tex_file_path, "Timeout expired")
    except Exception as e:
        print(f"An error occurred for {tex_file_path}: {e}")
        return (False, tex_file_path, str(e))

    finally:
        # Clean up temporary files
        for ext in ['.aux', '.log', '.out', '.synctex.gz']:
            aux_file = os.path.join(temp_folder, f"{file_name}{ext}")
            if os.path.exists(aux_file):
                os.remove(aux_file)
        
        # Remove PDF file after conversion
        if os.path.exists(pdf_file_path):
            os.remove(pdf_file_path)

def process_all_tex_files(input_folder, output_folder=None, log_file='skipped_files.txt', timeout=60, num_processes=8, dpi=300):
    """
    Process all TeX files in a folder and convert them to PNG images.
    
    Args:
        input_folder: Folder containing TeX files
        output_folder: Folder for output PNG files (defaults to input folder if None)
        log_file: File to log skipped files
        timeout: Maximum time in seconds for compilation
        num_processes: Number of parallel processes
        dpi: Resolution of output images
    """
    start_time = time.time()
    
    # Use input folder as output folder if not specified
    if output_folder is None:
        output_folder = input_folder
    
    # Create output directory if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    
    # Collect all .tex files to process
    tex_files = []
    for root, dirs, files in os.walk(input_folder):
        for file in files:
            if file.endswith('.tex'):
                tex_files.append(os.path.join(root, file))
    
    print(f"Found {len(tex_files)} TEX files to process using {num_processes} CPU cores.")
    print(f"Input folder: {input_folder}")
    print(f"Output folder: {output_folder}")
    print(f"Subdirectory structure will be preserved in the output folder.")
    
    # Create a pool of worker processes
    pool = multiprocessing.Pool(processes=num_processes)
    
    # Create a partial function with fixed parameters
    convert_func = partial(convert_tex_to_png, input_folder=input_folder, output_folder=output_folder, 
                           timeout=timeout, dpi=dpi)
    
    # Map the function to all TEX files and get results
    results = pool.map(convert_func, tex_files)
    
    # Close the pool and wait for all processes to complete
    pool.close()
    pool.join()
    
    # Process results to collect skipped files
    skipped_files = []
    for result, file_path, error in results:
        if not result:
            skipped_files.append((file_path, error))
    
    # Write skipped files to log
    if skipped_files:
        # Save log file in the output folder
        log_path = os.path.join(output_folder, log_file)
        with open(log_path, 'w') as f:
            for file_path, error in skipped_files:
                f.write(f"{file_path} - Error: {error}\n")
        print(f"Skipped {len(skipped_files)} files. Details have been logged to {log_path}")
    else:
        print("All files processed successfully!")
    
    end_time = time.time()
    print(f"Processing completed in {end_time - start_time:.2f} seconds.")
    print(f"PNG images saved to: {output_folder} (with subdirectories preserved)")

if __name__ == "__main__":
    import argparse
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Process TEX files and convert them to PNG images.')
    parser.add_argument('input_folder', type=str, help='Input folder path containing .tex files')
    parser.add_argument('--output_folder', type=str, default=None, 
                        help='Output folder path for PNG images (default: same as input folder)')
    parser.add_argument('--cpus', type=int, default=8, help='Number of CPU cores to use (default: 8)')
    parser.add_argument('--dpi', type=int, default=300, help='Resolution in DPI for the output images (default: 300)')
    parser.add_argument('--timeout', type=int, default=60, help='Timeout per file in seconds (default: 60)')
    parser.add_argument('--log', type=str, default='skipped_files.txt', 
                        help='Log file name for skipped files (default: skipped_files.txt)')
    
    # Parse arguments
    args = parser.parse_args()
    
    process_all_tex_files(
        input_folder=args.input_folder,
        output_folder=args.output_folder,
        num_processes=args.cpus,
        timeout=args.timeout,
        dpi=args.dpi,
        log_file=args.log
    )