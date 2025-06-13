import os
import re

# Define mapping from language name to language code
lang_map = {
    "assamese": "as",
    "bengali": "bn",
    "gujarati": "gu",
    "hindi": "hi",
    "kannada": "kn",
    "malayalam": "ml",
    "marathi": "mr",
    "odia": "or",
    "punjabi": "pa",
    "tamil": "ta",
    "telugu": "te",
    "urdu": "ur",
    "english": "en",
    "konkani": "ko",
    "maithili": "mt",
    "sanskrit": "sa",
    "nepali": "ne",
    "sindhi": "sd",
    "bodo": "bd",
    "dogri": "dg",
    # Add more if needed
}

def rename_png_files(root_folder):
    if not os.path.isdir(root_folder):
        print("Invalid folder path.")
        return

    for subfolder in os.listdir(root_folder):
        match = re.match(r'Tex_files_(\w+)', subfolder)
        if match:
            lang_name = match.group(1).lower()
            lang_code = lang_map.get(lang_name)
            if not lang_code:
                print(f"Language '{lang_name}' not found in mapping. Skipping...")
                continue

            subfolder_path = os.path.join(root_folder, subfolder)
            for file in os.listdir(subfolder_path):
                if file.endswith(".png"):
                    old_path = os.path.join(subfolder_path, file)
                    new_name = f"{lang_code}_{file}"
                    new_path = os.path.join(subfolder_path, new_name)
                    os.rename(old_path, new_path)
                    print(f"Renamed: {file} → {new_name}")

# Example usage
folder_path = "synthgen_v5"
rename_png_files(folder_path)
