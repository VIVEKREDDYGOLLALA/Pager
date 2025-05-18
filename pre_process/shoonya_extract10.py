import os
import json
import requests

# Paths
json_file_path = r'input_jsons/Assamese_Magazines_4274.json'  # Combined JSON file with annotations and OCR predictions
output_folder = r'Magazines2'
images_folder = r'images_val'

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

# Function to process the JSON and extract bbox details along with image dimensions from annotations
def process_json(json_file, output_folder, images_folder, max_images=1000):
    os.makedirs(output_folder, exist_ok=True)
    os.makedirs(images_folder, exist_ok=True)

    try:
        with open(json_file, 'r', encoding='utf-8') as file:
            data = json.load(file)
    except Exception as e:
        print(f"Error reading JSON file: {e}")
        return

    image_count = 0

    for record in data:
        if image_count >= max_images:
            break

        try:
            image_id = record["id"]
            image_data = record["data"]
            image_url = image_data["image_url"]

            annotations = record.get("annotations", [])
            if not annotations:
                print(f"No annotations found for image ID {image_id}")
                continue

            annotation = annotations[0]
            original_width = annotation["result"][0].get("original_width")
            original_height = annotation["result"][0].get("original_height")

            if original_width is None or original_height is None:
                print(f"Image dimensions not found for image ID {image_id}")
                continue

            normalized_width = original_width
            normalized_height = original_height

            image_name = os.path.basename(image_url)
            image_output_path = os.path.join(images_folder, image_name)
            download_image(image_url, image_output_path)

            bbox_file_name = f"{os.path.splitext(image_name)[0]}_{image_id}.txt"
            bbox_file_path = os.path.join(output_folder, bbox_file_name)

            unique_bboxes = set()

            with open(bbox_file_path, 'w') as bbox_file:
                bbox_file.write(f"[{original_height}, {original_width}]\n")
                for annotation in annotations:
                    for result in annotation.get("result", []):
                        try:
                            bbox_value = result["value"]
                            x1 = bbox_value["x"]
                            y1 = bbox_value["y"]
                            width = bbox_value["width"]
                            height = bbox_value["height"]
                            label = bbox_value["labels"][0] if bbox_value["labels"] else "unknown"
                            bbox_id = result.get("id", "unknown")

                            norm_x1 = int((x1 / 100.0) * normalized_width)
                            norm_y1 = int((y1 / 100.0) * normalized_height)
                            norm_width = int((width / 100.0) * normalized_width)
                            norm_height = int((height / 100.0) * normalized_height)

                            bbox_tuple = (label, norm_x1, norm_y1, norm_width, norm_height, bbox_id, image_id)
                            if bbox_tuple not in unique_bboxes:
                                unique_bboxes.add(bbox_tuple)
                                bbox_file.write(f"[{label}, [{norm_x1:.6f}, {norm_y1:.6f}, {norm_width:.6f}, {norm_height:.6f}], {bbox_id}, {image_id}]\n")
                        except Exception as e:
                            print(f"Error processing bounding box for image ID {image_id}: {e}")

            image_count += 1

        except Exception as e:
            print(f"Error processing record for image ID {image_id if 'image_id' in locals() else 'unknown'}: {e}")

    print("Processing complete. Bounding boxes saved and images downloaded.")

# Call the function
process_json(json_file_path, output_folder, images_folder, max_images=1000)
