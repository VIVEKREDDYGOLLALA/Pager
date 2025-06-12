import os
import json
import cv2
import re

# langs_list = ['mr', 'bn', 'pa', 'or', 'ta', 'te', 'kn', 'ml']
langs_list = ['gu']

indicdlp_labels = {
    0: "advertisement", 1: "answer", 2: "author", 3: "chapter-title", 4: "contact-info",
    5: "dateline", 6: "figure", 7: "figure-caption", 8: "first-level-question", 9: "flag",
    10: "folio", 11: "footer", 12: "footnote", 13: "formula", 14: "header", 15: "headline",
    16: "index", 17: "jumpline", 18: "options", 19: "ordered-list", 20: "page-number",
    21: "paragraph", 22: "placeholder-text", 23: "quote", 24: "reference", 25: "second-level-question",
    26: "section-title", 27: "sidebar", 28: "sub-headline", 29: "sub-ordered-list",
    30: "sub-section-title", 31: "subsub-headline", 32: "subsub-ordered-list",
    33: "subsub-section-title", 34: "subsub-unordered-list", 35: "sub-unordered-list",
    36: "table", 37: "table-caption", 38: "table-of-contents", 39: "third-level-question",
    40: "unordered-list", 41: "website-link"
}

categories_list = [{"id": cid, "name": name} for cid, name in indicdlp_labels.items()]

def get_row_id(name):
    match = re.search(r'_(\d+)\.json$', name)
    return int(match.group(1)) if match else -1

for lang in langs_list:
    img_dir = f'/root/Pager/sample_{lang}'
    label_dir = os.path.join(img_dir, 'labels')
    snippet_json_dir = f'/root/Pager/sample_{lang}_snippets_output'
    output_dir = f'/root/Pager/sample_{lang}_coco_jsons'
    os.makedirs(output_dir, exist_ok=True)

    doc_images = [f for f in os.listdir(img_dir) if f.endswith(('.png', '.jpg', '.jpeg'))]

    for image_id, img_name in enumerate(doc_images):
        img_base = os.path.splitext(img_name)[0]
        label_path = os.path.join(label_dir, img_base + '.txt')
        img_path = os.path.join(img_dir, img_name)

        if not os.path.exists(label_path):
            continue

        img = cv2.imread(img_path)
        h, w = img.shape[:2]

        with open(label_path, 'r') as f:
            lines = f.readlines()

        snippet_jsons = sorted(
            [f for f in os.listdir(snippet_json_dir) if f.startswith(img_base + '_') and f.endswith('.json')],
            key=get_row_id
        )

        annotations = []
        for ann_id, sn_json in enumerate(snippet_jsons):
            row_id = get_row_id(sn_json)
            if row_id >= len(lines):
                continue

            yolo_line = lines[row_id].strip().split()
            if len(yolo_line) != 5:
                continue

            class_id, cx, cy, bw, bh = map(float, yolo_line)
            class_id = int(class_id)

            x = (cx - bw / 2) * w
            y = (cy - bh / 2) * h
            width = bw * w
            height = bh * h

            with open(os.path.join(snippet_json_dir, sn_json), 'r') as f:
                ocr_json = json.load(f)

            text = " ".join([blk['block_text'] for blk in ocr_json.get("ocr_output", {}).get("blocks", [])])

            annotations.append({
                "id": ann_id,
                "image_id": image_id,
                "category_id": class_id,
                "category_name": indicdlp_labels.get(class_id, "unknown"),
                "bbox": [round(x, 2), round(y, 2), round(width, 2), round(height, 2)],
                "text": text
            })

        coco = {
            "images": [{
                "id": image_id,
                "file_name": img_name,
                "width": w,
                "height": h
            }],
            "annotations": annotations,
            "categories": categories_list
        }

        with open(os.path.join(output_dir, img_base + '.json'), 'w') as out_f:
            json.dump(coco, out_f, indent=2, ensure_ascii=False)
