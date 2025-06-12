import os
import ast

def is_valid_dimension(line):
    try:
        data = ast.literal_eval(line.strip())
        return isinstance(data, list) and len(data) == 2 and all(isinstance(x, (int, float)) for x in data)
    except Exception:
        return False

def delete_invalid_bbox_files(folder_path):
    if not os.path.isdir(folder_path):
        print("Invalid folder path.")
        return

    for filename in os.listdir(folder_path):
        if filename.endswith(".txt"):
            file_path = os.path.join(folder_path, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    first_line = file.readline()
                    if not is_valid_dimension(first_line):
                        os.remove(file_path)
                        print(f"Deleted invalid BBOX file: {filename}")
            except Exception as e:
                print(f"Error reading {filename}: {e}")

# Example usage
folder_path = "BBOX_0"
delete_invalid_bbox_files(folder_path)
