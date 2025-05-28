import json

# Load the input JSON
with open("input_jsons/novels/Odia_Novels_4341.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# COCO output structure
coco_output = {
    "info": {
        "description": "Ai4B Dataset",
        "url": "",
        "version": "1.0",
        "year": 2025,
        "contributor": "Ai4Bharat OCR Team",
        "date_created": "2025-05-22"
    },
    "licenses": [
        {
            "id": 1,
            "name": "CC BY-NC-SA 4.0",
            "url": "https://creativecommons.org/licenses/by-nc-sa/4.0/"
        }
    ],
    "images": [],
    "annotations": [],
    "categories": []
}

category_map = {}
existing_ann_ids = set()

for item in data:
    # Skip if result is missing or empty
    if not item.get("annotations") or not item["annotations"][0].get("result"):
        continue

    image_id = item["annotations"][0]["id"]
    results = item["annotations"][0]["result"]
    image_url = item["data"].get("image_url", f"image_{image_id}.png")

    # Use dimensions from any result (all should be same)
    width = results[0]["original_width"]
    height = results[0]["original_height"]
    file_name = image_url.split("/")[-1]

    # Add image entry
    coco_output["images"].append({
        "id": image_id,
        "image_name": file_name,
        "width": width,
        "height": height,
        "license": 1,
        "flickr_url": "",
        "image_url": image_url,
        "date_captured": ""
    })

    for ann in results:
        if ann["type"] != "rectangle":
            continue  # skip non-rectangle annotations

        ann_id = ann["id"]
        if ann_id in existing_ann_ids:
            continue
        existing_ann_ids.add(ann_id)

        val = ann["value"]
        x_norm = val["x"]
        y_norm = val["y"]
        w_norm = val["width"]
        h_norm = val["height"]
        label = val["labels"][0] if val["labels"] else "undefined"

        # Convert to pixel values
        x = x_norm * width / 100
        y = y_norm * height / 100
        w = w_norm * width / 100
        h = h_norm * height / 100
        area = w * h

        # Register category
        if label not in category_map:
            category_id = len(category_map) + 1
            category_map[label] = category_id
            coco_output["categories"].append({
                "id": category_id,
                "name": label,
                "supercategory": "text"
            })

        coco_output["annotations"].append({
            "id": ann_id,
            "image_id": image_id,
            "category_id": category_map[label],
            "bbox": [x, y, w, h],
            "area": area,
            "iscrowd": 0,
            "segmentation": [],
            "attributes": {
                "rotation": val.get("rotation", 0),
                "text": val.get("text", "")
            }
        })

# Save COCO JSON
with open("coco_output.json", "w", encoding="utf-8") as f:
    json.dump(coco_output, f, indent=2, ensure_ascii=False)

print("✅ COCO format JSON saved as 'coco_output.json'")
