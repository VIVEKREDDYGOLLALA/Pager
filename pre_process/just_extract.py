import os
import json
import shutil
import os
import re

base_folder = r'BBOX'
base_folder_2 = r'BBOX' 
json_file_path = r'input_jsons/magazines/English_Magazines_3502.json'
input_folder = r'BBOX'
base_folder_3 = r'BBOX'  

def create_folders_and_save_bbox(json_file, input_folder):
    # Load the JSON data with utf-8 encoding
    with open(json_file, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    # Create a dictionary to map image ids to their details
    image_dict = {img['id']: img for img in data['images']}
    
    # Create a dictionary to map category ids to their names
    category_dict = {cat['id']: cat['name'] for cat in data['categories']}
    
    processed_files = set()

    # Define the base output directory
    base_folder = os.path.join('M6Doc')
    os.makedirs(base_folder, exist_ok=True)  # Create the directory if it doesn't exist

    # Process each annotation
    for annotation in data['annotations']:
        image_id = annotation['image_id']
        bbox = annotation['bbox']
        category_id = annotation['category_id']
        image_info = image_dict[image_id]
        image_height = image_info['height']
        image_width = image_info['width']
        file_name = image_info['file_name']

        # Use 'doc_name' if it exists, otherwise use a default value
        doc_name = image_info.get('doc_name', 'BBOX_val')
        
        # Create a folder named after the doc_name (if it doesn't exist)
        folder_path = os.path.join(base_folder, doc_name)
        os.makedirs(folder_path, exist_ok=True)

        # Create a text file with the name formatted as filename_image_id (with .txt extension)
        bbox_file_path = os.path.join(folder_path, f"{file_name.rsplit('.', 1)[0]}_{image_id}.txt")

        # Check if the file has already been processed
        if bbox_file_path not in processed_files:
            # Write the image dimensions only once when the file is created
            with open(bbox_file_path, 'w') as bbox_file:
                bbox_file.write(f"[{image_height},{image_width}]\n")
            # Mark the file as processed
            processed_files.add(bbox_file_path)
        
        # Append the bounding box details to the file
        with open(bbox_file_path, 'a') as bbox_file:
            bbox_file.write(f"[{category_dict.get(category_id, 'unknown')}, {bbox}, {annotation['id']}, {image_id}]\n")
    
    # After extraction, classify the files
    classify_txt_files_by_prefix(base_folder)  # Change to the correct path if needed
    
    print("Bounding box details have been saved and classified.")

def classify_txt_files_by_prefix(input_folder):
    # Define the folder mapping based on the first two letters of the filename
    folder_mapping = {
        '01': 'textbooks',
        '02': 'newspapers',
        '03': 'magazines',
        '04': 'question_papers',
        '05': 'scientific_articles',
        '06': 'handwritten_notes'
    }

    # Loop through each file in the input folder
    for root, dirs, files in os.walk(input_folder):
        for filename in files:
            # Check if the file is a .txt file
            if filename.endswith(".txt"):
                # Get the first two letters of the filename
                prefix = filename[:2]
                
                # Get the destination folder name based on the prefix
                dest_folder_name = folder_mapping.get(prefix, 'others')

                # Create the destination folder path
                dest_folder = os.path.join(root, dest_folder_name)
                
                # If the destination folder doesn't exist, create it
                if not os.path.exists(dest_folder):
                    os.makedirs(dest_folder)
                
                # Define the source and destination file paths
                src_file = os.path.join(root, filename)
                dest_file = os.path.join(dest_folder, filename)
                
                # Move the file to the destination folder
                shutil.move(src_file, dest_file)
    
    print(f"Files have been classified into subfolders based on their prefixes.")

# Example usage

create_folders_and_save_bbox(json_file_path, input_folder)