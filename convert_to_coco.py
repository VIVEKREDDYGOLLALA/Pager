import json
import uuid
from datetime import datetime

def convert_to_coco(input_json_path, output_json_path):
    # Load the input JSON
    with open(input_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Initialize COCO format dictionary
    coco_format = {
        "info": {
            "description": "Converted dataset from custom JSON to COCO format",
            "version": "1.0",
            "year": datetime.now().year,
            "contributor": "Grok 3",
            "date_created": datetime.now().strftime("%Y-%m-%d")
        },
        "images": [],
        "annotations": [],
        "categories": [
            {"id": 1, "name": "paragraph", "supercategory": "text"},
            {"id": 2, "name": "footnote", "supercategory": "text"}
        ],
        "licenses": [
            {"id": 1, "name": "Unknown", "url": ""}
        ]
    }
    
    # Create a set of unique image IDs
    image_ids = set(annotation['image_id'] for annotation in data['annotations'])
    
    # Populate images section
    for image_id in image_ids:
        coco_format['images'].append({
            "id": image_id,
            "file_name": f"{image_id}.jpg",  # Assuming .jpg, as no file extension is provided
            "width": 0, 
            "height": 0, 
            "license": 1,
            "date_captured": ""
        })
    
    # Populate annotations section
    annotation_id = 1
    for annotation in data['annotations']:
        image_id = annotation['image_id']
        label = annotation['label']
        category_id = 1 if label == "paragraph" else 2  # Map label to category_id
        
        for textline in annotation['textlines']:
            bbox = textline['bbox']
            # Convert bbox [x_min, y_min, width, height] to COCO format [x_min, y_min, width, height]
            coco_bbox = [bbox[0], bbox[1], bbox[2], bbox[3]]
            area = bbox[2] * bbox[3]  # width * height
            
            coco_format['annotations'].append({
                "id": annotation_id,
                "image_id": image_id,
                "category_id": category_id,
                "bbox": coco_bbox,
                "area": area,
                "iscrowd": 0,
                "text": textline['text'],
                "line_idx": textline['line_idx'],
                "annotation_id": annotation['id']  # Retain original annotation ID
            })
            annotation_id += 1
    
    # Save the COCO format JSON to a file
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(coco_format, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    input_json_path = "input_jsons/novels/Hindi_Novels_4260.json"
    output_json_path = "hindi_coco2.json"
    convert_to_coco(input_json_path, output_json_path)
    print(f"Converted JSON saved to {output_json_path}")