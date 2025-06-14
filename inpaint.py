import os
import cv2
import numpy as np
import re
from tqdm import tqdm
import glob
from multiprocessing import Pool
from functools import partial
import argparse

def read_bbox_file(bbox_path):
    bbox_data = []
    try:
        with open(bbox_path, 'r') as f:
            lines = f.readlines()
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if this is a dimensions line (first line with width, height)
            if line.startswith('[') and line.endswith(']') and ',' in line:
                try:
                    # Try to parse as dimensions first
                    values = line.strip('[]').split(',')
                    if len(values) == 2:  # Only width and height
                        width = int(values[0])
                        height = int(values[1])
                        bbox_data.append(['dimensions', [width, height]])
                        continue
                except:
                    pass  # If it fails, treat as regular bbox line
            
            # Parse regular bbox lines
            match = re.match(r'\[(.*?), \[(.*?)\], (.*?), (.*?)\]', line)
            if match:
                bbox_type = match.group(1).strip().strip('"')  # Remove quotes if present
                coords_str = match.group(2)
                id1 = match.group(3).strip()
                id2 = match.group(4).strip()
                coords = [float(x.strip()) for x in coords_str.split(',')]
                if len(coords) >= 4:
                    x, y, width, height = coords[:4]
                    bbox_data.append([bbox_type, [x, y, width, height], id1, id2])
    except Exception as e:
        print(f"Error reading file {bbox_path}: {e}")
    return bbox_data

def find_matching_bbox_file(image_basename, bboxes_dir):
    if not os.path.exists(bboxes_dir):
        print(f"Error: Bounding box directory {bboxes_dir} does not exist")
        return None
    bbox_files = [f for f in os.listdir(bboxes_dir) if f.endswith('.txt')]
    exact_matches = [os.path.join(bboxes_dir, f) for f in bbox_files if f.startswith(f"{image_basename}_")]
    if exact_matches:
        if len(exact_matches) > 1:
            print(f"Multiple bbox files found for {image_basename}, using: {os.path.basename(exact_matches[0])}")
        return exact_matches[0]
    exact_file = os.path.join(bboxes_dir, f"{image_basename}.txt")
    if os.path.exists(exact_file):
        return exact_file
    contained_matches = [os.path.join(bboxes_dir, f) for f in bbox_files if image_basename in f]
    if contained_matches:
        if len(contained_matches) > 1:
            print(f"Multiple partial matches found for {image_basename}, using: {os.path.basename(contained_matches[0])}")
        return contained_matches[0]
    print(f"No matching bbox file found for {image_basename}")
    return None

def inpaint_from_bboxes(image_path, bbox_data, output_dir, shrink_pixels=2):
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Could not read image {image_path}")
        return False
    image_filename = os.path.basename(image_path)
    inpainted_path = os.path.join(output_dir, image_filename)
    combined_mask_path = os.path.join(output_dir, "masks", f"{os.path.splitext(image_filename)[0]}_mask.png")
    os.makedirs(os.path.join(output_dir, "masks"), exist_ok=True)
    img_height, img_width = image.shape[:2]
    combined_mask = np.zeros((img_height, img_width), dtype=np.uint8)
    result = image.copy()
    processed_boxes = 0
    skipped_boxes = 0
    
    for box in bbox_data:
        if box[0] == 'dimensions':
            continue
        box_type = box[0].lower()
        
        # Updated skip_types - removed 'figure' and made more specific
        # Now only skips specific types, not anything containing 'figure'
        skip_types = ['header', 'footer', 'figure_1', 'formula', 'formula_1', 'table']
        
        # Check for exact matches in skip_types, not partial matches
        if box_type in skip_types:
            skipped_boxes += 1
            print(f"Skipping box type: {box_type}")
            continue
        
        # Additional check for 'figure' but allow 'figure-caption', 'caption', etc.
        if box_type == 'figure':  # Only skip exact 'figure', not 'figure-caption'
            skipped_boxes += 1
            print(f"Skipping box type: {box_type}")
            continue
            
        x, y, width, height = [int(float(coord)) for coord in box[1]]
        x = max(0, min(x, img_width - 1))
        y = max(0, min(y, img_height - 1))
        w = min(width, img_width - x)
        h = min(height, img_height - y)
        
        if w <= 0 or h <= 0:
            skipped_boxes += 1
            continue
        
        # Shrink the bounding box by shrink_pixels on all sides
        x_shrunk = x + shrink_pixels
        y_shrunk = y + shrink_pixels
        w_shrunk = w - (2 * shrink_pixels)
        h_shrunk = h - (2 * shrink_pixels)
        
        # Ensure the shrunk box is valid
        if w_shrunk <= 0 or h_shrunk <= 0:
            skipped_boxes += 1
            continue
        
        # Adjust coordinates to stay within image bounds
        x_shrunk = max(0, min(x_shrunk, img_width - 1))
        y_shrunk = max(0, min(y_shrunk, img_height - 1))
        w_shrunk = min(w_shrunk, img_width - x_shrunk)
        h_shrunk = min(h_shrunk, img_height - y_shrunk)
        
        if w_shrunk <= 0 or h_shrunk <= 0:
            skipped_boxes += 1
            continue
        
        cv2.rectangle(combined_mask, (x_shrunk, y_shrunk), (x_shrunk + w_shrunk, y_shrunk + h_shrunk), 255, -1)
        processed_boxes += 1
        print(f"Processing box type: {box[0]} at ({x_shrunk}, {y_shrunk}, {w_shrunk}, {h_shrunk})")
    
    if processed_boxes == 0:
        print(f"No valid boxes to inpaint for {image_filename}")
        return False
    
    try:
        inpainted = cv2.inpaint(result, combined_mask, inpaintRadius=7, flags=cv2.INPAINT_TELEA)
        cv2.imwrite(combined_mask_path, combined_mask)
        cv2.imwrite(inpainted_path, inpainted)
        print(f"Processed image {image_filename}: {processed_boxes} boxes inpainted, {skipped_boxes} boxes skipped")
        return True
    except Exception as e:
        print(f"Error inpainting {image_filename}: {e}")
        return False

def process_image(image_path, bboxes_dir, output_dir, shrink_pixels=2):
    image_basename = os.path.splitext(os.path.basename(image_path))[0]
    bbox_path = find_matching_bbox_file(image_basename, bboxes_dir)
    if bbox_path is None:
        print(f"Skipping {image_basename}: No matching bbox file found")
        return False
    bbox_data = read_bbox_file(bbox_path)
    if not bbox_data:
        print(f"Skipping {image_basename}: No valid bbox data")
        return False
    return inpaint_from_bboxes(image_path, bbox_data, output_dir, shrink_pixels)

def process_all_images(images_dir, bboxes_dir, output_dir, shrink_pixels=2, num_cpus=None):
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, "masks"), exist_ok=True)
    image_extensions = ['.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp']
    all_image_files = []
    for ext in image_extensions:
        all_image_files.extend(glob.glob(os.path.join(images_dir, f"*{ext}")))
        all_image_files.extend(glob.glob(os.path.join(images_dir, f"*{ext.upper()}")))
    all_image_files = list(set(all_image_files))
    print(f"Found {len(all_image_files)} images to process")
    
    # Use multiprocessing Pool for parallel processing
    successful = 0
    failed = 0
    with Pool(processes=num_cpus) as pool:
        # Partial function to pass additional arguments to process_image
        process_func = partial(process_image, bboxes_dir=bboxes_dir, output_dir=output_dir, shrink_pixels=shrink_pixels)
        # Map the processing function to all image files with tqdm progress bar
        results = list(tqdm(pool.imap(process_func, all_image_files), total=len(all_image_files), desc="Processing images"))
    
    # Count successful and failed processes
    successful = sum(1 for result in results if result)
    failed = len(all_image_files) - successful
    print(f"\nInpainting completed: {successful} images processed successfully, {failed} failed")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Text removal inpainting with parallel processing")
    parser.add_argument('--cpus', type=int, default=os.cpu_count() or 4, 
                        help=f"Number of CPU cores to use (default: all available cores or 4 if undetectable, max: {os.cpu_count() or 'unknown'})")
    args = parser.parse_args()

    # Validate the number of CPUs
    max_cpus = os.cpu_count() or 4
    if args.cpus < 1:
        print(f"Error: Number of CPUs must be at least 1. Got {args.cpus}")
        exit(1)
    if args.cpus > max_cpus:
        print(f"Warning: Requested {args.cpus} CPUs, but only {max_cpus} available. Using {max_cpus} CPUs.")
        args.cpus = max_cpus
    
    print(f"Starting text removal inpainting process with {args.cpus} CPU cores...")
    IMAGES_FOLDER = "images_original2"
    BBOXES_FOLDER = "BBOX"
    OUTPUT_DIR = "images_val"
    process_all_images(IMAGES_FOLDER, BBOXES_FOLDER, OUTPUT_DIR, shrink_pixels=2, num_cpus=args.cpus)