import os
import shutil
import json

def copy_position_json_files(input_folder, output_folder):
    # Ensure the output folder exists
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # Walk through the input folder and its subfolders
    for root, _, files in os.walk(input_folder):
        for file in files:
            if file.endswith("position.json"):
                # Construct full file paths
                input_file_path = os.path.join(root, file)
                output_file_path = os.path.join(output_folder, file)
                
                try:
                    # Verify if the file is a valid JSON
                    with open(input_file_path, 'r') as f:
                        json.load(f)  # Attempt to parse JSON
                        
                    # Copy the file to the output folder
                    shutil.copy2(input_file_path, output_file_path)
                    print(f"Copied: {input_file_path} to {output_file_path}")
                except json.JSONDecodeError:
                    print(f"Error: {input_file_path} is not a valid JSON file")
                except Exception as e:
                    print(f"Error copying {input_file_path}: {str(e)}")

if __name__ == "__main__":
    # Define input and output folders
    input_folder = "synthgen_jsons"  # Replace with your input folder path
    output_folder = "output_jsons"# Replace with your output folder path
    
    copy_position_json_files(input_folder, output_folder)