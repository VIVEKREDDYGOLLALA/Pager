import subprocess
import os
import argparse
from multiprocessing import cpu_count

# Base directory where your Python scripts are located
base_dir = "/root/Pager"

scripts = [
    "shoonya_extract.py",# remove duplicates
    "inpaint.py", 
    "overlaap_manage_shoonya.py",
    # "reading_order.py"
    "normal__fill_shoonya.py",
    "text_fill.py",
    "tex_to_png.py"
]

def run_script(script_name, args):
    """Run a script with appropriate arguments based on the script type."""
    script_path = os.path.join(base_dir, script_name)
    if not os.path.isfile(script_path):
        print(f"Script not found: {script_path}")
        return False
    
    try:
        # Build command based on script requirements
        command = ["python3", script_path]
        
        if script_name == "shoonya_extract.py":
            # shoonya_extract.py arguments
            command.extend(["--doc_types"] + args.doc_types)
            command.extend([
                "--num_docs", str(args.num_docs),
                "--num_cores", str(args.cpus)
            ])
            command.extend(["--image_patterns"] + args.image_patterns)
            
        elif script_name == "inpaint.py":
            # inpaint.py arguments
            command.extend([
                "--cpus", str(args.cpus)
            ])
            
        elif script_name == "overlaap_manage_shoonya.py":
            # No specific arguments mentioned in comments, runs without additional args
            pass
            
        elif script_name == "normal__fill_shoonya.py":
            # normal__fill_shoonya.py arguments
            command.extend([
                "--cpus", str(args.cpus),
                "--bbox-dir", args.bbox_dir,
                "--image-dir", args.image_dir,
                "--hindi-text-file", args.hindi_text_file,
                "--chunk-size", str(args.chunk_size),
                "--font-path", args.font_path
            ])
            
        elif script_name == "extract_text_bbox.py":
            # No specific arguments mentioned in comments, runs without additional args
            pass
            
        elif script_name == "text_fill.py":
            # textline_fill_shoonya.py arguments
            command.extend(["--languages"] + args.languages)
            if args.text_file:
                command.extend(["--text-file", args.text_file])
            command.extend(["--input-text-folder", args.input_text_folder])
            if args.file_count:
                command.extend(["--file-count", str(args.file_count)])
                
        elif script_name == "tex_to_png.py":
            # tex_to_png.py arguments - input_folder is a positional argument
            command.append(args.input_folder)  # Positional argument
            if args.output_folder:
                command.extend(["--output_folder", args.output_folder])
            command.extend([
                "--cpus", str(args.cpus),
                "--dpi", str(args.dpi),
                "--timeout", str(args.timeout),
                "--log", args.log_file
            ])
        
        print(f"Running: {' '.join(command)}")
        
        # Run the Python script and wait for it to complete
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"✅ Successfully executed {script_name}")
        if result.stdout:
            print(f"Output: {result.stdout}")
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Error while executing {script_name}: {e}")
        if e.stderr:
            print(f"Error details: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error while executing {script_name}: {e}")
        return False

def validate_paths(args):
    """Validate that required paths exist. Only check paths that must exist at startup."""
    
    # # Check base directory (must exist)
    # if not os.path.exists(base_dir):
    #     print(f"❌ Base directory does not exist: {base_dir}")
    #     return False
    
    # # Check font path (must exist if specified)
    # if hasattr(args, 'font_path') and args.font_path and not os.path.exists(args.font_path):
    #     print(f"❌ Font file does not exist: {args.font_path}")
    #     return False
    
    # # Check hindi text file (must exist if specified and not default)
    # if (hasattr(args, 'hindi_text_file') and args.hindi_text_file and 
    #     args.hindi_text_file != "1M_seed/input_1/assamese.txt" and  # Skip default path
    #     not os.path.exists(args.hindi_text_file)):
    #     print(f"❌ Hindi text file does not exist: {args.hindi_text_file}")
    #     return False
    
    # # Check text-file for textline_fill_shoonya.py (only if explicitly provided)
    # if hasattr(args, 'text_file') and args.text_file and not os.path.exists(args.text_file):
    #     print(f"❌ Text file does not exist: {args.text_file}")
    #     return False
    
    # Note: We don't validate bbox_dir, image_dir, input_folder, or output_folder
    # because these might be created by earlier scripts in the pipeline
    
    print("✅ Initial path validation passed")
    return True

if __name__ == "__main__":
    # Set up argument parsing
    parser = argparse.ArgumentParser(
        description="Run a series of Python scripts with unified CPU argument",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Script execution order:
1. shoonya_extract.py - Extract data with specified doc types and counts
2. inpaint.py - Text removal inpainting  
3. overlaap_manage_shoonya.py - Manage overlaps
4. normal__fill_shoonya.py - Fill processing with BBOX and images
5. extract_text_bbox.py - Extract text from bounding boxes
6. textline_fill_shoonya.py - Fill textlines with specified languages
7. tex_to_png.py - Convert TEX files to PNG images

Example usage:
python script_runner.py --cpus 8 --doc_types magazines newspapers --num_docs 100 
--languages urdu kashmiri hindi --bbox-dir "/path/to/bbox" --image-dir "/path/to/images" 
--output_folder "/path/to/output" --dpi 300 --timeout 60
        """
    )
    
    # Unified CPU argument
    parser.add_argument(
        "--cpus", 
        type=int, 
        default=cpu_count(),
        help=f"Number of CPU cores to use for all scripts (default: {cpu_count()}, all available cores)"
    )
    
    # Arguments for shoonya_extract.py
    parser.add_argument(
        "--doc_types",
        nargs='+',
        default=["magazines", "newspapers"],
        help="List of document types (subfolder names, e.g., magazines newspapers)"
    )
    parser.add_argument(
        "--num_docs",
        type=int,
        default=50,
        help="Number of documents to process per document type"
    )
    parser.add_argument(
        "--image_patterns",
        nargs='*',
        default=["all"],
        help="Image patterns to process. Options: 'all', 'normal', '_0', '_1', '_2', etc."
    )
    
    # Arguments for normal__fill_shoonya.py
    parser.add_argument(
        '--bbox-dir',
        type=str,
        required=True,
        help='Directory containing BBOX text files (will be created by earlier scripts if not exists)'
    )
    parser.add_argument(
        '--image-dir',
        type=str,
        required=True,
        help='Directory containing corresponding image files (will be created by earlier scripts if not exists)'
    )
    parser.add_argument(
        '--hindi-text-file',
        type=str,
        default="1M_seed/input_1/assamese.txt",
        help='Path to the Hindi/Assamese text file'
    )
    parser.add_argument(
        '--chunk-size',
        type=int,
        default=1,
        help='Number of files to process per worker at a time'
    )
    parser.add_argument(
        '--font-path',
        type=str,
        default="fonts/bengali/Header/Atma-Bold.ttf",
        help='Path to the font file to use for text rendering'
    )
    
    # Arguments for text_fill.py
    parser.add_argument(
        "--languages", 
        nargs='+',
        default=['urdu', 'kashmiri'],
        help="List of languages to process for textline_fill_shoonya.py (e.g., urdu kashmiri hindi)"
    )
    parser.add_argument(
        "--text-file", 
        type=str, 
        default=None, 
        help="Path to the text file containing input text. If not provided, defaults to input_text_folder/input_1/{language}.txt"
    )
    parser.add_argument(
        "--input-text-folder",
        type=str,
        default='1M_seed',
        help='Path to the folder containing input text subfolders (input_1, input_2). Default: 1M_texts'
    )
    parser.add_argument(
        "--file-count",
        type=int,
        default=None,
        help='Number of files to generate for each language. If not provided, processes all available files.'
    )
    
    # Arguments for tex_to_png.py
    parser.add_argument(
        'input_folder',
        type=str,
        default="Output_Tex_Files",
        nargs='?',  # Makes it optional with default
        help='Input folder path containing .tex files (default: Output_Tex_Files)'
    )
    parser.add_argument(
        "--output_folder", 
        type=str, 
        default=None,
        help="Output folder for tex_to_png.py (default: same as input folder if not specified)"
    )
    parser.add_argument(
        "--dpi", 
        type=int, 
        default=300, 
        help="Resolution in DPI for the output images"
    )
    parser.add_argument(
        "--timeout", 
        type=int, 
        default=60, 
        help="Timeout per file in seconds"
    )
    parser.add_argument(
        "--log_file", 
        type=str, 
        default="skipped_files.txt", 
        help="Log file name for skipped files (default: skipped_files.txt)"
    )
    
    # Additional options
    parser.add_argument(
        "--skip-scripts",
        nargs='*',
        default=[],
        help="Scripts to skip (e.g., --skip-scripts inpaint.py extract_text_bbox.py)"
    )
    parser.add_argument(
        "--dry-run",
        action='store_true',
        help="Show what commands would be run without executing them"
    )

    # Parse arguments
    args = parser.parse_args()
    
    # Validate CPU count
    max_cpus = cpu_count()
    if args.cpus > max_cpus:
        print(f"⚠️  Warning: Requested {args.cpus} CPUs, but only {max_cpus} available. Using {max_cpus}.")
        args.cpus = max_cpus
    elif args.cpus < 1:
        print(f"⚠️  Warning: Invalid CPU count {args.cpus}. Using 1.")
        args.cpus = 1
    
    # Validate paths
    if not validate_paths(args):
        print("❌ Path validation failed. Please check the paths and try again.")
        exit(1)
    
    # Show configuration
    print("=" * 60)
    print("SCRIPT EXECUTION CONFIGURATION")
    print("=" * 60)
    print(f"📁 Base directory: {base_dir}")
    print(f"🖥️  CPU cores: {args.cpus}")
    print(f"📄 Document types: {args.doc_types}")
    print(f"📊 Documents per type: {args.num_docs}")
    print(f"🗣️  Languages: {args.languages}")
    print(f"📁 Input text folder: {args.input_text_folder}")
    if args.file_count:
        print(f"📊 File count per language: {args.file_count}")
    print(f"📂 BBOX directory: {args.bbox_dir}")
    print(f"🖼️  Image directory: {args.image_dir}")
    print(f"📤 Output folder: {args.output_folder}")
    
    if args.skip_scripts:
        print(f"⏭️  Skipping scripts: {args.skip_scripts}")
    
    if args.dry_run:
        print("\n🔍 DRY RUN MODE - Commands will be shown but not executed")
    
    print("=" * 60)
    
    # Filter out skipped scripts
    scripts_to_run = [script for script in scripts if script not in args.skip_scripts]
    
    success_count = 0
    total_scripts = len(scripts_to_run)
    
    print(f"\n🚀 Starting execution of {total_scripts} scripts...")
    
    for i, script in enumerate(scripts_to_run, 1):
        print(f"\n[{i}/{total_scripts}] Processing: {script}")
        print("-" * 40)
        
        if args.dry_run:
            print(f"Would execute: {script}")
            success_count += 1
            continue
            
        success = run_script(script, args)
        if success:
            success_count += 1
        else:
            print(f"❌ Stopping execution due to error in {script}")
            break
    
    # Final summary
    print("\n" + "=" * 60)
    print("EXECUTION SUMMARY")
    print("=" * 60)
    print(f"✅ Successfully executed: {success_count}/{total_scripts} scripts")
    
    if success_count == total_scripts:
        print("🎉 All scripts completed successfully!")
        exit(0)
    else:
        failed_count = total_scripts - success_count
        print(f"❌ Failed scripts: {failed_count}")
        exit(1)