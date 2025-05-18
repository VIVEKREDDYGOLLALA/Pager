import os

def rename_jpg_files(folder_path):
    """
    Renames JPEG files in the specified folder by removing '_0000' at the end of the file names.

    Args:
        folder_path (str): The path to the folder containing JPEG files.
    """
    if not os.path.exists(folder_path):
        print(f"Folder '{folder_path}' does not exist.")
        return

    for file_name in os.listdir(folder_path):
        # Check if the file is a JPEG file and ends with '_0000'
        if file_name.lower().endswith('.jpg') and '_0000' in file_name:
            new_name = file_name.replace('_0000', '')  # Remove '_0000'
            old_path = os.path.join(folder_path, file_name)
            new_path = os.path.join(folder_path, new_name)

            # Rename the file
            try:
                os.rename(old_path, new_path)
                print(f"Renamed: {file_name} -> {new_name}")
            except Exception as e:
                print(f"Error renaming {file_name}: {e}")

# Example usage
jpg_folder = 'output_folder19'  # Replace with your JPEG folder path
rename_jpg_files(jpg_folder)
