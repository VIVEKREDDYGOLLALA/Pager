import json
from collections import defaultdict

def transform_json(input_file, output_file):
    # Read the input JSON file
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Group data by 'element_type'
    transformed_data = defaultdict(list)
    
    for entry in data:
        element_type = entry.get("element_type")
        text = entry.get("text", "")
        if element_type and text:
            transformed_data[element_type].append(text)
    
    # Convert defaultdict to a normal dictionary
    transformed_data = dict(transformed_data)
    
    # Write the transformed data to an output JSON file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(transformed_data, f, ensure_ascii=False, indent=2)

# Example usage
input_file = "jsno1.json"  # Replace with actual input file
output_file = "json2.json"  # Replace with desired output file
transform_json(input_file, output_file)
