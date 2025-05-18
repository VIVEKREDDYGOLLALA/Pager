import os
import json
import shutil
from urllib.parse import urlparse


def extract_filename_from_url(url):
    """
    Extract the filename from a URL
    Example: "https://objectstore.e2enetworks.net/indic-ocr/as_v2/mg/mg_as_000949_1.png"
    Returns: "mg_as_000949_1.png"
    """
    parsed_url = urlparse(url)
    path = parsed_url.path
    return os.path.basename(path)


def build_id_to_filename_mapping(input_json_folder):
    """
    Build a mapping from image_id to filename from all JSON files in the input folder
    
    Args:
        input_json_folder (str): Path to the folder containing input JSON files
        
    Returns:
        dict: Mapping of image_id to filename
    """
    id_to_filename = {}
    processed_files = 0
    
    for filename in os.listdir(input_json_folder):
        if not filename.endswith('.json'):
            continue
            
        input_json_path = os.path.join(input_json_folder, filename)
        
        try:
            with open(input_json_path, 'r', encoding='utf-8') as f:
                input_data = json.load(f)
            
            # Handle both list and single object formats
            if isinstance(input_data, list):
                items = input_data
            else:
                items = [input_data]
                
            for item in items:
                item_id = item.get('id')
                image_url = item.get('data', {}).get('image_url', '')
                
                if item_id and image_url:
                    filename = extract_filename_from_url(image_url)
                    id_to_filename[str(item_id)] = filename
            
            processed_files += 1
            print(f"Processed input file: {filename}")
                
        except json.JSONDecodeError:
            print(f"Skipped input file: {filename} - Invalid JSON")
        except Exception as e:
            print(f"Error processing input file {filename}: {str(e)}")
    
    print(f"Processed {processed_files} input JSON files, found {len(id_to_filename)} mappings")
    return id_to_filename


def process_files(input_json_folder, json_folder_path, output_folder=None):
    """
    Process JSON files:
    1. Read all input JSON files from the input folder
    2. For each file in json_folder, find the corresponding entry in the mappings
    3. Rename the file based on the image_url
    
    Args:
        input_json_folder (str): Path to the folder containing input JSON files
        json_folder_path (str): Path to the folder containing JSON files to rename
        output_folder (str, optional): Path to output folder. If None, files will be renamed in place.
    """
    # Create output folder if specified and doesn't exist
    if output_folder and not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # Build mapping from all input JSON files
    id_to_filename = build_id_to_filename_mapping(input_json_folder)
    
    if not id_to_filename:
        print("No valid mappings found in input JSON files. Exiting.")
        return
    
    # Process each file in the JSON folder
    processed_count = 0
    skipped_count = 0
    
    for filename in os.listdir(json_folder_path):
        if not filename.endswith('.json'):
            continue
            
        file_path = os.path.join(json_folder_path, filename)
        
        # Read JSON file to extract ID
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                file_data = json.load(f)
                
            # Get the first annotation's image_id
            if file_data.get('annotations') and len(file_data['annotations']) > 0:
                image_id = file_data['annotations'][0].get('image_id')
                
                if image_id in id_to_filename:
                    new_filename = id_to_filename[image_id]
                    new_filename = f"{os.path.splitext(new_filename)[0]}.json"
                    
                    if output_folder:
                        new_path = os.path.join(output_folder, new_filename)
                        shutil.copy2(file_path, new_path)
                    else:
                        new_path = os.path.join(json_folder_path, new_filename)
                        # Check if the file already exists
                        if os.path.exists(new_path) and new_path != file_path:
                            print(f"Warning: File {new_filename} already exists. Skipping rename of {filename}")
                            skipped_count += 1
                            continue
                        os.rename(file_path, new_path)
                    
                    processed_count += 1
                    print(f"Renamed: {filename} -> {new_filename}")
                else:
                    skipped_count += 1
                    print(f"Skipped: {filename} - No matching ID found")
            else:
                skipped_count += 1
                print(f"Skipped: {filename} - No annotations found")
                
        except json.JSONDecodeError:
            skipped_count += 1
            print(f"Skipped: {filename} - Invalid JSON")
        except Exception as e:
            skipped_count += 1
            print(f"Error processing {filename}: {str(e)}")
    
    print(f"\nProcessing complete!")
    print(f"Files processed: {processed_count}")
    print(f"Files skipped: {skipped_count}")


# Hard-coded paths - MODIFY THESE PATHS BEFORE RUNNING
INPUT_JSON_FOLDER = "input_jsons/research_jsons"  # Path to folder containing input JSON files
JSON_FOLDER_PATH = "synthetic_documents/research_papers/santhali/output_jsons_santhali_rps"        # Path to folder containing JSON files to rename
OUTPUT_FOLDER = None                           # Set to None to rename in place, or provide a path for output

# Display configuration
print(f"Input JSON folder: {INPUT_JSON_FOLDER}")
print(f"JSON folder to process: {JSON_FOLDER_PATH}")
print(f"Output folder: {OUTPUT_FOLDER if OUTPUT_FOLDER else 'None (files will be renamed in place)'}")
print("-" * 50)

# Run the processing
process_files(INPUT_JSON_FOLDER, JSON_FOLDER_PATH, OUTPUT_FOLDER)