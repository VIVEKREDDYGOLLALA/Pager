import os
import glob
import shutil
from multiprocessing import Pool, cpu_count
from functools import partial

def sort_boxes_by_reading_order(bboxes):
    """
    Sort bounding boxes by reading order while keeping textlines grouped with their parent boxes.
    """
    # Group boxes by their box_id
    box_groups = {}
    
    for bbox in bboxes:
        if len(bbox) >= 4:
            box_id = bbox[2]
            if box_id not in box_groups:
                box_groups[box_id] = []
            box_groups[box_id].append(bbox)
    
    # For each box group, find the topmost-leftmost coordinates (reading order reference point)
    box_positions = []
    
    for box_id, group in box_groups.items():
        # Find the first box (topmost, then leftmost) in this group
        min_y = float('inf')
        min_x_for_min_y = float('inf')
        
        for bbox in group:
            coordinates = bbox[1]
            x, y = coordinates[0], coordinates[1]
            
            # Primary sort: by y-coordinate (top first)
            # Secondary sort: by x-coordinate (left first) for same y
            if y < min_y or (y == min_y and x < min_x_for_min_y):
                min_y = y
                min_x_for_min_y = x
        
        box_positions.append({
            'box_id': box_id,
            'reference_y': min_y,
            'reference_x': min_x_for_min_y,
            'group': group
        })
    
    # Sort box groups by reading order (top-to-bottom, left-to-right)
    box_positions.sort(key=lambda item: (item['reference_y'], item['reference_x']))
    
    # Build the final sorted list
    sorted_bboxes = []
    
    for box_pos in box_positions:
        group = box_pos['group']
        # Within each group, sort textlines by their position (top-to-bottom, left-to-right)
        group_sorted = sorted(group, key=lambda bbox: (bbox[1][1], bbox[1][0]))  # Sort by y, then x
        sorted_bboxes.extend(group_sorted)
    
    return sorted_bboxes


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
    """
    bboxes = []
    
    try:
        with open(bbox_file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                parsed_bbox = parse_bbox_line(line)
                if parsed_bbox:
                    bboxes.append(parsed_bbox)
                elif line.strip():  # Only warn for non-empty lines
                    print(f"Warning: Could not parse line {line_num} in {os.path.basename(bbox_file_path)}")
        
        return bboxes
        
    except Exception as e:
        print(f"Error reading {bbox_file_path}: {e}")
        return []


def write_sorted_bbox_file(sorted_bboxes, output_file_path):
    """
    Write sorted bounding boxes back to a file in the same format.
    """
    try:
        with open(output_file_path, 'w', encoding='utf-8') as f:
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
    """
    txt_file, backup = file_args
    filename = os.path.basename(txt_file)
    
    try:
        # Create backup if requested
        if backup:
            backup_file = txt_file + ".backup"
            shutil.copy2(txt_file, backup_file)
        
        # Read bounding boxes
        bboxes = read_bbox_file(txt_file)
        
        if not bboxes:
            return {
                "filename": filename,
                "status": "failed", 
                "reason": "no_valid_boxes",
                "original_count": 0,
                "sorted_count": 0
            }
        
        # Sort by reading order
        sorted_bboxes = sort_boxes_by_reading_order(bboxes)
        
        # Write sorted file back to original location
        success = write_sorted_bbox_file(sorted_bboxes, txt_file)
        
        if success:
            return {
                "filename": filename,
                "status": "success", 
                "original_count": len(bboxes),
                "sorted_count": len(sorted_bboxes),
                "backup_created": backup
            }
        else:
            return {
                "filename": filename,
                "status": "failed", 
                "reason": "write_error",
                "original_count": len(bboxes),
                "sorted_count": len(sorted_bboxes)
            }
            
    except Exception as e:
        return {
            "filename": filename,
            "status": "failed", 
            "reason": str(e),
            "original_count": 0,
            "sorted_count": 0
        }


def process_folder_bbox_files_parallel(input_folder, file_pattern="*.txt", backup=True, num_cores=None):
    """
    Process all bbox txt files in a folder using parallel processing.
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
    if backup:
        print("Backup files will be created with .backup extension")
    
    # Prepare arguments for parallel processing
    file_args = [(txt_file, backup) for txt_file in txt_files]
    
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
    
    print(f"✅ Successfully processed: {successful} files")
    print(f"❌ Failed to process: {failed} files")
    print(f"📦 Total bounding boxes processed: {total_boxes_processed}")
    
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
    parser = argparse.ArgumentParser(description='Sort bounding box files by reading order (parallel processing)')
    parser.add_argument('input_folder', help='Path to folder containing bbox txt files')
    parser.add_argument('--cores', '-c', type=int, default=None, 
                       help=f'Number of CPU cores to use (default: auto, max available: {cpu_count()})')
    parser.add_argument('--pattern', '-p', default='*.txt', help='File pattern to match (default: *.txt)')
    parser.add_argument('--no-backup', action='store_true', help='Do not create backup files before overwriting')
    
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
        num_cores=args.cores
    )
    
    # Exit with error code if any files failed
    failed_count = sum(1 for r in results.values() if r["status"] == "failed")
    if failed_count > 0:
        sys.exit(1)
    else:
        print(f"\n🎉 All files processed successfully!")