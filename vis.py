import json
import os
from PIL import Image, ImageDraw

def draw_coco_boxes_single_normalized(json_path, image_path, output_path):
    """
    Draws main bounding boxes (red) and textline boxes (blue) from a COCO JSON file on a single image,
    normalizing bounding box coordinates to image dimensions and scaling them back for drawing.
    
    Args:
        json_path (str): Path to the COCO JSON file.
        image_path (str): Path to the image file.
        output_path (str): Path to save the annotated image.
    """
    # Load JSON file
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            coco_data = json.load(f)  # Fixed: use json.load() instead of json.loads()
    except Exception as e:
        print(f"Error loading JSON file {json_path}: {e}")
        return

    # Check if image exists
    if not os.path.exists(image_path):
        print(f"Image not found: {image_path}")
        return

    # Load image and get dimensions
    try:
        img = Image.open(image_path).convert('RGB')
        img_width, img_height = img.size
    except Exception as e:
        print(f"Error loading image {image_path}: {e}")
        return

    draw = ImageDraw.Draw(img)

    # Get image ID and dimensions from JSON
    image_info = coco_data.get('images', [{}])[0]
    image_id = image_info.get('id')
    json_img_width = image_info.get('width', img_width)  # Use JSON width if available
    json_img_height = image_info.get('height', img_height)  # Use JSON height if available

    # Find annotations for this image
    annotations = [ann for ann in coco_data.get('annotations', []) if ann['image_id'] == image_id]

    print(f"Found {len(annotations)} annotations for image ID: {image_id}")

    # Draw bounding boxes
    for ann in annotations:
        # Normalize main bounding box (x, y, w, h) to [0, 1]
        main_bbox = ann['bbox']
        x1, y1, w, h = main_bbox
        norm_x1 = x1 / json_img_width
        norm_y1 = y1 / json_img_height
        norm_w = w / json_img_width
        norm_h = h / json_img_height

        # Scale normalized coordinates to actual image dimensions
        scaled_x1 = norm_x1 * img_width
        scaled_y1 = norm_y1 * img_height
        scaled_w = norm_w * img_width
        scaled_h = norm_h * img_height

        # # Draw main bounding box (red, thicker line)
        # draw.rectangle(
        #     [scaled_x1, scaled_y1, scaled_x1 + scaled_w, scaled_y1 + scaled_h],
        #     outline='red',
        #     width=3
        # )

        # Normalize and draw textline boxes (blue, thinner line)
        textlines = ann.get('textlines', [])
        print(f"Drawing {len(textlines)} textlines for annotation {ann.get('id')}")
        
        for textline in textlines:
            tl_bbox = textline['bbox']
            tl_x1, tl_y1, tl_w, tl_h = tl_bbox
            norm_tl_x1 = tl_x1 / json_img_width
            norm_tl_y1 = tl_y1 / json_img_height
            norm_tl_w = tl_w / json_img_width
            norm_tl_h = tl_h / json_img_height

            # Scale normalized coordinates to actual image dimensions
            scaled_tl_x1 = norm_tl_x1 * img_width
            scaled_tl_y1 = norm_tl_y1 * img_height
            scaled_tl_w = norm_tl_w * img_width
            scaled_tl_h = norm_tl_h * img_height

            draw.rectangle(
                [scaled_tl_x1, scaled_tl_y1, scaled_tl_x1 + scaled_tl_w, scaled_tl_y1 + scaled_tl_h],
                outline='blue',
                width=1
            )

    # Save annotated image
    try:
        img.save(output_path)
        print(f"Saved annotated image: {output_path}")
    except Exception as e:
        print(f"Error saving annotated image {output_path}: {e}")

if __name__ == "__main__":
    # Fixed: Corrected the variable names and paths
    JSON_PATH = "output_jsons/bengali_ar_bn_000854_1.json"  # Path to your JSON file
    IMAGE_PATH = "synthgen_v3/Tex_files_bengali/ar_bn_000854_1.png"  # Path to your image
    OUTPUT_PATH = "mg_as_000007_0_annotated.png"  # Path to save annotated image

    # Fixed: Corrected the parameter order
    draw_coco_boxes_single_normalized(JSON_PATH, IMAGE_PATH, OUTPUT_PATH)