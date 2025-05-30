import requests
import os
import time
from requests.exceptions import JSONDecodeError

# Create a directory to store the text files
output_dir = "sangraha_languages_1000"
os.makedirs(output_dir, exist_ok=True)

# List of all 23 language splits
languages = [
    "asm", "ben", "brx", "doi", "eng", "gom", "guj", "hin", "kan", "kas",
    "mai", "mal", "mar", "mni", "nep", "ori", "pan", "san", "sat", "snd",
    "tam", "tel", "urd"
]

# Base URL and parameters for the API
base_url = "https://datasets-server.huggingface.co/rows"
target_lines_per_language = 100
lines_per_request = 100

# Process each language
for lang in languages:
    print(f"Processing language: {lang}...")
    
    # Define the output file for this language
    output_file = os.path.join(output_dir, f"{lang}.txt")
    
    # Skip if the file already exists (to resume after failure)
    if os.path.exists(output_file):
        print(f"File for {lang} already exists, skipping...")
        continue
    
    # Parameters for the rows API
    params = {
        "dataset": "ai4bharat/sangraha",
        "config": "verified",
        "split": lang,
        "length": lines_per_request
    }
    
    lines_collected = 0
    offset = 0
    
    # Open the output file for this language
    with open(output_file, "w", encoding="utf-8") as f:
        while lines_collected < target_lines_per_language:
            params["offset"] = offset
            print(f"Fetching rows {offset} to {offset + params['length'] - 1} for {lang}...")
            
            # Make the API request with retry logic
            for attempt in range(3):  # Retry up to 3 times
                try:
                    response = requests.get(base_url, params=params)
                    
                    # Check for rate limit (429) or server errors (e.g., 502)
                    if response.status_code == 200:
                        break
                    elif response.status_code == 429:
                        print(f"Rate limit hit for {lang} at offset {offset}. Retrying in 10 seconds...")
                        time.sleep(10)  # Wait longer for rate limit
                    elif response.status_code >= 500:  # Server errors (e.g., 502)
                        print(f"Server error ({response.status_code}) for {lang} at offset {offset}. Retrying in 5 seconds...")
                        time.sleep(5)  # Wait for server issues
                    else:
                        print(f"Failed to fetch rows for {lang} at offset {offset}. Status code: {response.status_code}")
                        break
                except requests.RequestException as e:
                    print(f"Request failed for {lang} at offset {offset}: {e}. Retrying in 5 seconds...")
                    time.sleep(5)
            else:
                print(f"Failed to fetch rows for {lang} after retries. Moving to next language.")
                break
            
            # Parse the response as JSON
            try:
                data = response.json()
            except JSONDecodeError as e:
                print(f"JSON decode error for {lang} at offset {offset}: {e}")
                print(f"Response content: {response.text}")
                print("Skipping this batch...")
                break
            
            rows = data.get("rows", [])
            
            if not rows:
                print(f"No more rows available for {lang}. Total collected: {lines_collected}")
                break
            
            for row in rows:
                text = row["row"]["text"]
                f.write(text + "\n")
                lines_collected += 1
                
                if lines_collected >= target_lines_per_language:
                    break
            
            offset += params["length"]
            time.sleep(2)  # Delay between requests to avoid rate limiting
    
    print(f"Saved {lines_collected} text lines for language {lang} to {output_file}")

print("Completed downloading for all languages.")