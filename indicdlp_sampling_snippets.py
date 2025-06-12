import os
import cv2

# langs_list = ['mr', 'bn', 'pa', 'or', 'ta', 'te', 'kn', 'ml']
langs_list = ['gu']

for lang in langs_list:
    img_dir = f'/root/Pager/sample_{lang}'
    label_dir = os.path.join(img_dir, 'labels')
    output_dir = f'/root/Pager/sample_{lang}_snippets'

    os.makedirs(output_dir, exist_ok=True)

    img_files = [f for f in os.listdir(img_dir) if f.endswith(('.png', '.jpg', '.jpeg'))]

    for img_file in img_files:
        img_path = os.path.join(img_dir, img_file)
        label_path = os.path.join(label_dir, os.path.splitext(img_file)[0] + '.txt')

        if not os.path.exists(label_path):
            continue

        img = cv2.imread(img_path)
        if img is None:
            print(f"Error reading image: {img_path}")
            continue

        h, w, _ = img.shape

        with open(label_path, 'r') as f:
            lines = f.readlines()

        for idx, line in enumerate(lines):
            parts = line.strip().split()
            if len(parts) != 5:
                print(f"Skipping malformed line in {label_path}: {line.strip()}")
                continue

            try:
                _, cx, cy, bw, bh = map(float, parts)
            except:
                print(f"Skipping non-numeric line in {label_path}: {line.strip()}")
                continue

            if bw <= 0 or bh <= 0:
                print(f"Skipping invalid bbox in {label_path}, line {idx}: bw={bw}, bh={bh}")
                continue

            x1 = int((cx - bw / 2) * w)
            y1 = int((cy - bh / 2) * h)
            x2 = int((cx + bw / 2) * w)
            y2 = int((cy + bh / 2) * h)

            x1, y1 = max(x1, 0), max(y1, 0)
            x2, y2 = min(x2, w - 1), min(y2, h - 1)

            if y2 <= y1 or x2 <= x1:
                print(f"Skipping invalid crop in {img_file}, box {idx}")
                continue

            snippet = img[y1:y2, x1:x2]

            if snippet is None or snippet.size == 0:
                print(f"Skipping empty snippet in {img_file}, box {idx}")
                continue

            snippet_name = f"{os.path.splitext(img_file)[0]}_{idx}.png"
            cv2.imwrite(os.path.join(output_dir, snippet_name), snippet)

    print(f"Done processing language: {lang}")
