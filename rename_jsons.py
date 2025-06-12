import os
import shutil

# Language to code mapping
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

def process_json_files(input_folder):
    if not os.path.isdir(input_folder):
        print("Invalid folder path.")
        return

    for filename in os.listdir(input_folder):
        if filename.endswith(".json"):
            parts = filename.split("_", 1)
            if len(parts) != 2:
                print(f"Skipping malformed filename: {filename}")
                continue

            lang_name = parts[0].lower()
            rest = parts[1]

            lang_code = lang_map.get(lang_name)
            if not lang_code:
                print(f"Unknown language: {lang_name} in file {filename}")
                continue

            new_filename = f"{lang_code}_{rest}"
            src_path = os.path.join(input_folder, filename)

            lang_folder = os.path.join(input_folder, lang_code)
            os.makedirs(lang_folder, exist_ok=True)

            dest_path = os.path.join(lang_folder, new_filename)
            shutil.move(src_path, dest_path)

            print(f"Moved and renamed: {filename} → {lang_code}/{new_filename}")

# Example usage
input_folder_path = "output_jsons"
process_json_files(input_folder_path)
