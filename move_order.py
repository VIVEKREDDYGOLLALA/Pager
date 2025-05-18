import os
import shutil
import argparse
from pathlib import Path
import re

def organize_files(orig_images_dir, output_base_dir, json_dir, max_depth=3):
    """
    Copy original images and JSON files to the corresponding output folders.
    Recursively searches for image folders up to max_depth.
    
    Args:
        orig_images_dir (str): Directory containing original images
        output_base_dir (str): Base directory containing output_folder_* directories
        json_dir (str): Directory containing JSON files
        max_depth (int): Maximum recursion depth for finding image folders
    """
    # Convert paths to Path objects
    orig_images_path = Path(orig_images_dir)
    json_path = Path(json_dir)
    output_base_path = Path(output_base_dir)
    
    print(f"Original images directory: {orig_images_path}")
    print(f"JSON directory: {json_path}")
    print(f"Output base directory: {output_base_path}")
    print(f"Maximum search depth: {max_depth}")
    
    # Check if directories exist
    if not orig_images_path.exists():
        print(f"ERROR: Original images directory {orig_images_path} does not exist!")
        return
    if not json_path.exists():
        print(f"ERROR: JSON directory {json_path} does not exist!")
        return
    if not output_base_path.exists():
        print(f"ERROR: Output base directory {output_base_path} does not exist!")
        return
    
    # Keep track of statistics
    total_processed = 0
    failed_matches = 0
    
    # Find all output folders
    output_folders = [d for d in output_base_path.glob("output_folder_*") if d.is_dir()]
    print(f"Found {len(output_folders)} output folders: {[f.name for f in output_folders]}")
    
    for output_folder in output_folders:
        # Extract language from folder name
        language = output_folder.name.replace("output_folder_", "")
        print(f"\nProcessing language: {language}")
        
        # Find all potential image folders recursively up to max_depth
        image_folders = []
        
        def find_image_folders(current_dir, current_depth=0):
            """Recursively find directories that might contain images"""
            if current_depth > max_depth:
                return
            
            # Check if current directory contains PNG files
            if list(current_dir.glob("*.png")):
                image_folders.append(current_dir)
                return
            
            # Continue recursion through subdirectories
            for subdir in current_dir.iterdir():
                if subdir.is_dir():
                    find_image_folders(subdir, current_depth + 1)
        
        # Start recursive search
        find_image_folders(output_folder)
        
        print(f"  Found {len(image_folders)} potential image folders")
        
        # Process each image folder
        for img_folder in image_folders:
            # Find PNG files in this folder
            png_files = list(img_folder.glob("*.png"))
            if not png_files:
                continue  # Skip folders with no PNG files
            
            # Use the PNG file name as the base for finding original and JSON
            synth_image = png_files[0]
            image_name = synth_image.stem  # Filename without extension
            
            # If the folder name pattern matches mg_hi_000775_0_5653893, extract mg_hi_000775_0
            folder_name = img_folder.name
            match = re.match(r'(.+?)_\d+$', folder_name)
            if match:
                # Use the folder name pattern if it exists
                image_name = match.group(1)
            
            # Find the corresponding original image
            orig_image_path = orig_images_path / f"{image_name}.png"
            if not orig_image_path.exists():
                print(f"  Original image not found: {orig_image_path} for folder {img_folder.name}")
                failed_matches += 1
                continue
            
            # Find the corresponding JSON file (format: language_image_name.json)
            json_file_path = json_path / f"{language}_{image_name}.json"
            if not json_file_path.exists():
                print(f"  JSON file not found: {json_file_path} for folder {img_folder.name}")
                failed_matches += 1
                continue
            
            # Copy original image to image folder
            dest_orig_image = img_folder / "original.png"
            try:
                shutil.copy2(orig_image_path, dest_orig_image)
            except Exception as e:
                print(f"  ERROR copying original image to {img_folder.name}: {e}")
                failed_matches += 1
                continue
            
            # Copy JSON file to image folder
            dest_json_file = img_folder / "annotations.json"
            try:
                shutil.copy2(json_file_path, dest_json_file)
            except Exception as e:
                print(f"  ERROR copying JSON file to {img_folder.name}: {e}")
                failed_matches += 1
                continue
            
            relative_path = img_folder.relative_to(output_base_path)
            print(f"  Processed: {relative_path}")
            total_processed += 1
            
            # Print progress every 100 items
            if total_processed % 100 == 0:
                print(f"Processed {total_processed} directories so far...")
    
    print("\nSummary:")
    print(f"Total directories processed: {total_processed}")
    print(f"Failed matches: {failed_matches}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Organize images and JSON files")
    parser.add_argument("--orig", required=True, help="Directory containing original images")
    parser.add_argument("--output", required=True, help="Base directory containing output_folder_* directories")
    parser.add_argument("--json", required=True, help="Directory containing JSON files")
    parser.add_argument("--max-depth", type=int, default=3, 
                        help="Maximum recursion depth for finding image folders (default: 3)")
    
    args = parser.parse_args()
    
    organize_files(args.orig, args.output, args.json, args.max_depth)