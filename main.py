import subprocess
import os
import argparse

# Base directory where your Python scripts are located
base_dir = "/home/vivek/Desktop/Pager"

scripts = [
    # "shoonya_extract.py",
    "coco_extract.py",
    "inpaint.py",
    # "overlaap_manage_shoonya.py",
    "normal__fill_shoonya.py",
    "extract_text_bbox.py",
    "clear_textlines.py",
    "textline_fill_shoonya.py",
    "tex_to_png.py"
]

def run_script(script_name, doc_type=None, num_docs=None, languages=None, text_file=None, output_folder=None, cpus=None, dpi=None, timeout=None, log_file=None):
    script_path = os.path.join(base_dir, script_name)
    if not os.path.isfile(script_path):
        print(f"Script not found: {script_path}")
        return False  # Return False if script is not found
    
    try:
        # Prepare the command based on the script
        if script_name == "coco_extract.py" and doc_type and num_docs is not None:
            # Run shoonya_extract.py with doc_type and num_docs
            command = ["python3", script_path, "--doc_type", doc_type, "--num_docs", str(num_docs)]
        elif script_name == "textline_fill_shoonya.py" and languages:
            # Run textline_fill_shoonya.py with languages and optional text-file
            command = ["python3", script_path, "--languages"] + languages.split()
            if text_file:
                command += ["--text-file", text_file]
        elif script_name == "tex_to_png.py" and output_folder and cpus is not None and dpi is not None and timeout is not None and log_file:
            # Run tex_to_png.py with all specified arguments
            command = [
                "python3", script_path, "Output_Tex_Files",
                "--output_folder", output_folder,
                "--cpus", str(cpus),
                "--dpi", str(dpi),
                "--timeout", str(timeout),
                "--log", log_file
            ]
        else:
            # Run other scripts without additional arguments
            command = ["python3", script_path]
        
        # Run the Python script and wait for it to complete
        subprocess.run(command, check=True)
        print(f"Successfully executed {script_name}")
        return True  # Return True if the script executed successfully

    except subprocess.CalledProcessError as e:
        print(f"Error while executing {script_name}: {e}")
        return False  # Return False if there was an error

if __name__ == "__main__":
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Run a series of Python scripts with specific arguments")
    parser.add_argument("--doc_type", type=str, required=True, help="Document type for shoonya_extract.py")
    parser.add_argument("--num_docs", type=int, required=True, help="Number of documents for shoonya_extract.py")
    parser.add_argument("--languages", type=str, required=True, help="Space-separated languages for textline_fill_shoonya.py (e.g., 'hindi urdu kashmiri')")
    parser.add_argument("--text_file", type=str, default=None, help="Text file for textline_fill_shoonya.py (e.g., 'text_file/hindi.txt'). If not provided, textline_fill_shoonya.py runs without --text-file.")
    parser.add_argument("--output_folder", type=str, required=True, help="Output folder for tex_to_png.py")
    parser.add_argument("--cpus", type=int, required=True, help="Number of CPUs for tex_to_png.py")
    parser.add_argument("--dpi", type=int, required=True, help="DPI for tex_to_png.py")
    parser.add_argument("--timeout", type=int, required=True, help="Timeout for tex_to_png.py")
    parser.add_argument("--log_file", type=str, required=True, help="Log file for tex_to_png.py")

    # Parse arguments
    args = parser.parse_args()
    
    for script in scripts:
        # Pass all arguments to run_script, which will use them for specific scripts
        success = run_script(
            script,
            doc_type=args.doc_type,
            num_docs=args.num_docs,
            languages=args.languages,
            text_file=args.text_file,
            output_folder=args.output_folder,
            cpus=args.cpus,
            dpi=args.dpi,
            timeout=args.timeout,
            log_file=args.log_file
        )
        if not success:
            print(f"Stopping further execution due to error in {script}.")
            break