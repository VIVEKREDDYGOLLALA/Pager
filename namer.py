import os
import json
import glob
import re

def split_and_rename_json_files(json_folder, bboxes_folder, output_folder):
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    
    # Create a mapping from image_id to image_name
    image_id_to_name = {}
    for bbox_file in glob.glob(os.path.join(bboxes_folder, "*.txt")):
        bbox_filename = os.path.basename(bbox_file)
        # Extract image_name and image_id from the bbox filename
        match = re.match(r'(.+)_(\d+)\.txt$', bbox_filename)
        if match:
            image_name = match.group(1)
            image_id = match.group(2)
            image_id_to_name[image_id] = image_name
    
    # Process each JSON file
    for json_file in glob.glob(os.path.join(json_folder, "*.json")):
        json_filename = os.path.basename(json_file)
        json_name = os.path.splitext(json_filename)[0]
        
        # Load the JSON data
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Group annotations by image_id
        annotations_by_image = {}
        for annotation in data.get("annotations", []):
            image_id = annotation.get("image_id")
            if image_id not in annotations_by_image:
                annotations_by_image[image_id] = []
            annotations_by_image[image_id].append(annotation)
        
        # Create and save separate JSON files for each image_id
        for image_id, annotations in annotations_by_image.items():
            if image_id in image_id_to_name:
                image_name = image_id_to_name[image_id]
                output_filename = f"{json_name}_{image_name}.json"
                output_path = os.path.join(output_folder, output_filename)
                
                # Create a new JSON object with only annotations for this image_id
                new_data = {"annotations": annotations}
                
                # Save the new JSON file
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(new_data, f, ensure_ascii=False, indent=4)
                
                print(f"Created: {output_filename}")
            else:
                print(f"Warning: No matching bbox file found for image_id {image_id}")

# Example usage
json_folder = "output_jsons"
bboxes_folder = "BBOX"
output_folder = "Image_jsons"

split_and_rename_json_files(json_folder, bboxes_folder, output_folder)