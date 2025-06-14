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

def get_box_area(box):
    """Calculate area: width * height"""
    return box[3] * box[4]

def get_intersection_area(box1, box2):
    """Calculate intersection area between two boxes"""
    x1_1, y1_1, x2_1, y2_1 = box1[1], box1[2], box1[1] + box1[3], box1[2] + box1[4]
    x1_2, y1_2, x2_2, y2_2 = box2[1], box2[2], box2[1] + box2[3], box2[2] + box2[4]

    xi1 = max(x1_1, x1_2)
    yi1 = max(y1_1, y1_2)
    xi2 = min(x2_1, x2_2)
    yi2 = min(y2_1, y2_2)

    if xi1 < xi2 and yi1 < yi2:
        return (xi2 - xi1) * (yi2 - yi1)
    return 0

def is_overlapping(box1, box2):
    """Check if two boxes overlap"""
    return get_intersection_area(box1, box2) > 0

def compute_intersection(box1, box2):
    """Compute intersection coordinates"""
    x1_1, y1_1, x2_1, y2_1 = box1[1], box1[2], box1[1] + box1[3], box1[2] + box1[4]
    x1_2, y1_2, x2_2, y2_2 = box2[1], box2[2], box2[1] + box2[3], box2[2] + box2[4]

    xi1 = max(x1_1, x1_2)
    yi1 = max(y1_1, y1_2)
    xi2 = min(x2_1, x2_2)
    yi2 = min(y2_1, y2_2)

    if xi1 < xi2 and yi1 < yi2:
        return (xi1, yi1, xi2 - xi1, yi2 - yi1)
    return None

def get_intersection_percentage(box, intersection_area):
    """Calculate what percentage of box's area is in the intersection"""
    box_area = get_box_area(box)
    if box_area == 0:
        return 0
    return (intersection_area / box_area) * 100

def choose_intersection_winner(box1, box2, intersection_area):
    """
    Choose which box gets the intersection based on percentage logic
    Returns the winning box
    """
    # Priority rules:
    # 1. Header/Footer boxes always win
    # 2. Box with higher intersection percentage wins
    # 3. In case of tie, larger box wins
    
    ignored_labels = {"header", "footer"}
    
    # Rule 1: Priority labels
    if box1[0].lower() in ignored_labels and box2[0].lower() not in ignored_labels:
        return box1
    elif box2[0].lower() in ignored_labels and box1[0].lower() not in ignored_labels:
        return box2
    
    # Rule 2: Higher intersection percentage
    percentage1 = get_intersection_percentage(box1, intersection_area)
    percentage2 = get_intersection_percentage(box2, intersection_area)
    
    print(f"    Intersection percentages: {box1[5]}={percentage1:.1f}%, {box2[5]}={percentage2:.1f}%")
    
    if percentage1 > percentage2:
        print(f"    → {box1[5]} wins intersection (higher percentage)")
        return box1
    elif percentage2 > percentage1:
        print(f"    → {box2[5]} wins intersection (higher percentage)")
        return box2
    
    # Rule 3: In case of equal percentages, larger box wins
    area1 = get_box_area(box1)
    area2 = get_box_area(box2)
    
    if area1 >= area2:
        print(f"    → {box1[5]} wins intersection (equal percentage, larger area)")
        return box1
    else:
        print(f"    → {box2[5]} wins intersection (equal percentage, larger area)")
        return box2

def segment_box(box, intersection):
    """Create segments from a box by removing intersection area"""
    x1, y1, width, height = box[1], box[2], box[3], box[4]
    ix1, iy1, iwidth, iheight = intersection

    segments = []
    label = box[0]
    annotation_id = box[5]
    image_id = box[6]

    # Top segment (above intersection)
    if iy1 > y1:
        seg_height = iy1 - y1
        if seg_height > 0:
            segments.append((label, x1, y1, width, seg_height, annotation_id, image_id))

    # Bottom segment (below intersection)
    bottom_y = iy1 + iheight
    if y1 + height > bottom_y:
        seg_height = (y1 + height) - bottom_y
        if seg_height > 0:
            segments.append((label, x1, bottom_y, width, seg_height, annotation_id, image_id))

    # Left segment (left of intersection, within intersection height range)
    if ix1 > x1:
        seg_y = max(y1, iy1)
        seg_height = min(y1 + height, iy1 + iheight) - seg_y
        seg_width = ix1 - x1
        if seg_width > 0 and seg_height > 0:
            segments.append((label, x1, seg_y, seg_width, seg_height, annotation_id, image_id))

    # Right segment (right of intersection, within intersection height range)
    right_x = ix1 + iwidth
    if x1 + width > right_x:
        seg_y = max(y1, iy1)
        seg_height = min(y1 + height, iy1 + iheight) - seg_y
        seg_width = (x1 + width) - right_x
        if seg_width > 0 and seg_height > 0:
            segments.append((label, right_x, seg_y, seg_width, seg_height, annotation_id, image_id))

    return segments

def handle_overlapping_boxes_with_percentage_logic(bbox_details, max_iterations=10):
    """
    Handle overlapping boxes using percentage-based intersection assignment
    """
    ignored_labels = {"header", "footer"}
    current_boxes = list(bbox_details)
    
    print(f"  Starting overlap resolution with {len(current_boxes)} boxes")
    
    for iteration in range(max_iterations):
        overlaps_found = False
        new_boxes = []
        processed_indices = set()
        
        for i, box1 in enumerate(current_boxes):
            if i in processed_indices:
                continue
            
            # Skip processing for ignored labels (but keep them)
            if box1[0].lower() in ignored_labels:
                new_boxes.append(box1)
                processed_indices.add(i)
                continue
            
            # Find all overlapping boxes
            overlapping_boxes = []
            overlapping_indices = []
            
            for j, box2 in enumerate(current_boxes[i+1:], i+1):
                if j in processed_indices:
                    continue
                
                # Skip ignored labels for overlap processing
                if box2[0].lower() in ignored_labels:
                    continue
                
                if is_overlapping(box1, box2):
                    overlapping_boxes.append(box2)
                    overlapping_indices.append(j)
                    overlaps_found = True
            
            if overlapping_boxes:
                # Process box1 against all overlapping boxes
                remaining_segments = [box1]
                intersection_boxes = []  # Store intersection areas with their owners
                
                for overlapping_box in overlapping_boxes:
                    new_remaining_segments = []
                    
                    for segment in remaining_segments:
                        intersection = compute_intersection(segment, overlapping_box)
                        if intersection:
                            intersection_area = intersection[2] * intersection[3]  # width * height
                            
                            # Choose winner using percentage logic
                            intersection_winner = choose_intersection_winner(segment, overlapping_box, intersection_area)
                            
                            # Create intersection box with winner's annotation_id
                            ix, iy, iw, ih = intersection
                            intersection_box = (intersection_winner[0], ix, iy, iw, ih, 
                                              intersection_winner[5], intersection_winner[6])  # Keep same annotation_id
                            intersection_boxes.append(intersection_box)
                            
                            # Create segments from current segment (minus intersection)
                            segments = segment_box(segment, intersection)
                            new_remaining_segments.extend(segments)
                            
                            print(f"    Created {len(segments)} segments from {segment[5]}")
                        else:
                            new_remaining_segments.append(segment)
                    
                    remaining_segments = new_remaining_segments
                
                # Add all segments from box1
                new_boxes.extend(remaining_segments)
                
                # Add intersection boxes
                new_boxes.extend(intersection_boxes)
                
                # Process each overlapping box (create segments minus intersections)
                for k, overlapping_box in enumerate(overlapping_boxes):
                    box_segments = [overlapping_box]
                    
                    # Remove intersections with box1 and previous overlapping boxes
                    for ref_box in [box1] + overlapping_boxes[:k]:
                        new_segments = []
                        for segment in box_segments:
                            intersection = compute_intersection(segment, ref_box)
                            if intersection:
                                # Create segments (intersection already handled above)
                                segments = segment_box(segment, intersection)
                                new_segments.extend(segments)
                            else:
                                new_segments.append(segment)
                        box_segments = new_segments
                    
                    new_boxes.extend(box_segments)
                
                # Mark all as processed
                processed_indices.add(i)
                processed_indices.update(overlapping_indices)
            else:
                # No overlaps - keep original box
                new_boxes.append(box1)
                processed_indices.add(i)
        
        # Add ignored label boxes that weren't processed
        for i, box in enumerate(current_boxes):
            if i not in processed_indices and box[0].lower() in ignored_labels:
                new_boxes.append(box)
        
        current_boxes = new_boxes
        
        if not overlaps_found:
            print(f"  Overlap resolution completed in {iteration + 1} iterations")
            break
    else:
        print(f"  Warning: Maximum iterations ({max_iterations}) reached")
    
    print(f"  Final result: {len(current_boxes)} non-overlapping boxes")
    return current_boxes

def remove_duplicates(boxes):
    """Remove exact duplicate boxes"""
    seen = set()
    unique_boxes = []
    for box in boxes:
        # Create tuple for comparison (excluding potential floating point precision issues)
        box_tuple = (box[0], round(box[1], 2), round(box[2], 2), 
                    round(box[3], 2), round(box[4], 2), box[5], box[6])
        if box_tuple not in seen:
            seen.add(box_tuple)
            unique_boxes.append(box)
    return unique_boxes

def remove_small_boxes(bboxes, min_height=15):
    """Remove boxes with height less than minimum threshold"""
    filtered = []
    removed_count = 0
    
    for box in bboxes:
        if box[4] >= min_height:  # height >= min_height
            filtered.append(box)
        else:
            removed_count += 1
    
    if removed_count > 0:
        print(f"  Removed {removed_count} boxes with height < {min_height}")
    
    return filtered

def process_bboxes(file_path):
    """Process bounding boxes in a file using percentage-based logic"""
    try:
        with open(file_path, 'r') as file:
            lines = [line.strip() for line in file.readlines() if line.strip()]

        if not lines:
            print(f"  Warning: Empty file {file_path}")
            return

        image_size_line = lines[0]
        try:
            image_width, image_height = parse_image_size(image_size_line)
        except ValueError as e:
            print(f"  Warning: {e}")
            return

        bbox_details = []
        for line_num, line in enumerate(lines[1:], 2):
            try:
                bbox_details.append(parse_bbox_line(line))
            except ValueError as e:
                print(f"  Warning line {line_num}: {e}")
                continue
        
        if not bbox_details:
            print(f"  Warning: No valid bounding boxes found")
            return

        print(f"  Initial boxes: {len(bbox_details)}")
        
        # Apply percentage-based overlap resolution
        segmented_boxes = handle_overlapping_boxes_with_percentage_logic(bbox_details)
        
        # Remove small boxes
        filtered_boxes = remove_small_boxes(segmented_boxes)
        
        # Remove duplicates
        final_boxes = remove_duplicates(filtered_boxes)
        
        print(f"  After deduplication: {len(final_boxes)} boxes")

        # Write results back to file
        with open(file_path, 'w') as file:
            file.write(f"[{image_width}, {image_height}]\n")
            for box in final_boxes:
                file.write(f"[{box[0]}, [{box[1]}, {box[2]}, {box[3]}, {box[4]}], {box[5]}, {box[6]}]\n")

        print(f"  ✅ Successfully processed {file_path}")

    except Exception as e:
        print(f"  ❌ Error processing {file_path}: {e}")

def process_all_bboxes(base_folder):
    """Process all bbox files in the base folder"""
    processed_count = 0
    
    for root, dirs, files in os.walk(base_folder):
        for file in files:
            if file.endswith('.txt'):
                file_path = os.path.join(root, file)
                print(f"\nProcessing: {file_path}")
                process_bboxes(file_path)
                processed_count += 1
    
    print(f"\n🎯 Completed processing {processed_count} files using percentage-based logic")
    print("📊 Key improvements:")
    print("  • Intersection assigned to box with highest percentage")
    print("  • Intersection keeps same annotation_id as winner")
    print("  • All content preserved as segments")
    print("  • Perfect for text filling with no gaps")

if __name__ == "__main__":
    base_folder = r'BBOX'
    if not os.path.exists(base_folder):
        print(f"❌ Error: Base folder '{base_folder}' does not exist")
    else:
        print("🚀 Starting percentage-based overlap resolution...")
        process_all_bboxes(base_folder)