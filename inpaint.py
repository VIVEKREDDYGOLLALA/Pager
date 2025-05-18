
import os
import cv2
import numpy as np
import re
from tqdm import tqdm
import glob

def read_bbox_file(bbox_path):
    bbox_data = []
    try:
        with open(bbox_path, 'r') as f:
            lines = f.readlines()
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith('[') and line.endswith(']') and ',' in line and 'paragraph' not in line and 'figure' not in line:
                try:
                    values = line.strip('[]').split(',')
                    width = int(values[0])
                    height = int(values[1])
                    bbox_data.append(['dimensions', [width, height]])
                    continue
                except:
                    pass
            match = re.match(r'\[(.*?), \[(.*?)\], (.*?), (.*?)\]', line)
            if match:
                bbox_type = match.group(1)
                coords_str = match.group(2)
                id1 = match.group(3)
                id2 = match.group(4)
                coords = [float(x) for x in coords_str.split(',')]
                if len(coords) >= 4:
                    x, y, width, height = coords
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
        box_type = box[0]
        skip_types = ['header', 'footer', 'figure', 'figure_1', 'formula', 'formula_1', 'table']
        if any(skip_type in box_type.lower() for skip_type in skip_types):
            skipped_boxes += 1
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

def process_all_images(images_dir, bboxes_dir, output_dir, shrink_pixels=2):
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, "masks"), exist_ok=True)
    image_extensions = ['.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp']
    all_image_files = []
    for ext in image_extensions:
        all_image_files.extend(glob.glob(os.path.join(images_dir, f"*{ext}")))
        all_image_files.extend(glob.glob(os.path.join(images_dir, f"*{ext.upper()}")))
    all_image_files = list(set(all_image_files))
    print(f"Found {len(all_image_files)} images to process")
    successful = 0
    failed = 0
    for image_path in tqdm(all_image_files, desc="Processing images"):
        image_basename = os.path.splitext(os.path.basename(image_path))[0]
        bbox_path = find_matching_bbox_file(image_basename, bboxes_dir)
        if bbox_path is None:
            print(f"Skipping {image_basename}: No matching bbox file found")
            failed += 1
            continue
        bbox_data = read_bbox_file(bbox_path)
        if not bbox_data:
            print(f"Skipping {image_basename}: No valid bbox data")
            failed += 1
            continue
        if inpaint_from_bboxes(image_path, bbox_data, output_dir, shrink_pixels):
            successful += 1
        else:
            failed += 1
    print(f"\nInpainting completed: {successful} images processed successfully, {failed} failed")

def refine_inpainting(output_dir, refinement_method="telea", radius=5):
    print("\nStarting refinement pass...")
    inpainted_files = (glob.glob(os.path.join(output_dir, "*.[pPjJ][nNpP][gG]")) +
                       glob.glob(os.path.join(output_dir, "*.[tT][iI][fF]")) +
                       glob.glob(os.path.join(output_dir, "*.[tT][iI][fF][fF]")) +
                       glob.glob(os.path.join(output_dir, "*.[bB][mM][pP]")) +
                       glob.glob(os.path.join(output_dir, "*.[jJ][pP][eE][gG]")))
    if not inpainted_files:
        print("No inpainted files found for refinement")
        return
    refined_dir = os.path.join(output_dir, "refined")
    os.makedirs(refined_dir, exist_ok=True)
    successful = 0
    failed = 0
    for inpainted_path in tqdm(inpainted_files, desc="Refining inpainting"):
        try:
            img = cv2.imread(inpainted_path)
            if img is None:
                print(f"Error: Could not read image {inpainted_path}")
                failed += 1
                continue
            base_filename = os.path.basename(inpainted_path)
            mask_path = os.path.join(output_dir, "masks", f"{os.path.splitext(base_filename)[0]}_mask.png")
            if not os.path.exists(mask_path):
                print(f"Error: Mask file not found: {mask_path}")
                failed += 1
                continue
            mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
            inpaint_method = cv2.INPAINT_NS if refinement_method.lower() == "ns" else cv2.INPAINT_TELEA
            refined = cv2.inpaint(img, mask, radius, inpaint_method)
            refined_path = os.path.join(refined_dir, f"{os.path.splitext(base_filename)[0]}_refined.png")
            cv2.imwrite(refined_path, refined)
            successful += 1
        except Exception as e:
            print(f"Error refining {inpainted_path}: {e}")
            failed += 1
    print(f"Refinement complete: {successful} images refined successfully, {failed} failed")
    print(f"Refined images saved to {refined_dir}")

if __name__ == "__main__":
    IMAGES_FOLDER = "images_val"
    BBOXES_FOLDER = "BBOX"
    OUTPUT_DIR = "inpainted_results"
    print("Starting text removal inpainting process...")
    process_all_images(IMAGES_FOLDER, BBOXES_FOLDER, OUTPUT_DIR, shrink_pixels=2)
    refine_inpainting(OUTPUT_DIR, refinement_method="telea", radius=5)