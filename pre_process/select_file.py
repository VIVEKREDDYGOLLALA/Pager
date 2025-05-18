import os
import random
import shutil


def select_and_copy_bboxes(base_folder, output_folder_bbox, num_files=10):
    """
    Selects `num_files` randomly from each subfolder of `base_folder` and copies them to the corresponding
    subfolder in `output_folder_bbox` with '_BBOX' added to their names.
    """
    selected_bboxes = []

    for root, _, files in os.walk(base_folder):
        bbox_files = [f for f in files if f.endswith('.txt')]  # Adjust extension if needed
        if len(bbox_files) > 0:
            selected_files = random.sample(bbox_files, min(num_files, len(bbox_files)))
            for file in selected_files:
                src_path = os.path.join(root, file)

                # Create the corresponding subfolder in output_folder_bbox
                relative_path = os.path.relpath(root, base_folder)
                output_subfolder = os.path.join(output_folder_bbox, relative_path)
                os.makedirs(output_subfolder, exist_ok=True)

                dst_file_name = f"{os.path.splitext(file)[0]}.txt"
                dst_path = os.path.join(output_subfolder, dst_file_name)
                shutil.copy(src_path, dst_path)
                selected_bboxes.append(dst_path)

    return selected_bboxes


def match_and_copy_images(bbox_folder, image_folder, output_folder_images):
    """
    Matches the names of bbox files with images (removing '_BBOX' and everything after the last underscore in bbox names),
    then copies the matched images to the corresponding subfolder in `output_folder_images`.
    """
    selected_images = []

    for root, _, files in os.walk(bbox_folder):
        bbox_files = [f for f in files if f.endswith('.txt')]  # Adjust extension if needed
        for bbox_file in bbox_files:
            # Remove '_BBOX' and everything after the last underscore
            base_name = os.path.splitext(bbox_file)[0].rsplit('_', 1)[0]

            # Find matching images in the corresponding subfolder
            relative_path = os.path.relpath(root, bbox_folder)
            image_subfolder = os.path.join(image_folder, relative_path)
            if not os.path.exists(image_subfolder):
                continue

            matching_images = [
                img for img in os.listdir(image_subfolder)
                if img.startswith(base_name)
            ]

            for img in matching_images:
                src_img_path = os.path.join(image_subfolder, img)

                # Create the corresponding subfolder in output_folder_images
                output_subfolder = os.path.join(output_folder_images, relative_path)
                os.makedirs(output_subfolder, exist_ok=True)

                dst_img_path = os.path.join(output_subfolder, img)
                shutil.copy(src_img_path, dst_img_path)
                selected_images.append(dst_img_path)

    return selected_images


def process_bboxes_and_images(base_bbox_folder1, base_bbox_folder2, output_bbox_folder1, output_bbox_folder2, 
                               image_folder, output_image_folder1, output_image_folder2, num_files=10):
    """
    Main function to process BBox files and images from two input folders.
    Ensures the output folders have files with the same names.
    """
    # Step 1: Select and copy random BBox files from both folders
    selected_bboxes1 = select_and_copy_bboxes(base_bbox_folder1, output_bbox_folder1, num_files)
    selected_bboxes2 = select_and_copy_bboxes(base_bbox_folder2, output_bbox_folder2, num_files)

    # Step 2: Get common files between the two folders to ensure same names
    common_files = set(
        os.path.basename(path) for path in selected_bboxes1
    ).intersection(
        os.path.basename(path) for path in selected_bboxes2
    )

    # Filter selected files to keep only common ones
    final_selected_bboxes1 = [
        path for path in selected_bboxes1 if os.path.basename(path) in common_files
    ]
    final_selected_bboxes2 = [
        path for path in selected_bboxes2 if os.path.basename(path) in common_files
    ]

    # Step 3: Match BBox files with images and copy matched images
    selected_images1 = match_and_copy_images(output_bbox_folder1, image_folder, output_image_folder1)
    selected_images2 = match_and_copy_images(output_bbox_folder2, image_folder, output_image_folder2)

    return final_selected_bboxes1, final_selected_bboxes2, selected_images1, selected_images2


# Example usage
if __name__ == "__main__":
    base_bbox_folder1 = r'M6Doc/BBOX_val1'
    base_bbox_folder2 = r'M6Doc/BBOX_val2'
    output_bbox_folder1 = r'M6Doc/BBOX_val'
    output_bbox_folder2 = r'M6Doc/BBOX_val_output2'
    image_folder = r'M6Doc/images_val'
    output_image_folder1 = r'M6Doc/images_val_output1'
    output_image_folder2 = r'M6Doc/images_val_output2'

    selected_bboxes1, selected_bboxes2, selected_images1, selected_images2 = process_bboxes_and_images(
        base_bbox_folder1, base_bbox_folder2, output_bbox_folder1, output_bbox_folder2,
        image_folder, output_image_folder1, output_image_folder2, num_files=10
    )

    print("Selected BBox files from Folder 1:")
    print(selected_bboxes1)

    print("\nSelected BBox files from Folder 2:")
    print(selected_bboxes2)

    print("\nMatched images for Folder 1:")
    print(selected_images1)

    print("\nMatched images for Folder 2:")
    print(selected_images2)
