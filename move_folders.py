import os
import shutil
import argparse
import random
from pathlib import Path

def randomly_select_folders(base_dir, output_dir, num_to_keep=10, dry_run=False):
    """
    Randomly select num_to_keep folders from each language directory and move the rest.
    
    Args:
        base_dir (str): Base directory containing output_folder_* directories
        output_dir (str): Directory to move unselected folders to
        num_to_keep (int): Number of folders to randomly select and keep
        dry_run (bool): If True, only print what would be done without actually moving
    """
    base_path = Path(base_dir)
    output_path = Path(output_dir)
    
    # Create output directory if it doesn't exist and this is not a dry run
    if not dry_run:
        output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"Base directory: {base_path}")
    print(f"Output directory: {output_path}")
    print(f"Number of folders to keep per language: {num_to_keep}")
    print(f"Dry run: {dry_run}")
    
    # Statistics
    total_kept = 0
    total_moved = 0
    
    # Get all language folders
    for lang_folder in base_path.glob("output_folder_*"):
        if not lang_folder.is_dir():
            continue
            
        print(f"\nProcessing language folder: {lang_folder.name}")
        
        # Find all the leaf folders (those that don't contain other folders)
        leaf_folders = []
        
        # Recursive function to find leaf folders
        def find_leaf_folders(folder):
            # Check if this folder contains any subdirectories
            has_subdirs = False
            for item in folder.iterdir():
                if item.is_dir():
                    has_subdirs = True
                    find_leaf_folders(item)
            
            # If no subdirectories, this is a leaf folder
            if not has_subdirs:
                leaf_folders.append(folder)
        
        # Start recursion
        find_leaf_folders(lang_folder)
        
        print(f"  Found {len(leaf_folders)} leaf folders")
        
        # Randomly select folders to keep
        folders_to_keep = []
        if len(leaf_folders) <= num_to_keep:
            # Keep all folders if there are fewer than or equal to num_to_keep
            folders_to_keep = leaf_folders
            print(f"  Keeping all {len(folders_to_keep)} folders (fewer than {num_to_keep})")
        else:
            # Randomly select num_to_keep folders
            folders_to_keep = random.sample(leaf_folders, num_to_keep)
            print(f"  Randomly selected {len(folders_to_keep)} folders to keep")
        
        # Move the rest of the folders
        folders_to_move = [f for f in leaf_folders if f not in folders_to_keep]
        print(f"  Moving {len(folders_to_move)} folders")
        
        # Keep track of stats
        total_kept += len(folders_to_keep)
        total_moved += len(folders_to_move)
        
        # Move folders not selected to keep
        for folder in folders_to_move:
            # Determine relative path to preserve structure
            rel_path = folder.relative_to(base_path)
            dest_path = output_path / rel_path
            
            if not dry_run:
                # Create parent directories if they don't exist
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                
                try:
                    # Move the folder to the destination
                    shutil.move(str(folder), str(dest_path))
                    print(f"  Moved: {rel_path}")
                except Exception as e:
                    print(f"  ERROR moving {folder}: {e}")
            else:
                print(f"  Would move: {rel_path} (dry run)")
    
    print("\nSummary:")
    print(f"Total folders kept: {total_kept}")
    print(f"Total folders {'would be ' if dry_run else ''}moved: {total_moved}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Randomly select folders to keep and move the rest")
    parser.add_argument("--base", required=True, help="Base directory containing output_folder_* directories")
    parser.add_argument("--output", required=True, help="Output directory for moved folders")
    parser.add_argument("--keep", type=int, default=10, help="Number of folders to randomly keep per language (default: 10)")
    parser.add_argument("--dry-run", action="store_true", help="Dry run: don't actually move files, just print what would be done")
    parser.add_argument("--seed", type=int, help="Random seed for reproducibility")
    
    args = parser.parse_args()
    
    # Set random seed if provided
    if args.seed is not None:
        random.seed(args.seed)
        print(f"Using random seed: {args.seed}")
    
    randomly_select_folders(args.base, args.output, args.keep, args.dry_run)