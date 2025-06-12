import os
import json
import re
import base64
import requests
from natsort import natsorted
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

# ------------------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------------------
load_dotenv()
API_KEY = "AIzaSyAgSDU8KHxadMtqhhtocqV19Yv1tCbukkI"  # Or use: os.getenv("GCLOUD_VISION_API_KEY")

# ------------------------------------------------------------------------------
# Utility Functions
# ------------------------------------------------------------------------------
def get_bbox_coords(bbox):
    xs = [v.get("x", 0) for v in bbox]
    ys = [v.get("y", 0) for v in bbox]
    return min(xs), min(ys), max(xs), max(ys)

def compute_iou(b1, b2):
    x1, y1, x2, y2 = max(b1[0], b2[0]), max(b1[1], b2[1]), min(b1[2], b2[2]), min(b1[3], b2[3])
    if x2 < x1 or y2 < y1: return 0.0
    inter = (x2 - x1) * (y2 - y1)
    area1 = (b1[2] - b1[0]) * (b1[3] - b1[1])
    area2 = (b2[2] - b2[0]) * (b2[3] - b2[1])
    union = area1 + area2 - inter
    return inter / union if union else 0.0

def filter_inner_boxes(blocks, key="boundingBox"):
    filtered = []
    for i, b1 in enumerate(blocks):
        c1 = get_bbox_coords(b1.get(key, []))
        if not any(i != j and all(c1[k] >= get_bbox_coords(b2.get(key, []))[k] for k in (0, 1)) and
                   all(c1[k] <= get_bbox_coords(b2.get(key, []))[k] for k in (2, 3)) for j, b2 in enumerate(blocks)):
            filtered.append(b1)
    return filtered

def sort_reading_order(items):
    return sorted(items, key=lambda b: (get_bbox_coords(b["boundingBox"])[1], get_bbox_coords(b["boundingBox"])[0]))

def extract_page_number(filename):
    m = re.search(r'(\d+)', os.path.splitext(filename)[0])
    return int(m.group(1)) if m else 1

# ------------------------------------------------------------------------------
# OCR and Conversion Logic
# ------------------------------------------------------------------------------
def perform_ocr(image_path, output_path, language_hints):
    try:
        with open(image_path, "rb") as f:
            img_base64 = base64.b64encode(f.read()).decode()

        payload = {
            "requests": [{
                "image": {"content": img_base64},
                "features": [{"type": "DOCUMENT_TEXT_DETECTION"}],
                "imageContext": {"languageHints": language_hints}
            }]
        }

        r = requests.post(f"https://vision.googleapis.com/v1/images:annotate?key={API_KEY}", json=payload)
        r.raise_for_status()
        result = r.json()["responses"][0]

        full_text = result.get("fullTextAnnotation", {})
        blocks = []

        for page in full_text.get("pages", []):
            for b in page.get("blocks", []):
                block_box = b.get("boundingBox", {}).get("vertices", [])
                block_conf = b.get("confidence", None)
                lines = []
                text = ""
                for p in b.get("paragraphs", []):
                    para_box = p.get("boundingBox", {}).get("vertices", [])
                    para_text = " ".join("".join(s.get("text", "") for s in w.get("symbols", [])) for w in p.get("words", []))
                    lines.append({"text": para_text, "boundingBox": para_box, "confidence": p.get("confidence", None)})
                    text += para_text + " "
                blocks.append({"text": text.strip(), "boundingBox": block_box, "confidence": block_conf, "lines": lines})

        blocks = filter_inner_boxes(blocks)
        for b in blocks:
            b["lines"] = filter_inner_boxes(b.get("lines", []))

        lines = [l for b in blocks for l in b["lines"]]

        json.dump({
            "image_path": image_path,
            "full_text": full_text.get("text", ""),
            "blocks": blocks,
            "lines": lines
        }, open(output_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

        return f"✅ {os.path.basename(image_path)}"
    except Exception as e:
        return f"❌ {os.path.basename(image_path)} failed: {e}"

def convert_json(old_path, new_path):
    with open(old_path, "r", encoding="utf-8") as f:
        old = json.load(f)
    blocks = sort_reading_order(old.get("blocks", []))
    new = {"page_number": extract_page_number(old_path), "ocr_output": {"blocks": []}}

    for b in blocks:
        paras = sort_reading_order(b.get("lines", []))
        for p in paras:
            t = p.get("text", "").strip()
            if not t:
                continue
            new["ocr_output"]["blocks"].append({
                "block_text": t,
                "lines": [t],
                "bounding_box": p.get("boundingBox", []),
                "confidence": p.get("confidence", None)
            })

    with open(new_path, "w", encoding="utf-8") as f:
        json.dump(new, f, ensure_ascii=False, indent=2)

# ------------------------------------------------------------------------------
# Multithreaded Runner
# ------------------------------------------------------------------------------
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

def run_parallel_gcv(lang, max_workers=64):
    input_dir = f"/root/Pager/sample_{lang}_snippets"
    output_dir = f"/root/Pager/sample_{lang}_snippets_output"
    os.makedirs(output_dir, exist_ok=True)

    image_files = [f for f in os.listdir(input_dir) if f.lower().endswith((".png", ".jpg", ".jpeg"))]

    print(f"\n▶️ Processing {len(image_files)} images for language: {lang}")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(perform_ocr, os.path.join(input_dir, f),
                            os.path.join(output_dir, os.path.splitext(f)[0] + ".json"),
                            [lang]): f
            for f in image_files
        }

        for _ in tqdm(as_completed(futures), total=len(futures), desc=f"{lang.upper()} OCR"):
            pass  # silently consume

    # JSON conversion with progress
    json_files = [f for f in os.listdir(output_dir) if f.endswith(".json")]
    for jf in tqdm(json_files, desc=f"{lang.upper()} Convert"):
        in_path = os.path.join(output_dir, jf)
        convert_json(in_path, in_path)



# ------------------------------------------------------------------------------
# Main
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    # langs_list = ['mr', 'bn', 'pa', 'or', 'ta', 'te', 'kn', 'ml']
    langs_list = ['gu']
    for lang in langs_list:
        print(f"=== Running OCR for language: {lang} ===")
        run_parallel_gcv(lang)
