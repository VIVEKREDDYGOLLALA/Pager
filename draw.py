#!/usr/bin/env python3
"""
Overlap Resolver with Percentage-Based Intersection Assignment
Assigns intersection areas to boxes with highest intersection percentage
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import os

def get_box_area(box):
    """Calculate area: width * height"""
    return box[3] * box[4]

def get_intersection_area(box1, box2):
    """Calculate intersection area between two boxes"""
    x1, y1, w1, h1 = box1[1], box1[2], box1[3], box1[4]
    x2, y2, w2, h2 = box2[1], box2[2], box2[3], box2[4]
    
    # Calculate boundaries
    left1, right1, top1, bottom1 = x1, x1 + w1, y1, y1 + h1
    left2, right2, top2, bottom2 = x2, x2 + w2, y2, y2 + h2
    
    # Find intersection boundaries
    left = max(left1, left2)
    right = min(right1, right2)
    top = max(top1, top2)
    bottom = min(bottom1, bottom2)
    
    # Check if there's actual intersection
    if left < right and top < bottom:
        return (right - left) * (bottom - top)
    return 0

def is_overlapping(box1, box2):
    """Check if two boxes overlap"""
    return get_intersection_area(box1, box2) > 0

def get_intersection_coordinates(box1, box2):
    """Get exact intersection coordinates"""
    x1, y1, w1, h1 = box1[1], box1[2], box1[3], box1[4]
    x2, y2, w2, h2 = box2[1], box2[2], box2[3], box2[4]
    
    left = max(x1, x2)
    right = min(x1 + w1, x2 + w2)
    top = max(y1, y2)
    bottom = min(y1 + h1, y2 + h2)
    
    if left < right and top < bottom:
        return (left, top, right - left, bottom - top)
    return None

def get_intersection_percentage(box, intersection_area):
    """Calculate what percentage of box's area is in the intersection"""
    box_area = get_box_area(box)
    if box_area == 0:
        return 0
    return (intersection_area / box_area) * 100

def segment_box_around_intersection(box, intersection):
    """
    Create segments from a box by removing intersection area
    Returns list of non-overlapping segments
    """
    if not intersection:
        return [box]
    
    x, y, w, h = box[1], box[2], box[3], box[4]
    ix, iy, iw, ih = intersection
    label, bbox_id, image_id = box[0], box[5], box[6]
    
    segments = []
    
    # Top segment (above intersection)
    if iy > y:
        top_seg = (label, x, y, w, iy - y, f"{bbox_id}_top", image_id)
        if get_box_area(top_seg) > 0:  # Only add if has area
            segments.append(top_seg)
    
    # Bottom segment (below intersection)
    if y + h > iy + ih:
        bottom_seg = (label, x, iy + ih, w, (y + h) - (iy + ih), f"{bbox_id}_bottom", image_id)
        if get_box_area(bottom_seg) > 0:
            segments.append(bottom_seg)
    
    # Left segment (left of intersection, within intersection height range)
    if ix > x:
        seg_y = max(y, iy)
        seg_h = min(y + h, iy + ih) - seg_y
        if seg_h > 0:
            left_seg = (label, x, seg_y, ix - x, seg_h, f"{bbox_id}_left", image_id)
            if get_box_area(left_seg) > 0:
                segments.append(left_seg)
    
    # Right segment (right of intersection, within intersection height range)
    if x + w > ix + iw:
        seg_y = max(y, iy)
        seg_h = min(y + h, iy + ih) - seg_y
        if seg_h > 0:
            right_seg = (label, ix + iw, seg_y, (x + w) - (ix + iw), seg_h, f"{bbox_id}_right", image_id)
            if get_box_area(right_seg) > 0:
                segments.append(right_seg)
    
    return segments

def resolve_overlaps_with_percentage_logic(boxes, max_iterations=10):
    """
    Resolve overlaps using percentage-based intersection assignment
    Box with highest intersection percentage gets the intersection area
    """
    # Remove duplicates first (keep largest per bbox_id)
    unique_boxes = {}
    for box in boxes:
        bbox_id = box[5]
        if bbox_id not in unique_boxes or get_box_area(box) > get_box_area(unique_boxes[bbox_id]):
            unique_boxes[bbox_id] = box
    
    current_boxes = list(unique_boxes.values())
    print(f"After duplicate removal: {len(current_boxes)} boxes")
    
    # Resolve overlaps using percentage logic
    for iteration in range(max_iterations):
        overlaps_found = False
        new_boxes = []
        processed_indices = set()
        
        for i, box1 in enumerate(current_boxes):
            if i in processed_indices:
                continue
            
            # Find all overlapping boxes
            overlapping_boxes = []
            overlapping_indices = []
            
            for j, box2 in enumerate(current_boxes[i+1:], i+1):
                if j in processed_indices:
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
                        intersection = get_intersection_coordinates(segment, overlapping_box)
                        if intersection:
                            intersection_area = intersection[2] * intersection[3]  # width * height
                            
                            # Calculate intersection percentages for both boxes
                            segment_area = get_box_area(segment)
                            overlapping_area = get_box_area(overlapping_box)
                            
                            segment_percentage = get_intersection_percentage(segment, intersection_area)
                            overlapping_percentage = get_intersection_percentage(overlapping_box, intersection_area)
                            
                            print(f"  Intersection Analysis:")
                            print(f"    {segment[5]}: area={segment_area:.0f}, intersection={intersection_area:.0f}, percentage={segment_percentage:.1f}%")
                            print(f"    {overlapping_box[5]}: area={overlapping_area:.0f}, intersection={intersection_area:.0f}, percentage={overlapping_percentage:.1f}%")
                            
                            # Assign intersection to box with higher percentage
                            if segment_percentage >= overlapping_percentage:
                                intersection_owner = segment
                                winner_name = segment[5]
                                print(f"    → {winner_name} gets intersection (higher percentage: {segment_percentage:.1f}%)")
                            else:
                                intersection_owner = overlapping_box
                                winner_name = overlapping_box[5]
                                print(f"    → {winner_name} gets intersection (higher percentage: {overlapping_percentage:.1f}%)")
                            
                            # Create intersection box with winner's content
                            ix, iy, iw, ih = intersection
                            intersection_box = (intersection_owner[0], ix, iy, iw, ih, 
                                              f"{intersection_owner[5]}_fill", intersection_owner[6])
                            intersection_boxes.append(intersection_box)
                            
                            # Create segments from current segment (minus intersection)
                            segments = segment_box_around_intersection(segment, intersection)
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
                            intersection = get_intersection_coordinates(segment, ref_box)
                            if intersection:
                                # Create segments (intersection already handled above)
                                segments = segment_box_around_intersection(segment, intersection)
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
        
        current_boxes = new_boxes
        
        if not overlaps_found:
            print(f"Percentage-based resolution completed in {iteration + 1} iterations")
            break
    
    print(f"Final result: {len(current_boxes)} non-overlapping boxes")
    return current_boxes

def visualize_boxes(before_boxes, after_boxes, title, save_path, image_width=400, image_height=300):
    """Create before/after visualization and save to file"""
    
    # Create output directory
    os.makedirs(save_path, exist_ok=True)
    
    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    fig.suptitle(title, fontsize=16, fontweight='bold')
    
    # Enhanced color palette
    colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6', '#e67e22', '#1abc9c', '#34495e']
    
    # Function to draw boxes on an axis
    def draw_boxes_on_axis(ax, boxes, subtitle):
        ax.set_xlim(0, image_width)
        ax.set_ylim(0, image_height)
        ax.set_aspect('equal')
        ax.invert_yaxis()
        ax.set_title(subtitle, fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        # Group by original bbox_id (before underscore)
        bbox_colors = {}
        for i, box in enumerate(boxes):
            original_id = box[5].split('_')[0]  # Get base ID
            if original_id not in bbox_colors:
                bbox_colors[original_id] = colors[len(bbox_colors) % len(colors)]
        
        for box in boxes:
            label, x, y, w, h, bbox_id, image_id = box
            original_id = bbox_id.split('_')[0]
            color = bbox_colors[original_id]
            
            # Different styling for fill boxes (intersection winners)
            if 'fill' in bbox_id:
                alpha = 0.8
                linewidth = 3
                linestyle = '-'
            else:
                alpha = 0.4
                linewidth = 2
                linestyle = '-'
            
            # Draw rectangle
            rect = patches.Rectangle((x, y), w, h, linewidth=linewidth, 
                                   edgecolor=color, facecolor=color, alpha=alpha,
                                   linestyle=linestyle)
            ax.add_patch(rect)
            
            # Add label
            font_size = 7 if len(bbox_id) > 12 else 8
            label_text = f'{bbox_id}\n{w:.0f}×{h:.0f}'
            if 'fill' in bbox_id:
                label_text += '\n(WINNER)'
            
            ax.text(x + w/2, y + h/2, label_text, 
                   ha='center', va='center', fontsize=font_size, fontweight='bold',
                   bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.9))
    
    # Draw before and after
    draw_boxes_on_axis(ax1, before_boxes, f"BEFORE\n{len(before_boxes)} boxes (with overlaps)")
    draw_boxes_on_axis(ax2, after_boxes, f"AFTER\n{len(after_boxes)} boxes (percentage-based)")
    
    plt.tight_layout()
    
    # Save image
    filename = title.replace(" ", "_").replace("-", "_").lower() + ".png"
    filepath = os.path.join(save_path, filename)
    plt.savefig(filepath, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"  📁 Saved visualization: {filepath}")
    plt.close()

def test_percentage_examples():
    """Test the percentage-based overlap resolver"""
    
    print("="*70)
    print("PERCENTAGE-BASED INTERSECTION ASSIGNMENT")
    print("="*70)
    
    save_dir = "percentage_visualizations"
    
    # Test Case 1: Different intersection percentages
    print("\n1. PERCENTAGE COMPARISON TEST:")
    print("   Box A: 1000 area, Box B: 2000 area, Intersection: 500")
    print("   A percentage: 500/1000 = 50%")
    print("   B percentage: 500/2000 = 25%")
    print("   → Box A should win (higher percentage)")
    
    boxes1 = [
        ("text", 50, 50, 100, 100, "box_A", "001"),  # Area: 10000
        ("text", 120, 80, 200, 100, "box_B", "001")  # Area: 20000, intersection ~5000
    ]
    result1 = resolve_overlaps_with_percentage_logic(boxes1)
    visualize_boxes(boxes1, result1, "1 - Percentage Winner Box A", save_dir)
    
    # Test Case 2: Reverse case - larger box wins on percentage
    print("\n2. LARGER BOX PERCENTAGE WIN:")
    boxes2 = [
        ("text", 50, 50, 80, 60, "small_box", "001"),   # Area: 4800
        ("text", 100, 70, 150, 80, "large_box", "001")  # Area: 12000
    ]
    result2 = resolve_overlaps_with_percentage_logic(boxes2)
    visualize_boxes(boxes2, result2, "2 - Percentage Winner Analysis", save_dir)
    
    # Test Case 3: Multiple overlaps with different percentages
    print("\n3. MULTIPLE OVERLAP PERCENTAGES:")
    boxes3 = [
        ("text", 80, 80, 100, 80, "center", "001"),     # Center box
        ("text", 50, 70, 60, 60, "left_small", "001"),  # Small left - high percentage
        ("text", 150, 60, 80, 60, "right_med", "001"),  # Medium right - lower percentage
        ("text", 110, 140, 60, 40, "bottom_tiny", "001") # Tiny bottom - very high percentage
    ]
    result3 = resolve_overlaps_with_percentage_logic(boxes3)
    visualize_boxes(boxes3, result3, "3 - Multiple Percentage Analysis", save_dir)
    
    # Test Case 4: Edge case - equal percentages
    print("\n4. EQUAL PERCENTAGE CASE:")
    boxes4 = [
        ("text", 60, 60, 100, 100, "square_A", "001"),   # 10000 area
        ("text", 120, 120, 100, 100, "square_B", "001")  # 10000 area, same intersection
    ]
    result4 = resolve_overlaps_with_percentage_logic(boxes4)
    visualize_boxes(boxes4, result4, "4 - Equal Percentage Resolution", save_dir)

if __name__ == "__main__":
    test_percentage_examples()
    
    print("\n" + "="*70)
    print("PERCENTAGE-BASED LOGIC SUMMARY")
    print("="*70)
    print("📊 Algorithm:")
    print("  1. Calculate intersection area between overlapping boxes")
    print("  2. Calculate percentage: (intersection_area / box_area) × 100")
    print("  3. Assign intersection to box with HIGHEST percentage")
    print("  4. Create segments from remaining areas")
    print("\n📁 Visualization files saved to 'percentage_visualizations/'")
    print("  • Shows percentage calculations and winners")
    print("  • 'fill' boxes = intersection winners (thick borders)")
    print("  • Segments = remaining non-overlapping areas")
    print("\n✅ Perfect for text filling:")
    print("  • No gaps in important content")
    print("  • Logical intersection assignment")
    print("  • All original content preserved as segments")
    
    plt.tight_layout()
    
    # Save image
    filename = title.replace(" ", "_").replace("-", "_").lower() + ".png"
    filepath = os.path.join(save_path, filename)
    plt.savefig(filepath, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"  📁 Saved visualization: {filepath}")
    plt.close()

def test_percentage_examples():
    """Test the percentage-based overlap resolver"""
    
    print("="*70)
    print("PERCENTAGE-BASED INTERSECTION ASSIGNMENT")
    print("="*70)
    
    save_dir = "percentage_visualizations"
    
    # Test Case 1: Different intersection percentages
    print("\n1. PERCENTAGE COMPARISON TEST:")
    print("   Box A: 1000 area, Box B: 2000 area, Intersection: 500")
    print("   A percentage: 500/1000 = 50%")
    print("   B percentage: 500/2000 = 25%")
    print("   → Box A should win (higher percentage)")
    
    boxes1 = [
        ("text", 50, 50, 100, 100, "box_A", "001"),  # Area: 10000
        ("text", 120, 80, 200, 100, "box_B", "001")  # Area: 20000, intersection ~5000
    ]
    result1 = resolve_overlaps_with_percentage_logic(boxes1)
    visualize_boxes(boxes1, result1, "1 - Percentage Winner Box A", save_dir)
    
    # Test Case 2: Reverse case - larger box wins on percentage
    print("\n2. LARGER BOX PERCENTAGE WIN:")
    boxes2 = [
        ("text", 50, 50, 80, 60, "small_box", "001"),   # Area: 4800
        ("text", 100, 70, 150, 80, "large_box", "001")  # Area: 12000
    ]
    result2 = resolve_overlaps_with_percentage_logic(boxes2)
    visualize_boxes(boxes2, result2, "2 - Percentage Winner Analysis", save_dir)
    
    # Test Case 3: Multiple overlaps with different percentages
    print("\n3. MULTIPLE OVERLAP PERCENTAGES:")
    boxes3 = [
        ("text", 80, 80, 100, 80, "center", "001"),     # Center box
        ("text", 50, 70, 60, 60, "left_small", "001"),  # Small left - high percentage
        ("text", 150, 60, 80, 60, "right_med", "001"),  # Medium right - lower percentage
        ("text", 110, 140, 60, 40, "bottom_tiny", "001") # Tiny bottom - very high percentage
    ]
    result3 = resolve_overlaps_with_percentage_logic(boxes3)
    visualize_boxes(boxes3, result3, "3 - Multiple Percentage Analysis", save_dir)
    
    # Test Case 4: Edge case - equal percentages
    print("\n4. EQUAL PERCENTAGE CASE:")
    boxes4 = [
        ("text", 60, 60, 100, 100, "square_A", "001"),   # 10000 area
        ("text", 120, 120, 100, 100, "square_B", "001")  # 10000 area, same intersection
    ]
    result4 = resolve_overlaps_with_percentage_logic(boxes4)
    visualize_boxes(boxes4, result4, "4 - Equal Percentage Resolution", save_dir)

# Example usage function
def simple_usage_example():
    """Simple example showing how to use the percentage-based resolver"""
    
    print("\n" + "="*50)
    print("SIMPLE USAGE EXAMPLE")
    print("="*50)
    
    # Your bounding boxes with overlaps
    input_boxes = [
        ("text", 100, 100, 150, 80, "region_1", "001"),  # Area: 12000
        ("text", 200, 120, 100, 120, "region_2", "001"), # Area: 12000  
        ("text", 180, 80, 80, 60, "region_3", "001")     # Area: 4800
    ]
    
    print("Input boxes:")
    for box in input_boxes:
        label, x, y, w, h, bbox_id, image_id = box
        print(f"  {bbox_id}: [{x}, {y}, {w}, {h}] area={w*h}")
    
    # Resolve overlaps
    clean_boxes = resolve_overlaps_with_percentage_logic(input_boxes, verbose=False)
    
    print(f"\nOutput: {len(clean_boxes)} clean boxes ready for text filling:")
    for box in clean_boxes:
        label, x, y, w, h, bbox_id, image_id = box
        box_type = "INTERSECTION" if "fill" in bbox_id else "SEGMENT"
        print(f"  {bbox_id}: [{x}, {y}, {w}, {h}] area={w*h} ({box_type})")

if __name__ == "__main__":
    test_percentage_examples()
    simple_usage_example()
    
    print("\n" + "="*70)
    print("PERCENTAGE-BASED LOGIC SUMMARY")
    print("="*70)
    print("📊 Algorithm:")
    print("  1. Calculate intersection area between overlapping boxes")
    print("  2. Calculate percentage: (intersection_area / box_area) × 100")
    print("  3. Assign intersection to box with HIGHEST percentage")
    print("  4. Create segments from remaining areas")
    print("\n📁 Visualization files saved to 'percentage_visualizations/'")
    print("  • Shows percentage calculations and winners")
    print("  • 'fill' boxes = intersection winners (thick borders)")
    print("  • Segments = remaining non-overlapping areas")
    print("\n✅ Perfect for text filling:")
    print("  • No gaps in important content")
    print("  • Logical intersection assignment")
    print("  • All original content preserved as segments")
    print("\n💡 Quick Usage:")
    print("from overlap_resolver import resolve_overlaps_with_percentage_logic")
    print("clean_boxes = resolve_overlaps_with_percentage_logic(your_boxes)")
    print("# Now fill text in clean_boxes - perfect coverage!")