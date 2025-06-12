import os
import json
import requests
import random
import argparse
import re
from multiprocessing import Pool, cpu_count

# Base directories
json_base_folder = r'Ai_jsons'  # Root folder containing subfolders with JSON files
output_base_folder = r'BBOX'  # Base folder for BBOX outputs
images_base_folder = r'images_original2'  # Base folder for downloaded images

# List of labels to skip (case-insensitive)
SKIP_LABELS = ["formula", "table"]

def should_process_image(image_url, image_patterns):
    """
    Check if the image should be processed based on its filename patterns.
    Returns True if the image matches any of the specified patterns.
    
    Args:
        image_url: URL of the image
        image_patterns: List of patterns to match against
    
    Patterns can be:
        - "normal": Images that don't end with _[number].png
        - "_0": Images ending with _0.png
        - "_1": Images ending with _1.png
        - "_2": Images ending with _2.png
        - etc.
        - "all": Process all images (no filtering)
    """
    if not image_url:
        return False
    
    if not image_patterns or "all" in image_patterns:
        return True
    
    image_name = os.path.basename(image_url).lower()
    image_name_without_ext = os.path.splitext(image_name)[0]
    
    for pattern in image_patterns:
        pattern = pattern.lower().strip()
        
        if pattern == "normal":
            # Check if image doesn't end with _[number]
            if not re.search(r'_\d+$', image_name_without_ext):
                return True
        elif pattern.startswith("_"):
            # Check for specific number patterns like _0, _1, _2, etc.
            try:
                number = pattern[1:]  # Remove the underscore
                if image_name_without_ext.endswith(f"_{number}"):
                    return True
            except:
                continue
        elif pattern.isdigit():
            # Handle cases where user just specifies numbers like "0", "1", "2"
            if image_name_without_ext.endswith(f"_{pattern}"):
                return True
    
    return False

# Function to download an image from a URL
def download_image(image_url, output_path):
    try:
        response = requests.get(image_url, stream=True, timeout=10)
        if response.status_code == 200:
            with open(output_path, 'wb') as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)
        else:
            print(f"Failed to download {image_url}: HTTP {response.status_code}")
    except Exception as e:
        print(f"Error downloading {image_url}: {e}")

def extract_annotations_and_image_url(record):
    annotations = []
    image_url = None

    if "data" in record:
        image_url = record["data"].get("image_url", "")
        if "ocr_prediction_json" in record["data"]:
            annotations.extend(record["data"]["ocr_prediction_json"])

    if "annotations" in record and isinstance(record["annotations"], list):
        for annotation in record["annotations"]:
            annotations.extend(annotation.get("result", []))

    return image_url, annotations

def validate_record(record, json_file, image_id=None):
    """Validate and parse a record, returning a dictionary or None if invalid."""
    if isinstance(record, str):
        try:
            parsed_record = json.loads(record)
            if not isinstance(parsed_record, dict):
                with open("skipped_records.log", "a") as log:
                    log.write(f"[{json_file}] Parsed record is not a dictionary: {record}\n")
                return None
            return parsed_record
        except json.JSONDecodeError:
            with open("skipped_records.log", "a") as log:
                log.write(f"[{json_file}] Invalid JSON string: {record}\n")
            return None
    elif not isinstance(record, dict):
        with open("skipped_records.log", "a") as log:
            log.write(f"[{json_file}] Record is not a dictionary: {record}\n")
        return None
    return record

def check_for_skip_labels(annotations):
    """Check if annotations contain any labels that should be skipped."""
    for annotation in annotations:
        try:
            bbox_value = annotation.get("value", annotation)
            if "labels" in bbox_value and bbox_value["labels"]:
                for label in bbox_value["labels"]:
                    if any(skip_label.lower() in label.lower() for skip_label in SKIP_LABELS):
                        return True
        except Exception:
            continue
    return False

def process_record(args):
    """Process a single record and return whether it was successfully processed."""
    record, output_folder, images_folder, json_file, doc_count, total_limit, doc_type, image_patterns = args
    os.makedirs(output_folder, exist_ok=True)
    os.makedirs(images_folder, exist_ok=True)

    # Validate and parse the record
    record = validate_record(record, json_file)
    if record is None:
        return False, None

    try:
        image_id = record["id"]
    except (KeyError, TypeError) as e:
        with open("skipped_records.log", "a") as log:
            log.write(f"[{json_file}] Missing or invalid 'id' field: {e}\n")
        return False, None

    try:
        image_url, annotations = extract_annotations_and_image_url(record)

        if not image_url:
            with open("skipped_records.log", "a") as log:
                log.write(f"[{json_file}] Image ID {image_id}: No image URL\n")
            return False, image_id

        # Check if image should be processed based on filename patterns
        if not should_process_image(image_url, image_patterns):
            image_name = os.path.basename(image_url)
            with open("skipped_records.log", "a") as log:
                log.write(f"[{json_file}] Image ID {image_id}: Skipped image due to pattern filter: {image_name}\n")
            return False, image_id

        if check_for_skip_labels(annotations):
            with open("skipped_records.log", "a") as log:
                log.write(f"[{json_file}] Image ID {image_id}: Skipped due to containing table/formula\n")
            return False, image_id

        original_width = annotations[0].get("original_width", None) if annotations else None
        original_height = annotations[0].get("original_height", None) if annotations else None

        if original_width is None or original_height is None:
            with open("skipped_records.log", "a") as log:
                log.write(f"[{json_file}] Image ID {image_id}: Missing dimensions\n")
            return False, image_id

        image_name = os.path.basename(image_url)
        image_output_path = os.path.join(images_folder, image_name)
        bbox_file_name = f"{os.path.splitext(image_name)[0]}_{image_id}.txt"
        bbox_file_path = os.path.join(output_folder, bbox_file_name)

        # Check for file name conflicts
        if os.path.exists(image_output_path) or os.path.exists(bbox_file_path):
            with open("skipped_records.log", "a") as log:
                log.write(f"[{json_file}] Image ID {image_id}: Skipped due to existing output file(s) ({image_name} or {bbox_file_name})\n")
            return False, image_id

        # Download image
        download_image(image_url, image_output_path)

        unique_bboxes = set()
        valid_bboxes = 0
        with open(bbox_file_path, 'w', encoding='utf-8') as bbox_file:
            bbox_file.write(f"[{original_height}, {original_width}]\n")
            for annotation in annotations:
                try:
                    bbox_value = annotation.get("value", annotation)
                    x1 = bbox_value["x"]
                    y1 = bbox_value["y"]
                    width = bbox_value["width"]
                    height = bbox_value["height"]
                    label = bbox_value["labels"][0] if bbox_value.get("labels") else "unknown"
                    bbox_id = annotation.get("id", "unknown")

                    if bbox_id == "unknown" or not bbox_id:
                        continue

                    norm_x1 = int((x1 / 100.0) * original_width)
                    norm_y1 = int((y1 / 100.0) * original_height)
                    norm_width = int((width / 100.0) * original_width)
                    norm_height = int((height / 100.0) * original_height)

                    bbox_tuple = (label, norm_x1, norm_y1, norm_width, norm_height, bbox_id, image_id)
                    if bbox_tuple not in unique_bboxes:
                        unique_bboxes.add(bbox_tuple)
                        bbox_file.write(f"[{label}, [{norm_x1:.6f}, {norm_y1:.6f}, {norm_width:.6f}, {norm_height:.6f}], {bbox_id}, {image_id}]\n")
                        valid_bboxes += 1
                except Exception as e:
                    print(f"Error processing bounding box for image ID {image_id}: {e}")

        if valid_bboxes == 0:
            os.remove(bbox_file_path)
            if os.path.exists(image_output_path):
                os.remove(image_output_path)
            with open("skipped_records.log", "a") as log:
                log.write(f"[{json_file}] Image ID {image_id}: No valid bounding boxes with IDs\n")
            return False, image_id

        print(f"Processed image ID {image_id} ({doc_count + 1}/{total_limit}) for doc_type {doc_type}")
        return True, image_id
    except Exception as e:
        with open("skipped_records.log", "a") as log:
            log.write(f"[{json_file}] Image ID {image_id}: Error - {e}\n")
        if 'bbox_file_path' in locals() and os.path.exists(bbox_file_path):
            os.remove(bbox_file_path)
        if 'image_output_path' in locals() and os.path.exists(image_output_path):
            os.remove(image_output_path)
        return False, image_id

def collect_records(json_base_folder, doc_type):
    """Collect all records from JSON files in the specified doc_type subfolder."""
    all_records = []
    subfolder_path = os.path.join(json_base_folder, doc_type)
    
    if not os.path.isdir(subfolder_path):
        print(f"No subfolder found for doc_type: {doc_type}")
        return all_records

    for file_name in os.listdir(subfolder_path):
        if file_name.endswith('.json'):
            json_file_path = os.path.join(subfolder_path, file_name)
            try:
                with open(json_file_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                for record in data:
                    all_records.append({
                        "record": record,
                        "json_file": json_file_path,
                        "subfolder": doc_type
                    })
            except Exception as e:
                with open("skipped_records.log", "a") as log:
                    log.write(f"[{json_file_path}] Error reading file: {e}\n")
    
    return all_records

def process_json_folder(json_base_folder, doc_types, num_docs, num_cores, image_patterns):
    """Process exactly num_docs valid images from JSON files for each doc_type using multiple cores."""
    if num_docs < 1:
        print(f"Invalid number of documents: {num_docs}. Must be at least 1.")
        return

    # Validate number of cores
    max_cores = cpu_count()
    num_cores = min(num_cores, max_cores)
    if num_cores < 1:
        print(f"Invalid number of cores: {num_cores}. Setting to 1.")
        num_cores = 1
    print(f"Using {num_cores} CPU cores for processing.")

    # Print image pattern information
    if not image_patterns or "all" in image_patterns:
        print("Processing ALL images (no filtering)")
        pattern_description = "all images"
    else:
        pattern_descriptions = []
        for pattern in image_patterns:
            if pattern == "normal":
                pattern_descriptions.append("normal images (no _[number] suffix)")
            elif pattern.startswith("_") or pattern.isdigit():
                num = pattern[1:] if pattern.startswith("_") else pattern
                pattern_descriptions.append(f"images ending with _{num}.png")
        pattern_description = ", ".join(pattern_descriptions)
        print(f"Processing images matching patterns: {pattern_description}")

    # Ensure skipped_records.log exists
    with open("skipped_records.log", "a") as log:
        log.write(f"Starting processing for doc_types: {', '.join(doc_types)}, num_docs per type: {num_docs}, num_cores: {num_cores}\n")
        log.write(f"Image patterns: {image_patterns}\n")

    for doc_type in doc_types:
        print(f"\nProcessing doc_type: {doc_type}")
        print(f"Filtering for: {pattern_description}")
        
        # Collect all records from the specified subfolder
        all_records = collect_records(json_base_folder, doc_type)
        if not all_records:
            print(f"No records found in {doc_type} subfolder.")
            continue

        # Shuffle records for random selection
        random.shuffle(all_records)

        # Prepare arguments for parallel processing
        tasks = []
        output_folder = output_base_folder  # Use base folder directly
        images_folder = images_base_folder  # Use base folder directly
        processed_count = 0
        processed_ids = set()
        index = 0
        batch_size = num_cores * 2  # Process records in batches to optimize parallel processing
        skipped_pattern_images = 0  # Counter for images skipped due to pattern

        while processed_count < num_docs and index < len(all_records):
            # Prepare a batch of tasks
            batch_tasks = []
            for i in range(index, min(index + batch_size, len(all_records))):
                item = all_records[i]
                record = item["record"]
                
                # Pre-check if this record should be skipped due to pattern
                if "data" in record:
                    image_url = record["data"].get("image_url", "")
                    if not should_process_image(image_url, image_patterns):
                        skipped_pattern_images += 1
                        continue
                
                if record.get("id") not in processed_ids:
                    batch_tasks.append((
                        record,
                        output_folder,
                        images_folder,
                        item["json_file"],
                        processed_count,
                        num_docs,
                        doc_type,
                        image_patterns
                    ))
            index += batch_size

            # Process batch in parallel
            if batch_tasks:  # Only process if we have tasks
                with Pool(processes=num_cores) as pool:
                    results = pool.map(process_record, batch_tasks)

                # Count successful processes and track processed IDs
                for success, image_id in results:
                    if success and image_id:
                        processed_count += 1
                        processed_ids.add(image_id)
                        if processed_count <= num_docs:
                            print(f"Valid record count: {processed_count}/{num_docs} for doc_type {doc_type}")
                    elif image_id:
                        processed_ids.add(image_id)

            # Break if we've reached the desired number of valid records
            if processed_count >= num_docs:
                break

        print(f"Skipped {skipped_pattern_images} images due to pattern filter for doc_type {doc_type}")
        
        if processed_count < num_docs:
            print(f"Warning: Only {processed_count}/{num_docs} valid records were processed for doc_type {doc_type}. Check skipped_records.log for details.")
        else:
            print(f"Successfully processed {processed_count}/{num_docs} valid records for doc_type {doc_type}.")

def validate_image_patterns(patterns):
    """Validate and normalize image patterns."""
    if not patterns:
        return ["all"]
    
    valid_patterns = []
    for pattern in patterns:
        pattern = pattern.strip().lower()
        if pattern in ["all", "normal"]:
            valid_patterns.append(pattern)
        elif pattern.startswith("_") and pattern[1:].isdigit():
            valid_patterns.append(pattern)
        elif pattern.isdigit():
            valid_patterns.append(f"_{pattern}")
        else:
            print(f"Warning: Invalid pattern '{pattern}' ignored. Valid patterns: 'all', 'normal', '_0', '_1', '0', '1', etc.")
    
    if not valid_patterns:
        print("No valid patterns specified. Using 'all' as default.")
        return ["all"]
    
    return valid_patterns

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Process JSON files for multiple document types with flexible image filtering",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Image Pattern Examples:
  --image_patterns all                 # Process all images
  --image_patterns normal              # Only images without _[number] suffix
  --image_patterns _0                  # Only images ending with _0.png
  --image_patterns _1 _2               # Images ending with _1.png or _2.png
  --image_patterns 0 1 2               # Same as _0 _1 _2
  --image_patterns normal _1           # Normal images OR images ending with _1.png
        """
    )
    
    parser.add_argument(
        "--doc_types",
        required=True,
        nargs='+',
        help="List of document types (subfolder names, e.g., magazines newspapers)"
    )
    parser.add_argument(
        "--num_docs",
        type=int,
        required=True,
        help="Number of documents to process per document type"
    )
    parser.add_argument(
        "--num_cores",
        type=int,
        default=cpu_count(),
        help="Number of CPU cores to use (default: all available cores)"
    )
    parser.add_argument(
        "--image_patterns",
        nargs='*',
        default=["all"],
        help="Image patterns to process. Options: 'all', 'normal', '_0', '_1', '_2', etc. or just numbers like '0', '1', '2'"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Validate and normalize image patterns
    validated_patterns = validate_image_patterns(args.image_patterns)
    
    print(f"Validated image patterns: {validated_patterns}")
    
    # Process the specified subfolders
    process_json_folder(json_base_folder, args.doc_types, args.num_docs, args.num_cores, validated_patterns)