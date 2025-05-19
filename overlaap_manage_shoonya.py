import os
import re

def parse_bbox_line(line):
    line = line.strip()
    pattern = re.compile(r'\[([^,]+), \[([0-9.]+), ([0-9.]+), ([0-9.]+), ([0-9.]+)\], ([^,]+), ([0-9]+)\]')
    match = pattern.match(line)

    if not match:
        raise ValueError(f"Line does not match expected format: {line}")

    label = match.group(1).strip()
    x1 = float(match.group(2))
    y1 = float(match.group(3))
    width = float(match.group(4))
    height = float(match.group(5))
    annotation_id = match.group(6).strip()
    image_id = match.group(7)

    return (label, x1, y1, width, height, annotation_id, image_id)

def parse_image_size(line):
    line = line.strip().strip('[]')
    parts = line.split(',')
    if len(parts) != 2:
        raise ValueError(f"Image size line does not match expected format: {line}")
    width = float(parts[0].strip())
    height = float(parts[1].strip())
    return width, height

def is_overlapping(box1, box2):
    x1_1, y1_1, x2_1, y2_1 = box1[1], box1[2], box1[1] + box1[3], box1[2] + box1[4]
    x1_2, y1_2, x2_2, y2_2 = box2[1], box2[2], box2[1] + box2[3], box2[2] + box2[4]

    return not (x2_1 <= x1_2 or x1_1 >= x2_2 or y2_1 <= y1_2 or y1_1 >= y2_2)

def compute_intersection(box1, box2):
    x1_1, y1_1, x2_1, y2_1 = box1[1], box1[2], box1[1] + box1[3], box1[2] + box1[4]
    x1_2, y1_2, x2_2, y2_2 = box2[1], box2[2], box2[1] + box2[3], box2[2] + box2[4]

    xi1 = max(x1_1, x1_2)
    yi1 = max(y1_1, y1_2)
    xi2 = min(x2_1, x2_2)
    yi2 = min(y2_1, y2_2)

    if xi1 < xi2 and yi1 < yi2:
        return (xi1, yi1, xi2 - xi1, yi2 - yi1)
    return None

def segment_box(box, intersection):
    x1, y1, width, height = box[1], box[2], box[3], box[4]
    ix1, iy1, iwidth, iheight = intersection

    segments = []
    label = box[0]
    annotation_id = box[5]
    image_id = box[6]

    if iy1 > y1:  # Top segment
        segments.append((label, x1, y1, width, iy1 - y1, annotation_id, image_id))

    bottom_y = iy1 + iheight
    if y1 + height > bottom_y:  # Bottom segment
        segments.append((label, x1, bottom_y, width, (y1 + height) - bottom_y, annotation_id, image_id))

    if ix1 > x1:  # Left segment
        segments.append((label, x1, max(y1, iy1), ix1 - x1, min(iheight, height), annotation_id, image_id))

    right_x = ix1 + iwidth
    if x1 + width > right_x:  # Right segment
        segments.append((label, right_x, max(y1, iy1), (x1 + width) - right_x, min(iheight, height), annotation_id, image_id))

    return segments

def handle_overlapping_boxes(bbox_details):
    result_boxes = []
    ignored_labels = {"header", "footer"}

    for i, box1 in enumerate(bbox_details):
        if box1[0].lower() in ignored_labels:
            result_boxes.append(box1)
            continue

        for box2 in bbox_details[i + 1:]:
            if box2[0].lower() in ignored_labels:
                result_boxes.append(box2)
                continue

            if is_overlapping(box1, box2):
                intersection = compute_intersection(box1, box2)
                if intersection:
                    result_boxes.extend(segment_box(box1, intersection))
                    result_boxes.extend(segment_box(box2, intersection))
        else:
            result_boxes.append(box1)

    return result_boxes

def remove_duplicates(boxes):
    seen = set()
    unique_boxes = []
    for box in boxes:
        box_tuple = tuple(box)
        if box_tuple not in seen:
            seen.add(box_tuple)
            unique_boxes.append(box)
    return unique_boxes

def process_bboxes(file_path):
    try:
        with open(file_path, 'r') as file:
            lines = [line.strip() for line in file.readlines() if line.strip()]

        if not lines:
            return

        image_size_line = lines[0]
        try:
            image_width, image_height = parse_image_size(image_size_line)
        except ValueError as e:
            print(f"Warning: {e}")
            return

        bbox_details = []
        for line in lines[1:]:
            try:
                bbox_details.append(parse_bbox_line(line))
            except ValueError as e:
                print(f"Warning: {e}")
                continue

        segmented_boxes = handle_overlapping_boxes(bbox_details)
        filtered_boxes = remove_small_boxes(segmented_boxes)
        final_boxes = remove_duplicates(filtered_boxes)

        with open(file_path, 'w') as file:
            file.write(f"[{image_width}, {image_height}]\n")
            for box in final_boxes:
                file.write(f"[{box[0]}, [{box[1]}, {box[2]}, {box[3]}, {box[4]}], {box[5]}, {box[6]}]\n")

    except Exception as e:
        print(f"Error processing {file_path}: {e}")

def process_all_bboxes(base_folder):
    for root, dirs, files in os.walk(base_folder):
        for file in files:
            if file.endswith('.txt'):
                file_path = os.path.join(root, file)
                print(f"Processing: {file_path}")
                process_bboxes(file_path)

def remove_small_boxes(bboxes, min_height=15):
    return [box for box in bboxes if box[4] >= min_height]

base_folder = r'BBOX'
process_all_bboxes(base_folder)
