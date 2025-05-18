import os
import csv

def extract_texts_from_csv_folder(input_folder, output_folder):
    """
    Extracts text from the 'Original' or 'sentences' column in each CSV file from the input folder,
    and saves each output as a .txt file in the output folder with the same base name.
    
    The script first tries to use the 'Original' column if it exists.
    If not, it looks for the 'sentences' column.
    
    Args:
        input_folder (str): Path to the folder containing input CSV files.
        output_folder (str): Path to the folder to save output text files.
    """
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    for filename in os.listdir(input_folder):
        if filename.lower().endswith('.csv'):
            input_csv_path = os.path.join(input_folder, filename)
            output_txt_name = os.path.splitext(filename)[0] + '.txt'
            output_txt_path = os.path.join(output_folder, output_txt_name)

            try:
                with open(input_csv_path, mode='r', encoding='utf-8') as csv_file:
                    csv_reader = csv.DictReader(csv_file)
                    # Determine which column to use
                    if 'Original' in csv_reader.fieldnames:
                        text_column = 'Original'
                    elif 'Sentence' in csv_reader.fieldnames:
                        text_column = 'Sentence'
                    else:
                        print(f"[SKIPPED] '{filename}' does not have 'Original' or 'sentences' column.")
                        continue

                    with open(output_txt_path, mode='w', encoding='utf-8') as txt_file:
                        for row in csv_reader:
                            txt_file.write(row[text_column] + '\n')

                print(f"[DONE] Extracted from '{filename}' → '{output_txt_name}' using column '{text_column}'.")
            except Exception as e:
                print(f"[ERROR] Failed to process '{filename}': {e}")

# Example usage:
input_folder_path = "input_csvs"       # Folder containing CSV files
output_folder_path = "output_texts"      # Folder to save TXT files

extract_texts_from_csv_folder(input_folder_path, output_folder_path)
