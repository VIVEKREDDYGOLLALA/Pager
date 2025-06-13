#!/usr/bin/env python3
"""
Enhanced script to sort bounding boxes based on x,y coordinates for reading order.
Incorporates advanced sorting logic from the first script while handling bbox txt files.
Sorts by y-coordinate first (top to bottom), then by x-coordinate (left to right).
Handles image dimensions in first line of bbox files.
"""

import os
import glob
import shutil
import json
from multiprocessing import Pool, cpu_count
from functools import partial
from typing import List, Dict, Any, Tuple
from pathlib import Path


def extract_bbox_info(bbox_data: List, bbox_type: str = "bbox") -> Dict[str, Any]:
    """Extract bounding box information with metadata from bbox format."""
    if len(bbox_data) < 4:
        return None
    
    label, coords, box_id, image_id = bbox_data
    x, y, width, height = coords
    
    return {
        "id": box_id,
        "type": bbox_type,
        "bbox": [x, y, width, height],
        "x": x,
        "y": y,
        "width": width,
        "height": height,
        "text": label,
        "category_id": None,
        "image_id": image_id,
        "original_data": bbox_data
    }


def sort_bboxes_reading_order(bbox_list: List[Dict[str, Any]], 
                             y_tolerance: float = 10.0) -> List[Dict[str, Any]]:
    """
    Sort bounding boxes in reading order (top to bottom, left to right).
    
    Args:
        bbox_list: List of bbox info dictionaries
        y_tolerance: Tolerance for considering bboxes on the same line
    
    Returns:
        Sorted list of bbox info dictionaries
    """
    # Sort by y-coordinate first, then by x-coordinate
    return sorted(bbox_list, key=lambda box: (box["y"], box["x"]))


def detect_columns(bbox_list: List[Dict[str, Any]], 
                  min_column_width: float = 100.0) -> List[List[Dict[str, Any]]]:
    """
    Detect columns by analyzing x-coordinates and overlap of bounding boxes.
    
    Args:
        bbox_list: List of bbox info dictionaries
        min_column_width: Minimum width to consider as a separate column
        
    Returns:
        List of columns, each containing bboxes in that column
    """
    if not bbox_list:
        return []
    
    if len(bbox_list) == 1:
        return [bbox_list]
    
    # Sort by x-coordinate to analyze column structure
    sorted_by_x = sorted(bbox_list, key=lambda x: x["x"])
    
    columns = []
    
    for bbox in sorted_by_x:
        # Check if this bbox belongs to any existing column
        assigned_to_column = False
        
        for column in columns:
            # Check if bbox overlaps significantly with this column's x-range
            column_left = min(b["x"] for b in column)
            column_right = max(b["x"] + b["width"] for b in column)
            
            bbox_left = bbox["x"]
            bbox_right = bbox["x"] + bbox["width"]
            
            # Calculate overlap
            overlap_start = max(column_left, bbox_left)
            overlap_end = min(column_right, bbox_right)
            overlap_width = max(0, overlap_end - overlap_start)
            
            # If there's significant overlap (more than 50% of bbox width), it belongs to this column
            bbox_width = bbox["width"]
            if overlap_width > (bbox_width * 0.5):
                column.append(bbox)
                assigned_to_column = True
                break
        
        # If not assigned to any existing column, create a new column
        if not assigned_to_column:
            columns.append([bbox])
    
    # Filter out columns that are too narrow (likely noise)
    filtered_columns = []
    for column in columns:
        column_width = max(b["x"] + b["width"] for b in column) - min(b["x"] for b in column)
        if column_width >= min_column_width * 0.5 or len(column) > 1:  # Keep if wide enough or has multiple elements
            filtered_columns.append(column)
    
    return filtered_columns


def is_multicolumn_layout(bbox_list: List[Dict[str, Any]], 
                         min_column_width: float = 100.0) -> bool:
    """
    Detect if the layout has multiple columns.
    
    Args:
        bbox_list: List of bbox info dictionaries
        min_column_width: Minimum width to consider as a separate column
        
    Returns:
        True if multi-column layout detected, False otherwise
    """
    if len(bbox_list) < 2:
        return False
    
    columns = detect_columns(bbox_list, min_column_width)
    return len(columns) > 1


def sort_bboxes_column_aware(bbox_list: List[Dict[str, Any]], 
                           min_column_width: float = 100.0) -> List[Dict[str, Any]]:
    """
    Sort bounding boxes with proper column awareness.
    First handles global headers/elements, then processes columns.
    
    Args:
        bbox_list: List of bbox info dictionaries
        min_column_width: Minimum width to consider as separate column
        
    Returns:
        Sorted list respecting column layout
    """
    if not bbox_list:
        return []
    
    # Detect columns
    columns = detect_columns(bbox_list, min_column_width)
    
    if len(columns) <= 1:
        # Single column or no columns detected - just sort by y, then x
        return sorted(bbox_list, key=lambda x: (x["y"], x["x"]))
    
    # Find the top y-coordinate of the main column content
    column_top_ys = []
    for column in columns:
        if len(column) > 1:  # Only consider columns with multiple elements
            column_top_ys.extend([bbox["y"] for bbox in column])
    
    if column_top_ys:
        # Calculate threshold for global headers (elements significantly above main content)
        main_content_top = min(column_top_ys)
        header_threshold = main_content_top - 50  # Elements 50+ pixels above main content
        
        # Separate global headers from column content
        global_headers = []
        column_content = []
        
        for bbox in bbox_list:
            if bbox["y"] < header_threshold:
                global_headers.append(bbox)
            else:
                column_content.append(bbox)
        
        # Re-detect columns for the main content only
        if column_content:
            columns = detect_columns(column_content, min_column_width)
        else:
            columns = []
    else:
        global_headers = []
        columns = detect_columns(bbox_list, min_column_width)
    
    # Sort global headers by y-coordinate, then x-coordinate
    global_headers.sort(key=lambda x: (x["y"], x["x"]))
    
    # Sort each column by y-coordinate (top to bottom)
    sorted_columns = []
    for column in columns:
        sorted_column = sorted(column, key=lambda x: x["y"])
        sorted_columns.append(sorted_column)
    
    # Sort columns by their leftmost x-coordinate
    sorted_columns.sort(key=lambda col: min(bbox["x"] for bbox in col))
    
    # Combine: global headers first, then columns
    result = global_headers[:]
    for column in sorted_columns:
        result.extend(column)
    
    return result


def sort_bboxes_advanced_reading_order(bbox_list: List[Dict[str, Any]], 
                                     y_tolerance: float = 20.0) -> List[Dict[str, Any]]:
    """
    Advanced sorting that groups bboxes by approximate y-level (line) first,
    then sorts by x within each line.
    
    Args:
        bbox_list: List of bbox info dictionaries  
        y_tolerance: Tolerance for grouping bboxes on the same line
        
    Returns:
        Sorted list of bbox info dictionaries
    """
    if not bbox_list:
        return []
    
    # Group bboxes by approximate y-level (lines)
    lines = []
    for bbox in sorted(bbox_list, key=lambda x: x["y"]):
        # Find if this bbox belongs to an existing line
        added_to_line = False
        for line in lines:
            if abs(bbox["y"] - line[0]["y"]) <= y_tolerance:
                line.append(bbox)
                added_to_line = True
                break
        
        if not added_to_line:
            lines.append([bbox])
    
    # Sort each line by x-coordinate and flatten
    result = []
    for line in lines:
        line.sort(key=lambda x: x["x"])
        result.extend(line)
    
    return result


def sort_boxes_by_reading_order(bboxes, 
                               sorting_method="column_aware",
                               y_tolerance=20.0,
                               min_column_width=100.0):
    """
    Sort bounding boxes by reading order while keeping textlines grouped with their parent boxes.
    Enhanced with advanced sorting algorithms from the first script.
    
    Args:
        bboxes: List of bounding box data
        sorting_method: "simple", "advanced", or "column_aware"
        y_tolerance: Tolerance for line grouping in advanced sort
        min_column_width: Minimum column width for column detection
    """
    if not bboxes:
        return []
    
    # Convert bbox format to standardized format
    bbox_info_list = []
    for bbox in bboxes:
        bbox_info = extract_bbox_info(bbox)
        if bbox_info:
            bbox_info_list.append(bbox_info)
    
    if not bbox_info_list:
        return []
    
    # Choose sorting method
    if sorting_method == "column_aware":
        sorted_bbox_info = sort_bboxes_column_aware(bbox_info_list, min_column_width)
    elif sorting_method == "advanced":
        sorted_bbox_info = sort_bboxes_advanced_reading_order(bbox_info_list, y_tolerance)
    else:  # simple
        sorted_bbox_info = sort_bboxes_reading_order(bbox_info_list)
    
    # Convert back to original format
    return [bbox_info["original_data"] for bbox_info in sorted_bbox_info]


def parse_bbox_line(line):
    """
    Parse a single line from bbox file to extract bbox information.
    """
    try:
        line = line.strip()
        if not line or line.startswith('#'):
            return None
            
        # Remove outer brackets if present
        if line.startswith('[') and line.endswith(']'):
            line = line[1:-1]
        
        # Split by '] [' to separate the main components
        parts = []
        current_part = ""
        bracket_count = 0
        
        for char in line:
            if char == '[':
                bracket_count += 1
            elif char == ']':
                bracket_count -= 1
            
            current_part += char
            
            # If we're at bracket level 0 and hit a comma, we have a complete part
            if bracket_count == 0 and char == ',':
                current_part = current_part[:-1].strip()  # Remove trailing comma
                if current_part:
                    parts.append(current_part)
                current_part = ""
        
        # Add the last part
        if current_part.strip():
            parts.append(current_part.strip())
        
        if len(parts) >= 4:
            # Parse each component
            label = parts[0].strip().strip('"\'')
            
            # Parse coordinates [x, y, width, height]
            coord_str = parts[1].strip()
            if coord_str.startswith('[') and coord_str.endswith(']'):
                coord_str = coord_str[1:-1]
            coords = [float(x.strip()) for x in coord_str.split(',')]
            
            box_id = parts[2].strip().strip('"\'')
            image_id = parts[3].strip().strip('"\'')
            
            # Try to convert image_id to int if it's numeric
            try:
                image_id = int(image_id)
            except ValueError:
                pass  # Keep as string if not numeric
            
            return [label, coords, box_id, image_id]
            
    except Exception as e:
        print(f"Error parsing line: {line[:50]}... Error: {e}")
        return None
    
    return None


def read_bbox_file(bbox_file_path):
    """
    Read bounding box file and parse all bbox entries.
    First line contains image dimensions and is preserved as-is.
    """
    image_dimensions = None
    bboxes = []
    
    try:
        with open(bbox_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
            if not lines:
                return image_dimensions, bboxes
            
            # First line is image dimensions - preserve as-is
            image_dimensions = lines[0].strip()
            
            # Process remaining lines as bboxes
            for line_num, line in enumerate(lines[1:], 2):  # Start from line 2
                parsed_bbox = parse_bbox_line(line)
                if parsed_bbox:
                    bboxes.append(parsed_bbox)
                elif line.strip():  # Only warn for non-empty lines
                    print(f"Warning: Could not parse line {line_num} in {os.path.basename(bbox_file_path)}")
        
        return image_dimensions, bboxes
        
    except Exception as e:
        print(f"Error reading {bbox_file_path}: {e}")
        return None, []


def write_sorted_bbox_file(image_dimensions, sorted_bboxes, output_file_path):
    """
    Write sorted bounding boxes back to a file in the same format.
    Preserves image dimensions as first line.
    """
    try:
        with open(output_file_path, 'w', encoding='utf-8') as f:
            # Write image dimensions as first line
            if image_dimensions:
                f.write(image_dimensions + '\n')
            
            # Write sorted bboxes
            for bbox in sorted_bboxes:
                label, coords, box_id, image_id = bbox
                # Format coordinates as [x, y, width, height]
                coord_str = f"[{coords[0]}, {coords[1]}, {coords[2]}, {coords[3]}]"
                # Write in original format
                line = f"[{label}, {coord_str}, {box_id}, {image_id}]\n"
                f.write(line)
        
        return True
        
    except Exception as e:
        print(f"Error writing {output_file_path}: {e}")
        return False


def process_single_file(file_args):
    """
    Process a single bbox file. Used for parallel processing.
    Enhanced with advanced sorting methods.
    """
    txt_file, backup, sorting_method, y_tolerance, min_column_width, auto_detect = file_args
    filename = os.path.basename(txt_file)
    
    try:
        # Create backup if requested
        if backup:
            backup_file = txt_file + ".backup"
            shutil.copy2(txt_file, backup_file)
        
        # Read bounding boxes (first line is image dimensions)
        image_dimensions, bboxes = read_bbox_file(txt_file)
        
        if not bboxes:
            return {
                "filename": filename,
                "status": "failed", 
                "reason": "no_valid_boxes",
                "original_count": 0,
                "sorted_count": 0,
                "sorting_method": sorting_method
            }
        
        # Auto-detect layout if enabled
        final_sorting_method = sorting_method
        if auto_detect and sorting_method == "auto":
            # Convert to bbox info format for detection
            bbox_info_list = []
            for bbox in bboxes:
                bbox_info = extract_bbox_info(bbox)
                if bbox_info:
                    bbox_info_list.append(bbox_info)
            
            if is_multicolumn_layout(bbox_info_list, min_column_width):
                final_sorting_method = "column_aware"
                print(f"🔍 Multi-column layout detected in {filename} - using column-aware sorting")
            else:
                final_sorting_method = "column_aware"  # Use as default
                print(f"📄 Single column layout detected in {filename} - using column-aware sorting")
        
        # Sort by reading order using enhanced algorithms
        sorted_bboxes = sort_boxes_by_reading_order(
            bboxes, 
            sorting_method=final_sorting_method,
            y_tolerance=y_tolerance,
            min_column_width=min_column_width
        )
        
        # Write sorted file back to original location
        success = write_sorted_bbox_file(image_dimensions, sorted_bboxes, txt_file)
        
        if success:
            return {
                "filename": filename,
                "status": "success", 
                "original_count": len(bboxes),
                "sorted_count": len(sorted_bboxes),
                "backup_created": backup,
                "sorting_method": final_sorting_method
            }
        else:
            return {
                "filename": filename,
                "status": "failed", 
                "reason": "write_error",
                "original_count": len(bboxes),
                "sorted_count": len(sorted_bboxes),
                "sorting_method": final_sorting_method
            }
            
    except Exception as e:
        return {
            "filename": filename,
            "status": "failed", 
            "reason": str(e),
            "original_count": 0,
            "sorted_count": 0,
            "sorting_method": sorting_method
        }


def process_folder_bbox_files_parallel(input_folder, 
                                     file_pattern="*.txt", 
                                     backup=True, 
                                     num_cores=None,
                                     sorting_method="auto",
                                     y_tolerance=20.0,
                                     min_column_width=100.0,
                                     auto_detect=True):
    """
    Process all bbox txt files in a folder using parallel processing.
    Enhanced with advanced sorting algorithms.
    """
    
    # Find all txt files in input folder
    search_pattern = os.path.join(input_folder, file_pattern)
    txt_files = glob.glob(search_pattern)
    
    if not txt_files:
        print(f"No files found matching pattern {search_pattern}")
        return {}
    
    # Determine number of cores to use
    max_cores = cpu_count()
    if num_cores is None:
        cores_to_use = min(max_cores, len(txt_files))  # Don't use more cores than files
    else:
        cores_to_use = min(num_cores, max_cores, len(txt_files))
    
    print(f"Found {len(txt_files)} files to process")
    print(f"Using {cores_to_use} CPU cores out of {max_cores} available")
    print(f"Input folder: {input_folder}")
    print(f"Sorting method: {sorting_method}")
    if auto_detect:
        print("Auto-detection of multi-column layouts: enabled")
    if backup:
        print("Backup files will be created with .backup extension")
    
    # Prepare arguments for parallel processing
    file_args = [(txt_file, backup, sorting_method, y_tolerance, min_column_width, auto_detect) 
                 for txt_file in txt_files]
    
    # Process files in parallel
    print(f"\nProcessing {len(txt_files)} files in parallel...")
    
    with Pool(processes=cores_to_use) as pool:
        results = pool.map(process_single_file, file_args)
    
    # Convert results to dictionary
    results_dict = {result["filename"]: result for result in results}
    
    # Print summary
    print(f"\n{'='*60}")
    print("PROCESSING SUMMARY")
    print(f"{'='*60}")
    successful = sum(1 for r in results if r["status"] == "success")
    failed = len(results) - successful
    total_boxes_processed = sum(r["sorted_count"] for r in results if r["status"] == "success")
    
    # Count sorting methods used
    method_counts = {}
    for result in results:
        if result["status"] == "success" and "sorting_method" in result:
            method = result["sorting_method"]
            method_counts[method] = method_counts.get(method, 0) + 1
    
    print(f"✅ Successfully processed: {successful} files")
    print(f"❌ Failed to process: {failed} files")
    print(f"📦 Total bounding boxes processed: {total_boxes_processed}")
    
    if method_counts:
        print("\n📊 Sorting methods used:")
        for method, count in method_counts.items():
            print(f"  - {method}: {count} files")
    
    if backup and successful > 0:
        print(f"💾 Backup files created: {successful} (.backup extension)")
    
    if failed > 0:
        print("\nFailed files:")
        for result in results:
            if result["status"] == "failed":
                print(f"  - {result['filename']}: {result['reason']}")
    
    return results_dict


if __name__ == "__main__":
    import argparse
    import sys
    
    # Command line interface
    parser = argparse.ArgumentParser(description='Enhanced bbox sorting with advanced algorithms (parallel processing)')
    parser.add_argument('input_folder', help='Path to folder containing bbox txt files')
    parser.add_argument('--cores', '-c', type=int, default=None, 
                       help=f'Number of CPU cores to use (default: auto, max available: {cpu_count()})')
    parser.add_argument('--pattern', '-p', default='*.txt', help='File pattern to match (default: *.txt)')
    parser.add_argument('--no-backup', action='store_true', help='Do not create backup files before overwriting')
    parser.add_argument('--sorting-method', choices=['simple', 'advanced', 'column_aware', 'auto'], 
                       default='auto', help='Sorting method to use (default: auto)')
    parser.add_argument('--y-tolerance', type=float, default=20.0,
                       help='Y-coordinate tolerance for line grouping (default: 20.0)')
    parser.add_argument('--min-column-width', type=float, default=100.0,
                       help='Minimum column width for column detection (default: 100.0)')
    parser.add_argument('--no-auto-detect', action='store_true',
                       help='Disable automatic multi-column detection')
    
    args = parser.parse_args()
    
    # Validate input folder
    if not os.path.exists(args.input_folder):
        print(f"Error: Input folder '{args.input_folder}' does not exist")
        sys.exit(1)
    
    # Validate cores argument
    max_cores = cpu_count()
    if args.cores is not None:
        if args.cores < 1:
            print(f"Error: Number of cores must be at least 1")
            sys.exit(1)
        elif args.cores > max_cores:
            print(f"Warning: Requested {args.cores} cores, but only {max_cores} available. Using {max_cores}.")
            args.cores = max_cores
    
    # Process folder
    results = process_folder_bbox_files_parallel(
        input_folder=args.input_folder,
        file_pattern=args.pattern,
        backup=not args.no_backup,
        num_cores=args.cores,
        sorting_method=args.sorting_method,
        y_tolerance=args.y_tolerance,
        min_column_width=args.min_column_width,
        auto_detect=not args.no_auto_detect
    )
    
    # Exit with error code if any files failed
    failed_count = sum(1 for r in results.values() if r["status"] == "failed")
    if failed_count > 0:
        sys.exit(1)
    else:
        print(f"\n🎉 All files processed successfully!")


"""
How to run it:
python enhanced_bbox_sorter.py "path/to/folder/"

Options:
--sorting-method simple|advanced|column_aware|auto (default: auto)
--y-tolerance 20.0 (for line grouping)
--min-column-width 100.0 (for column detection)
--no-auto-detect (disable automatic layout detection)
--cores 4 (number of CPU cores to use)
--no-backup (don't create backup files)

The script now:
1. Preserves image dimensions in the first line
2. Applies advanced sorting algorithms from the first code
3. Auto-detects multi-column layouts
4. Handles column-aware sorting
5. Supports parallel processing
6. Creates backups before modifying files
"""