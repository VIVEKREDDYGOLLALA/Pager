import os
import json
import requests
import random
import argparse

# Base directories
json_base_folder = r'input_jsons'  # Root folder containing subfolders with JSON files
output_base_folder = r'BBOX'  # Base folder for BBOX outputs (e.g., BBOX_magazines)
images_base_folder = r'images_original'  # Base folder for downloaded images

# List of labels to skip (case-insensitive)
SKIP_LABELS = ["formula", "table"]

# Function to download an image from a URL
def download_image(image_url, output_path):
    try:
        response = requests.get(image_url, stream=True, timeout=10)
        if response.status_code == 200:
            with open(output_path, 'wb') as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)
            # print(f"Downloaded image to {output_path}")
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
                # print(f"Skipping record in {json_file}: Parsed record is not a dictionary (type: {type(parsed_record)})")
                with open("skipped_records.log", "a") as log:
                    log.write(f"[{json_file}] Parsed record is not a dictionary: {record}\n")
                return None
            # print(f"Parsed string record in {json_file} to dictionary")
            return parsed_record
        except json.JSONDecodeError:
            # print(f"Skipping record in {json_file}: String record is not valid JSON")
            with open("skipped_records.log", "a") as log:
                log.write(f"[{json_file}] Invalid JSON string: {record}\n")
            return None
    elif not isinstance(record, dict):
        # print(f"Skipping record in {json_file}: Record is not a dictionary (type: {type(record)})")
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
                    # Case-insensitive comparison
                    if any(skip_label.lower() in label.lower() for skip_label in SKIP_LABELS):
                        return True
        except Exception:
            continue
    return False

def process_record(record, output_folder, images_folder, json_file, doc_count, total_limit):
    """Process a single record and return whether it was successfully processed."""
    os.makedirs(output_folder, exist_ok=True)
    os.makedirs(images_folder, exist_ok=True)

    # Validate and parse the record
    record = validate_record(record, json_file)
    if record is None:
        return False

    try:
        image_id = record["id"]
    except (KeyError, TypeError) as e:
        # print(f"Skipping record in {json_file}: Missing or invalid 'id' field ({e})")
        with open("skipped_records.log", "a") as log:
            log.write(f"[{json_file}] Missing or invalid 'id' field: {e}\n")
        return False

    try:
        image_url, annotations = extract_annotations_and_image_url(record)

        if not image_url:
            # print(f"Skipping image ID {image_id}: No image URL.")
            with open("skipped_records.log", "a") as log:
                log.write(f"[{json_file}] Image ID {image_id}: No image URL\n")
            return False

        # Check if annotations contain any labels to skip
        if check_for_skip_labels(annotations):
            with open("skipped_records.log", "a") as log:
                log.write(f"[{json_file}] Image ID {image_id}: Skipped due to containing table/formula\n")
            return False

        original_width = annotations[0].get("original_width", None) if annotations else None
        original_height = annotations[0].get("original_height", None) if annotations else None

        if original_width is None or original_height is None:
            # print(f"Image dimensions not found for image ID {image_id}")
            with open("skipped_records.log", "a") as log:
                log.write(f"[{json_file}] Image ID {image_id}: Missing dimensions\n")
            return False

        image_name = os.path.basename(image_url)
        image_output_path = os.path.join(images_folder, image_name)
        bbox_file_name = f"{os.path.splitext(image_name)[0]}_{image_id}.txt"
        bbox_file_path = os.path.join(output_folder, bbox_file_name)

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

                    # Skip annotations with missing or unknown id
                    if bbox_id == "unknown" or not bbox_id:
                        # print(f"Skipping bounding box with unknown ID for image ID {image_id}")
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
            # print(f"No valid bounding boxes with IDs found for image ID {image_id}. Deleting BBOX file.")
            os.remove(bbox_file_path)
            # Also delete the downloaded image if it exists
            if os.path.exists(image_output_path):
                os.remove(image_output_path)
            with open("skipped_records.log", "a") as log:
                log.write(f"[{json_file}] Image ID {image_id}: No valid bounding boxes with IDs\n")
            return False

        print(f"Processed image ID ({doc_count + 1}/{total_limit})")
        return True
    except Exception as e:
        # print(f"Error processing record for image ID {image_id}: {e}")
        with open("skipped_records.log", "a") as log:
            log.write(f"[{json_file}] Image ID {image_id}: Error - {e}\n")
        # Clean up any partially created files
        if 'bbox_file_path' in locals() and os.path.exists(bbox_file_path):
            os.remove(bbox_file_path)
        if 'image_output_path' in locals() and os.path.exists(image_output_path):
            os.remove(image_output_path)
        return False

def collect_records(json_base_folder, doc_type):
    """Collect all records from JSON files in the specified doc_type subfolder."""
    all_records = []
    subfolder_path = os.path.join(json_base_folder, doc_type)
    
    if not os.path.isdir(subfolder_path):
        # print(f"Subfolder {subfolder_path} does not exist.")
        return all_records

    for file_name in os.listdir(subfolder_path):
        if file_name.endswith('.json'):
            json_file_path = os.path.join(subfolder_path, file_name)
            try:
                with open(json_file_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                # Store each record with metadata
                for record in data:
                    all_records.append({
                        "record": record,
                        "json_file": json_file_path,
                        "subfolder": doc_type
                    })
                # print(f"Collected {len(data)} records from {json_file_path}")
            except Exception as e:
                # print(f"Error reading JSON file {json_file_path}: {e}")
                with open("skipped_records.log", "a") as log:
                    log.write(f"[{json_file_path}] Error reading file: {e}\n")
    
    return all_records

def process_json_folder(json_base_folder, doc_type, num_docs):
    """Process up to num_docs images from JSON files in the specified doc_type subfolder."""
    # Validate inputs
    if num_docs < 1:
        # print(f"Invalid number of documents: {num_docs}. Must be at least 1.")
        return

    # Ensure skipped_records.log exists
    with open("skipped_records.log", "a") as log:
        log.write(f"Starting processing for doc_type: {doc_type}, num_docs: {num_docs}\n")

    # Collect all records from the specified subfolder
    all_records = collect_records(json_base_folder, doc_type)
    if not all_records:
        # print(f"No records found in {doc_type} subfolder.")
        return

    # Shuffle records for random selection
    random.shuffle(all_records)

    doc_count = 0
    for item in all_records:  # Process all records until num_docs is reached
        if doc_count >= num_docs:
            break
        
        record = item["record"]
        subfolder_name = item["subfolder"]
        json_file = item["json_file"]
        
        # Determine output folders
        output_folder = os.path.join(output_base_folder)
        images_folder = os.path.join(images_base_folder)
        
        # Process the record
        success = process_record(record, output_folder, images_folder, json_file, doc_count, num_docs)
        if success:
            doc_count += 1
            # print(f"Processed record from {json_file} (Total: {doc_count}/{num_docs})")

    if doc_count < num_docs:
        print(f"Warning: Only {doc_count}/{num_docs} valid records were processed. Check skipped_records.log for details.")

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Process JSON files for a specific document type with a total document limit")
    parser.add_argument(
        "--doc_type",
        required=True,
        help="Document type (subfolder name, e.g., magazines, newspapers)"
    )
    parser.add_argument(
        "--num_docs",
        type=int,
        required=True,
        help="Total number of documents to process"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Process the specified subfolder
    process_json_folder(json_base_folder, args.doc_type, args.num_docs)