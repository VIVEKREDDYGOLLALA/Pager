import os
import json
import cv2

img_dir = '/root/Pager/sample_hi'
json_dir = '/root/Pager/sample_hi_coco_jsons'
output_dir = '/root/Pager/sample_hi_visualizations'
os.makedirs(output_dir, exist_ok=True)

json_files = [f for f in os.listdir(json_dir) if f.endswith('.json')]

for jf in json_files:
    json_path = os.path.join(json_dir, jf)
    with open(json_path, 'r') as f:
        data = json.load(f)

    img_name = data['images'][0]['file_name']
    img_path = os.path.join(img_dir, img_name)
    img = cv2.imread(img_path)

    for ann in data['annotations']:
        x, y, w, h = map(int, ann['bbox'])
        ann_id = ann['id']
        label = ann['category_name']

        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
        text = f"{ann_id}: {label}"
        cv2.putText(img, text, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA)

    output_path = os.path.join(output_dir, img_name)
    cv2.imwrite(output_path, img)
    print(f"Saved visualization to {output_path}")
