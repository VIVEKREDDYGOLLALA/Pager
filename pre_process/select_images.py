import os
import shutil

def process_bbox_and_images(bbox_folder, images_folder, output_folder):
    # Ensure the output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # Traverse subfolders in bbox_folder
    for subfolder, _, files in os.walk(bbox_folder):
        for file in files:
            if file.endswith(".txt"):
                # Remove `_imageid` from the bbox file name
                original_bbox_name = os.path.splitext(file)[0]
                modified_bbox_name = "_".join(original_bbox_name.split("_")[:-1])
                
                # Match bbox name to corresponding image in images_folder
                image_name = modified_bbox_name + ".jpg"  # Assuming images are in .jpg format
                image_path = os.path.join(images_folder, image_name)
                
                # Save matching image files to the output folder
                if os.path.exists(image_path):
                    # Copy image file
                    output_image_path = os.path.join(output_folder, os.path.basename(image_path))
                    shutil.copy(image_path, output_image_path)
                    print(f"Copied: {image_path} to {output_folder}")
                else:
                    print(f"Image not found for bbox file: {file}")

# Example usage
bbox_folder = "M6Doc/BBOX_val"
images_folder = "M6Doc/images_val1"
output_folder = "M6Doc/selected_images"
process_bbox_and_images(bbox_folder, images_folder, output_folder)
