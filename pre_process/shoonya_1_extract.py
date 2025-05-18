import os
import json
import requests

# Function to download an image from a URL
def download_image(image_url, output_path):
    try:
        response = requests.get(image_url, stream=True, timeout=10)
        if response.status_code == 200:
            with open(output_path, 'wb') as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)
            print(f"Downloaded image to {output_path}")
        else:
            print(f"Failed to download {image_url}: HTTP {response.status_code}")
    except Exception as e:
        print(f"Error downloading {image_url}: {e}")

def extract_annotations_and_image_url(record):
    annotations = []
    image_url = None

    if "data" in record:
        image_url = record["data"].get("image_url", "")

        # Check if "ocr_prediction_json" exists and is a string
        ocr_data = record["data"].get("ocr_prediction_json", "[]")
        if isinstance(ocr_data, str):
            try:
                ocr_data = json.loads(ocr_data)  # Convert string to list of dictionaries
            except json.JSONDecodeError as e:
                print(f"Error decoding OCR data: {e}")
                ocr_data = []

        if isinstance(ocr_data, list):
            annotations.extend(ocr_data)

    if "annotations" in record and isinstance(record["annotations"], list):
        for annotation in record["annotations"]:
            annotations.extend(annotation.get("result", []))

    return image_url, annotations

# Function to process a single JSON file
def process_single_json(json_file, output_folder, images_folder, doc_limit, doc_count):
    if doc_count[0] >= doc_limit:
        return

    os.makedirs(output_folder, exist_ok=True)
    os.makedirs(images_folder, exist_ok=True)

    try:
        with open(json_file, 'r', encoding='utf-8') as file:
            data = json.load(file)
    except Exception as e:
        print(f"Error reading JSON file {json_file}: {e}")
        return

    for record in data:
        if doc_count[0] >= doc_limit:
            return
        
        try:
            image_id = record["id"]
            image_url, annotations = extract_annotations_and_image_url(record)

            if not image_url or image_url.endswith("_0.png"):
                continue

            original_width = annotations[0].get("original_width", None) if annotations else None
            original_height = annotations[0].get("original_height", None) if annotations else None

            if original_width is None or original_height is None:
                print(f"Image dimensions not found for image ID {image_id}")
                continue

            image_name = os.path.basename(image_url)
            image_output_path = os.path.join(images_folder, image_name)
            bbox_file_name = f"{os.path.splitext(image_name)[0]}_{image_id}.txt"
            bbox_file_path = os.path.join(output_folder, bbox_file_name)
            download_image(image_url, image_output_path)
            unique_bboxes = set()
            with open(bbox_file_path, 'w') as bbox_file:
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

                        norm_x1 = int((x1 / 100.0) * original_width)
                        norm_y1 = int((y1 / 100.0) * original_height)
                        norm_width = int((width / 100.0) * original_width)
                        norm_height = int((height / 100.0) * original_height)

                        bbox_tuple = (label, norm_x1, norm_y1, norm_width, norm_height, bbox_id, image_id)
                        if bbox_tuple not in unique_bboxes:
                            unique_bboxes.add(bbox_tuple)
                            bbox_file.write(f"[{label}, [{norm_x1:.6f}, {norm_y1:.6f}, {norm_width:.6f}, {norm_height:.6f}], {bbox_id}, {image_id}]\n")
                    except Exception as e:
                        print(f"Error processing bounding box for image ID {image_id}: {e}")
            
            doc_count[0] += 1
        except Exception as e:
            print(f"Error processing record for image ID {image_id if 'image_id' in locals() else 'unknown'}: {e}")

def process_json_folder(folder_path, output_folder, images_folder, doc_limit=3535):
    doc_count = [0]
    for file_name in os.listdir(folder_path):
        if file_name.endswith('.json'):
            json_file_path = os.path.join(folder_path, file_name)
            print(f"Processing file: {json_file_path}")
            process_single_json(json_file_path, output_folder, images_folder, doc_limit, doc_count)
            if doc_count[0] >= doc_limit:
                print("Reached document processing limit.")
                break

# Example usage
json_folder_path = r'input_jsons/magazines_jsonns'  
output_folder = r'BBOX_magazines'
images_folder = r'images_val_magazines'

process_json_folder(json_folder_path, output_folder, images_folder, doc_limit=100)
