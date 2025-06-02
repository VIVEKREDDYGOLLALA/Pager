import os

def count_lines_in_txt_files(root_folder):
    total_lines = 0
    for dirpath, _, filenames in os.walk(root_folder):
        for filename in filenames:
            if filename.endswith(".txt"):
                file_path = os.path.join(dirpath, filename)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        line_count = sum(1 for _ in f)
                    print(f"{file_path}: {line_count} lines")
                    total_lines += line_count
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
    print(f"\nTotal lines across all .txt files: {total_lines}")

# Example usage
if __name__ == "__main__":
    folder_path = "input_texts"  # Replace with your folder path
    count_lines_in_txt_files(folder_path)
