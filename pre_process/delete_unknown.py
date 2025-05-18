import os
import re

def process_txt_files(folder_path):
    if not os.path.exists(folder_path):
        print(f"Folder '{folder_path}' does not exist.")
        return
    
    for file_name in os.listdir(folder_path):
        if file_name.endswith('.txt'):
            file_path = os.path.join(folder_path, file_name)
            print(f"Processing {file_name}...")
            
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
            
            # Preserve the first line (dimensions) and remove lines containing "unknown"
            filtered_lines = [lines[0]] + [line for line in lines[1:] if 'unknown' not in line]
            
            with open(file_path, 'w', encoding='utf-8') as file:
                file.writelines(filtered_lines)
            
            print(f"Updated {file_name}, removed {len(lines) - len(filtered_lines)} entries.")

# Example usage
folder_path = r'BBOX' 
process_txt_files(folder_path)