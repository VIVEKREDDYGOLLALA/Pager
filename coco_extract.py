import os
import json
import requests
import random
import argparse

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
        else:
            print(f"Failed to download {image_url}: HTTP {response.status_code}")
    except Exception as e:
        print(f"Error downloading {image_url}: {e}")

def extract_annotations_and_image_url(coco_data, image_id):
    """Extract image_url, dimensions, and annotations for a given image_id from COCO JSON."""
    annotations = []
    image_url = None
    original_width = None
    original_height = None

    # Find the image entry
    for image in coco_data.get("images", []):
        if image.get("id") == image_id:
            image_url = image.get("image_url", "")
            original_width = image.get("width")
            original_height = image.get("height")
            break

    # Get annotations for this image
    for annotation in coco_data.get("annotations", []):
        if annotation.get("image_id") == image_id:
            annotations.append(annotation)

    # Map category_id to label name
    category_map = {cat["id"]: cat["name"] for cat in coco_data.get("categories", [])}
    for ann in annotations:
        ann["label"] = category_map.get(ann.get("category_id"), "unknown")

    return image_url, original_width, original_height, annotations

def validate_coco_data(coco_data, json_file):
    """Validate COCO JSON data structure."""
    if not isinstance(coco_data, dict):
        with open("skipped_records.log", "a") as log:
            log.write(f"[{json_file}] Invalid JSON: Not a dictionary\n")
        return False
    if "images" not in coco_data or "annotations" not in coco_data or "categories" not in coco_data:
        with open("skipped_records.log", "a") as log:
            log.write(f"[{json_file}] Missing required COCO fields: images, annotations, or categories\n")
        return False
    return True

def check_for_skip_labels(annotations):
    """Check if annotations contain any labels that should be skipped."""
    for ann in annotations:
        label = ann.get("label", "").lower()
        if any(skip_label.lower() == label for skip_label in SKIP_LABELS):
            return True
    return False

def collect_labels(json_folder):
    """Collect unique labels from all COCO JSON files."""
    unique_labels = set()
    for file_name in os.listdir(json_folder):
        if file_name.endswith('.json'):
            json_file_path = os.path.join(json_folder, file_name)
            try:
                with open(json_file_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                if not validate_coco_data(data, json_file_path):
                    continue
                for cat in data.get("categories", []):
                    label = cat.get("name", "").lower()
                    if not any(skip_label.lower() == label.lower() for skip_label in SKIP_LABELS):
                        unique_labels.add(label.lower())
            except Exception as e:
                with open("skipped_records.log", "a") as log:
                    log.write(f"[{json_file_path}] Error reading file: {e}\n")
    unique_labels.add("unknown")
    return sorted(unique_labels)

def process_record(coco_data, image_id, output_folder, images_folder, json_file, doc_count, total_images, labels):
    """Process a single image record from COCO JSON."""
    os.makedirs(output_folder, exist_ok=True)
    os.makedirs(images_folder, exist_ok=True)

    image_url, original_width, original_height, annotations = extract_annotations_and_image_url(coco_data, image_id)

    if not image_url:
        with open("skipped_records.log", "a") as log:
            log.write(f"[{json_file}] Image ID {image_id}: No image URL\n")
        return False

    if original_width is None or original_height is None:
        with open("skipped_records.log", "a") as log:
            log.write(f"[{json_file}] Image ID {image_id}: Missing dimensions\n")
        return False

    if check_for_skip_labels(annotations):
        with open("skipped_records.log", "a") as log:
            log.write(f"[{json_file}] Image ID {image_id}: Skipped due to containing table/formula\n")
        return False

    image_name = os.path.basename(image_url)
    image_output_path = os.path.join(images_folder, folder, image_name)
    bbox_file_name = f"{os.path.splitext(image_name)[0]}_{image_id}.txt"
    bbox_file_path = os.path.join(output_folder, bbox_file_name)

    # Download image
    download_image(image_url, image_output_path)

    unique_bboxes = []
    valid_bboxes = 0
    with open(bbox_file_path, 'w', encoding='utf-8') as f:
        f.write(f"[{original_height}, {original_width}]\n")
        for ann in annotations:
            try:
                label = ann["label"]
                if label.lower() not in labels:
                    continue

                x1, y1, width, height = ann["bbox"]
                bbox_id = ann["id"]
                image_id = ann["image_id"]

                # Validate bounding box
                if any(v < 0 for v in [x1, y1, width, height]):
                    continue

                bbox_tuple = (label, x1, y1, width, height, bbox_id, image_id)
                if bbox_tuple not in unique_bboxes:
                    unique_bboxes.add(bbox_tuple)
                    f.write(f"[{label}, [{x1:.2f}, {y1:.2f}, {width:.2f}, {height:.2f}], {bbox_id}, {image_id}]\n")
                    valid_bboxes += 1
                except Exception as e:
                    # print(f"Error processing bounding box for image {ID {image_id}: {bbox_id}: {e}")
                    continue

        if valid_bboxes == 0:
            os.remove(bbox_file_path)
            if os.path.exists(image_output_path):
                os.remove(image_output_path)
            with open("skipped_records.log", "a") as log:
                log.write(f"[{json_file}] Image ID {image_id}: No valid annotations\n")
            return False

        print(f"Processed image ID {image_id} ({doc_count + 1}/{total_images})")
        return True
    return None

def process_json_folder(json_folder, doc_type, num_images):
    """Process up to num_images from COCO JSON files."""
    if num_images < 0:
        print("Error: num_images must be non-negative")
        return

    output_folder = os.path.join(output_base_folder, doc_type)
    images_folder = os.path.join(images_base_folder, doc_type)

    with open("skipped_records.log", "a") as log:
        log.write(f"[{doc_type}] Starting processing, num_images: {num_images}\n")

    labels = collect_labels(json_folder)
    print(f"Extracted {len(labels)} unique labels: {labels}")

    image_records = []
    for file_name in os.listdir(json_folder):
        if file_name.endswith('.json'):
            json_file_path = os.path.join(json_folder, file_name)
            try:
                with open(json_file_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                if not validate_coco_data(data, json_file_path):
                    continue
                for image in data.get("images", []):
                    image_records.append({
                        "coco_data": data,
                        "image_id": image["id"],
                        "json_file": json_file_path
                    })
            except Exception as e:
                with open("skipped_records.log", "a") as log:
                    log.write(f"[{json_file_path}] Error reading file: {e}\n")

    if not image_records:
        print(f"No valid image records found in {json_folder}")
        return

    random.shuffle(image_records)

    image_count = 0
    for item in image_records:
        if image_count >= num_images:
            break
        success = process_record(
            item["coco_data"],
            item["image_id"],
            output_folder,
            images_folder,
            item["json_file"],
            image_count,
            num_images,
            labels
        )
        if success:
            image_count += 1

    if image_count < num_images:
        print(f"Warning: Only {image_count}/{num_images} images processed. Check skipped_records.log")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process COCO JSON files for a document type")
    parser.add_argument(
        "--json_folder",
        required=True,
        help="Path to folder containing COCO JSON files"
    )
    parser.add_argument(
        "--doc_type",
        required=True,
        help="Document type (e.g., magazines, newspapers)"
    )
    parser.add_argument(
        "--num_images",
        type=int,
        required=True,
        help="Number of images to process"
    )
    
    args = parser.parse_args()
    process_json_folder(args.json_folder, args.doc_type, args.num_images)