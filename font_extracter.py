import os
import zipfile
import shutil
from pathlib import Path

def extract_and_organize_fonts(input_folder, output_folder):
    # Create output directories
    header_folder = Path(output_folder) / "Header"
    paragraph_folder = Path(output_folder) / "Paragraph"
    header_folder.mkdir(parents=True, exist_ok=True)
    paragraph_folder.mkdir(parents=True, exist_ok=True)

    # Temporary directory for extraction
    temp_dir = Path(output_folder) / "temp"
    temp_dir.mkdir(exist_ok=True)

    # Find all zip files in input folder
    for zip_path in Path(input_folder).glob("*.zip"):
        # Extract zip file to temporary directory
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)

    # Find all .ttf files in temporary directory
    for ttf_file in temp_dir.rglob("*.ttf"):
        # Copy to Header folder
        shutil.copy2(ttf_file, header_folder / ttf_file.name)
        # Copy to Paragraph folder
        shutil.copy2(ttf_file, paragraph_folder / ttf_file.name)

    # Clean up temporary directory
    shutil.rmtree(temp_dir)

if __name__ == "__main__":
    # Define input and output directories
    input_dir = "english_fonts"
    output_dir = "english"

    # Verify input directory exists
    if not os.path.exists(input_dir):
        print(f"Error: Input folder '{input_dir}' does not exist.")
    else:
        extract_and_organize_fonts(input_dir, output_dir)
        print(f"TTF files have been extracted and organized into {output_dir}/Header and {output_dir}/Paragraph")