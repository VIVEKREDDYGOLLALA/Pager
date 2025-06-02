import os
import pandas as pd
import re

base_folder = "sangraha/sangraha/verified"
output_folder = "input_texts"
os.makedirs(output_folder, exist_ok=True)

TARGET_LINES_PER_LANG = 5_000_000

def extract_text_from_parquet(parquet_file, output_file, current_line_count):
    df = pd.read_parquet(parquet_file)

    if 'text' not in df.columns:
        print(f"'text' column not found in {parquet_file}")
        return current_line_count, True

    with open(output_file, "a", encoding="utf-8") as f:
        for line in df['text'].dropna().astype(str):
            if current_line_count >= TARGET_LINES_PER_LANG:
                return current_line_count, True
            f.write(line.strip() + "\n")
            current_line_count += 1

    return current_line_count, False

def extract_file_number(filename):
    # Extract number from filename like data-0.parquet
    match = re.search(r'data-(\d+)\.parquet$', filename)
    if match:
        return int(match.group(1))
    else:
        return float('inf')  # Put non-matching files at the end

def main():
    for lang_folder in os.listdir(base_folder):
        lang_path = os.path.join(base_folder, lang_folder)
        if not os.path.isdir(lang_path):
            continue
        
        print(f"Processing language: {lang_folder}")
        output_file = os.path.join(output_folder, f"{lang_folder}.txt")

        if os.path.exists(output_file):
            with open(output_file, "r", encoding="utf-8") as f:
                current_line_count = sum(1 for _ in f)
            if current_line_count >= TARGET_LINES_PER_LANG:
                print(f"{lang_folder} already reached target lines ({current_line_count}). Skipping.")
                continue
            else:
                print(f"{lang_folder} existing line count: {current_line_count}. Resuming...")
        else:
            current_line_count = 0

        # Sort parquet files by their number suffix
        parquet_files = [f for f in os.listdir(lang_path) if f.endswith(".parquet")]
        parquet_files.sort(key=extract_file_number)

        finished = False
        for filename in parquet_files:
            parquet_file = os.path.join(lang_path, filename)
            print(f"  Extracting from {filename} (lines so far: {current_line_count})")
            current_line_count, finished = extract_text_from_parquet(parquet_file, output_file, current_line_count)
            if finished:
                print(f"{lang_folder} reached {TARGET_LINES_PER_LANG} lines. Stopping extraction.")
                break

        print(f"Finished {lang_folder} with {current_line_count} lines saved.\n")

if __name__ == "__main__":
    main()
