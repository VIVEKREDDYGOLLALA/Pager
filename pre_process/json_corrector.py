import os
import json

def process_json_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    modified = False
    
    for annotation in data.get("annotations", []):
        if annotation.get("label") == "paragraph":
            for line in annotation.get("textlines", []):
                if line.get("line_idx") == 1:
                    words = line["text"].split()
                    if len(words) > 1:
                        words.pop(-2)  # Remove the second-to-last word
                        line["text"] = " ".join(words)
                        modified = True
            
            # Update the "text" field with the merged text lines
            annotation["text"] = " ".join(line["text"] for line in annotation.get("textlines", []))

    if modified:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

def process_json_folder(folder_path):
    for filename in os.listdir(folder_path):
        if filename.endswith(".json"):
            file_path = os.path.join(folder_path, filename)
            process_json_file(file_path)

# Example usage
folder_path = "synthetic_documents/research_papers/santhali/output_jsons_santhali_rps"  # Change this to your actual folder path
process_json_folder(folder_path)
