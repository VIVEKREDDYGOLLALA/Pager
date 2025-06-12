
import textwrap
import copy 
import random
import requests
from io import BytesIO
import time
from pylatex import Document, NoEscape, Package
from pylatex.base_classes import Environment
from PIL import ImageFont, ImageDraw, Image
import numpy as np
from sklearn.cluster import KMeans
from collections import Counter, defaultdict
import os
import re
import json
import math
from PIL import Image
from label_mapping import label_mapping_1, label_mapping_2, label_mapping_3, label_mapping_4, label_mapping_5, label_mapping_default

processed_box_ids = set()
asterisk_added = {}
start_time = time.time()
box_id_line_idx_map = {}

class Center(Environment):
    packages = [Package('amsmath')]
    _latex_name = 'center'

# Global variable to store JSON annotations
output_json = {"annotations": []}

font_size_mapping = {
    '\\zettaHuge': 200, '\\exaHuge': 165, '\\petaHuge': 135, '\\teraHuge': 110, '\\gigaHuge': 90,
    '\\megaHuge': 75, '\\superHuge': 62, '\\alphaa': 60, '\\betaa': 57, '\\gammaa': 55,
    '\\deltaa': 53, '\\epsilona': 51, '\\veryHuge': 49, '\\zetaa': 47, '\\etaa': 45,
    '\\veryLarge': 43, '\\iotaa': 41, '\\kappaa': 39, '\\verylarge': 37, '\\lambdaa': 35,
    '\\mua': 33, '\\nua': 31, '\\xia': 29, '\\pia': 27, '\\Huge': 25,
    '\\rhoa': 24, '\\sigmaa': 22, '\\huge': 20, '\\taua': 18, '\\LARGE': 17,
    '\\upsilona': 16, '\\Large': 15, '\\phia': 15, '\\large': 12, '\\chia': 13,
    '\\psia': 11, '\\normalsize': 10, '\\small': 9, '\\footnotesize': 8, '\\scriptsize': 7,
    '\\omegaa': 6, '\\tiny': 5, '\\oomegaa': 4, '\\ooomegaa': 3, '\\oooomegaaa': 2
}

FONT_MAPPING = {
    'assamese': 'NotoSerif', 'bengali': 'NotoSerifBengali', 'bodo': 'NotoSerif', 'dogri': 'NotoSerif',
    'gujarati': 'NotoSerifGujarati', 'hindi': 'NotoSerifDevanagari', 'kannada': 'NotoSerifKannada',
    'kashmiri': 'NotoSerif', 'konkani': 'NotoSerif', 'maithili': 'NotoSerifDevanagari',
    'malayalam': 'NotoSerifMalayalam', 'manipuri': 'NotoSansMeeteiMayek', 'marathi': '',
    'nepali': 'NotoSerifDevanagari', 'odia': 'NotoSerifOriya', 'punjabi': 'NotoSerifGurmukhi',
    'sanskrit': 'NotoSerifDevanagari', 'santali': 'NotoSerif', 'sindhi': 'NotoSerifDevanagari', 'tamil': 'NotoSerifTamil',
    'telugu': 'NotoSerifTelugu', 'urdu': 'Amiri'
}
import os
import json
import copy
from collections import defaultdict
from PIL import Image, ImageFont, ImageDraw

# Cache for text measurements
text_size_cache = defaultdict(dict)
# Track processed box IDs per image and language
processed_box_ids = defaultdict(set)
# Track line indices per box ID - this tracks which textline we're processing for each parent box
box_id_line_idx_map = defaultdict(int)

# Global tracking to ensure sequential processing and prevent repeats
global_text_state = defaultdict(lambda: {
    'current_position': 0,
    'current_folder': 1,
    'max_folder_reached': 1,
    'folders_exhausted': False,
    'total_words_processed': 0
})

# Track which languages are exhausted globally
exhausted_languages = set()

# Track textlines for each parent box ID
textlines_per_box = defaultdict(list)

def find_closest_font_size_point(bbox_height_inches, font_path, dpi):
    valid_sizes = {}
    for size, point_size in font_size_mapping.items():
        try:
            font = ImageFont.truetype(font_path, int(point_size))
            # Create a temporary image for measurement
            img = Image.new('RGB', (100, 100), (255, 255, 255))
            draw = ImageDraw.Draw(img)
            # Measure a sample character (e.g., 'A') to estimate height
            sample_text = 'A'
            text_bbox = draw.textbbox((0, 0), sample_text, font=font)
            text_height_pixels = text_bbox[3] - text_bbox[1]
            text_height_inches = text_height_pixels / dpi
            if text_height_inches <= bbox_height_inches:
                valid_sizes[size] = point_size
            del img, draw
        except (Exception, MemoryError) as e:
            print(f"Error measuring font size {size} for font {font_path}: {e}")
            try:
                del img, draw
            except:
                pass
    if not valid_sizes:
        return None, None
    best_size = max(valid_sizes, key=lambda size: valid_sizes[size])
    return best_size, valid_sizes[best_size]

def load_text_from_folder(input_text_folder, language, folder_index):
    """Load text from a specific folder, return words and total count"""
    text_file = os.path.join(input_text_folder, f"input_{folder_index}", f"{language}.txt")
    
    if not os.path.exists(text_file):
        return None, 0
    
    try:
        with open(text_file, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read().strip()
        
        if not text:
            return None, 0
            
        words = text.split()
        return words, len(words)
        
    except Exception as e:
        print(f"Error reading {text_file}: {e}")
        return None, 0

def get_next_sequential_text(language, input_text_folder, words_needed=50):
    """
    Get text sequentially from folders without repeating or going backwards.
    Returns words and updates global state.
    """
    # Check if language is already exhausted
    if language in exhausted_languages:
        print(f"Language {language} is already exhausted. Skipping.")
        return [], 0
        
    state = global_text_state[language]
    
    # If we've exhausted all folders, return empty
    if state['folders_exhausted']:
        print(f"All folders exhausted for {language}. Adding to exhausted languages.")
        exhausted_languages.add(language)
        return [], 0
    
    collected_words = []
    words_collected = 0
    
    while words_collected < words_needed and not state['folders_exhausted']:
        # Try to load current folder
        folder_words, total_words = load_text_from_folder(
            input_text_folder, language, state['current_folder']
        )
        
        if folder_words is None or total_words == 0:
            # Current folder doesn't exist or is empty, try next folder
            state['current_folder'] += 1
            state['current_position'] = 0
            
            # Check if we've gone too far (safety limit)
            if state['current_folder'] > 1000:  # Your mentioned limit
                print(f"Reached folder limit (1000) for {language}. Marking as exhausted.")
                state['folders_exhausted'] = True
                exhausted_languages.add(language)
                break
                
            continue
        
        # Update max folder reached
        state['max_folder_reached'] = max(state['max_folder_reached'], state['current_folder'])
        
        # Get available words from current position
        available_words = folder_words[state['current_position']:]
        
        if not available_words:
            # No more words in this folder, move to next
            print(f"Folder {state['current_folder']} exhausted for {language}. Moving to next folder.")
            state['current_folder'] += 1
            state['current_position'] = 0
            continue
        
        # Take what we need or what's available
        words_to_take = min(words_needed - words_collected, len(available_words))
        taken_words = available_words[:words_to_take]
        
        collected_words.extend(taken_words)
        words_collected += words_to_take
        state['current_position'] += words_to_take
        state['total_words_processed'] += words_to_take
        
        print(f"Language {language}: Took {words_to_take} words from folder {state['current_folder']}, "
              f"position {state['current_position'] - words_to_take} to {state['current_position']}")
        
        # If we've used all words in this folder, move to next
        if state['current_position'] >= total_words:
            print(f"Completed folder {state['current_folder']} for {language}. Moving to next folder.")
            state['current_folder'] += 1
            state['current_position'] = 0
    
    # If no words collected and we tried, mark as exhausted
    if words_collected == 0 and not state['folders_exhausted']:
        print(f"No more words available for {language}. Marking as exhausted.")
        state['folders_exhausted'] = True
        exhausted_languages.add(language)
    
    return collected_words, len(collected_words)

def save_language_state(language, output_folder_path):
    """Save the current state for a language"""
    state = global_text_state[language]
    state_file = os.path.join(output_folder_path, f"{language}_state.json")
    
    try:
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump({
                'current_position': state['current_position'],
                'current_folder': state['current_folder'],
                'max_folder_reached': state['max_folder_reached'],
                'folders_exhausted': state['folders_exhausted'],
                'total_words_processed': state['total_words_processed']
            }, f, indent=2)
    except Exception as e:
        print(f"Error saving state for {language}: {e}")

def load_language_state(language, output_folder_path):
    """Load the saved state for a language"""
    state_file = os.path.join(output_folder_path, f"{language}_state.json")
    
    if not os.path.exists(state_file):
        return
    
    try:
        with open(state_file, 'r', encoding='utf-8') as f:
            saved_state = json.load(f)
        
        state = global_text_state[language]
        state.update(saved_state)
        
        # Check if this language was marked as exhausted
        if state['folders_exhausted']:
            exhausted_languages.add(language)
        
        print(f"Loaded state for {language}: folder {state['current_folder']}, "
              f"position {state['current_position']}, "
              f"total processed: {state['total_words_processed']}")
              
    except Exception as e:
        print(f"Error loading state for {language}: {e}")

def create_or_update_json_annotation(output_folder_path, language, image_name, parent_box_id, 
                                    textline_id, image_id, parent_label, textline_x1, textline_y1, 
                                    textline_width, textline_height, text_content, image_width, 
                                    image_height, categories, parent_bbox=None):
    """
    Create or update JSON annotation by adding textlines to their parent bounding box.
    This function handles the grouping of multiple textlines under one parent box.
    """
    try:
        image_json_path = os.path.join(output_folder_path, f"{language}_{image_name}.json")
        
        # Load existing data or create new
        if os.path.exists(image_json_path):
            try:
                with open(image_json_path, 'r', encoding='utf-8') as f:
                    image_data = json.load(f)
            except:
                image_data = {"images": [], "annotations": [], "categories": categories}
        else:
            image_data = {"images": [], "annotations": [], "categories": categories}
        
        def get_category_id(label_name, categories):
            for category in categories:
                if label_name.lower() == category["name"].lower():
                    return category["id"]
            return 1  # Default category
        
        # Create image entry if not exists
        if not any(img["id"] == image_id for img in image_data["images"]):
            image_entry = {
                "id": image_id,
                "image_name": image_name,
                "width": int(image_width),
                "height": int(image_height),
                "license": None,
                "flickr_url": "",
                "image_url": "",
                "date_captured": ""
            }
            image_data["images"].append(image_entry)
        
        # Find existing parent annotation or create new one
        parent_annotation = None
        for annotation in image_data["annotations"]:
            if annotation["id"] == f"{parent_box_id}":
                parent_annotation = annotation
                break
        
        if parent_annotation is None:
            # Create new parent annotation
            if parent_bbox is None:
                # If no parent bbox provided, use textline bbox as approximation
                parent_bbox = [textline_x1, textline_y1, textline_width, textline_height]
            
            parent_annotation = {
                "id": f"{parent_box_id}",
                "image_id": image_id,
                "category_id": get_category_id(parent_label, categories),
                "bbox": parent_bbox,
                "area": parent_bbox[2] * parent_bbox[3],
                "iscrowd": 0,
                "segmentation": [],
                "attributes": {"text": ""},  # Will be updated with combined text
                "textlines": []
            }
            image_data["annotations"].append(parent_annotation)
        
        # Create textline annotation
        textline_annotation = {
            "id": textline_id,
            "image_id": image_id,
            "category_id": get_category_id("textline", categories),
            "bbox": [textline_x1, textline_y1, textline_width, textline_height],
            "area": textline_width * textline_height,
            "iscrowd": 0,
            "segmentation": [],
            "attributes": {"text": text_content}
        }
        
        # Check if this textline already exists (avoid duplicates)
        existing_textline = None
        for textline in parent_annotation["textlines"]:
            if textline["id"] == textline_id:
                existing_textline = textline
                break
        
        if existing_textline:
            # Update existing textline
            existing_textline.update(textline_annotation)
        else:
            # Add new textline
            parent_annotation["textlines"].append(textline_annotation)
        
        # Update parent annotation's combined text
        all_textline_texts = [tl["attributes"]["text"] for tl in parent_annotation["textlines"]]
        combined_text = " ".join(filter(None, all_textline_texts))  # Filter out empty strings
        parent_annotation["attributes"]["text"] = combined_text
        
        # Save JSON
        with open(image_json_path, 'w', encoding='utf-8') as f:
            json.dump(image_data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Updated JSON annotation for {language}_{image_name} - parent box {parent_box_id}, textline {textline_id}")
        return True
        
    except Exception as e:
        print(f"✗ Error updating JSON for {language}_{image_name} box {parent_box_id}: {e}")
        return False

def estimate_text_to_fit(text, bbox_width_inches, bbox_height_inches, parent_box_id, language, 
                        textline_x1, textline_y1, font_size, bboxes, dpi, font_path, image_name, 
                        image_height, image_width, input_text_folder):
    
    output_folder_path = 'output_jsons'
    os.makedirs(output_folder_path, exist_ok=True)
    
    try:
        # Check if language is exhausted before processing
        if language in exhausted_languages:
            print(f"Language {language} is exhausted. Skipping textline for box {parent_box_id}")
            return ''
        
        # Load saved state for this language
        load_language_state(language, output_folder_path)
        
        # Check again after loading state
        if language in exhausted_languages:
            print(f"Language {language} is exhausted after loading state. Skipping textline for box {parent_box_id}")
            return ''
        
        # Get current textline info - find the specific textline being processed
        current_textline = None
        parent_box_info = None
        
        # Find parent box and current textline
        for bbox in bboxes:
            if len(bbox) > 5 and bbox[5] == parent_box_id:
                if bbox[4].lower() != "textline":
                    parent_box_info = bbox
                else:
                    # This might be the current textline
                    if (abs(bbox[0] - textline_x1) < 1 and abs(bbox[1] - textline_y1) < 1):
                        current_textline = bbox
        
        if not parent_box_info:
            print(f"Parent box {parent_box_id} not found in bboxes")
            return ''
        
        parent_label = parent_box_info[4]
        image_id = parent_box_info[6] if len(parent_box_info) > 6 else "unknown"
        
        # Check if this is a dateline (special handling)
        is_dateline = parent_label.lower() == "dateline"
        
        # Define categories
        unique_labels = set(['textline', 'unknown'])
        for bbox in bboxes:
            if len(bbox) > 4:
                unique_labels.add(bbox[4].lower())
        categories = [{"id": idx + 1, "name": label_name, "supercategory": "text"} 
                     for idx, label_name in enumerate(sorted(unique_labels))]
        
        # Get the next line index for this parent box
        box_line_key = f"{language}_{image_name}_{parent_box_id}"
        box_id_line_idx_map[box_line_key] += 1
        current_line_idx = box_id_line_idx_map[box_line_key]
        
        # Create textline ID
        textline_id = f"{parent_box_id}_{current_line_idx}"
        
        # Precompute font size
        point_size = font_size_mapping.get(font_size, 10)
        try:
            font = ImageFont.truetype(font_path, int(point_size))
        except Exception as e:
            print(f"Error loading font {font_path}: {e}")
            return ''

        line_height = point_size * 1.5
        
        # Get text sequentially if not dateline
        if is_dateline:
            # For dateline, use provided text or fallback
            words = text.split() if text else ["Date:", "Location"]
            fitted_text_content = " ".join(words)
        else:
            # Calculate words needed for this textline
            estimated_words_needed = max(5, int(bbox_width_inches * 5))
            
            # Get sequential text without repetition
            words, word_count = get_next_sequential_text(language, input_text_folder, words_needed=estimated_words_needed)
            
            if word_count == 0:
                print(f"No more unique text available for {language} - language exhausted, skipping textline")
                return ''
            
            # Create temporary image for text measurement
            try:
                img_width = min(int(bbox_width_inches * dpi), 2000)
                img_height = 100  # Small height for single line
                img = Image.new('RGB', (img_width, img_height), (255, 255, 255))
                draw = ImageDraw.Draw(img)
            except MemoryError:
                print(f"MemoryError creating image for textline {textline_id}")
                return ''
            
            # Fit text to single line
            current_line = ''
            current_line_width = 0
            bbox_width_pixels = bbox_width_inches * dpi
            
            for word in words:
                try:
                    # Use cache for text measurements
                    cache_key = (word, point_size, font_path)
                    if cache_key not in text_size_cache[language]:
                        word_bbox = draw.textbbox((0, 0), word, font=font)
                        text_size_cache[language][cache_key] = word_bbox[2] - word_bbox[0]
                    word_width = text_size_cache[language][cache_key]
                    
                    space_cache_key = (' ', point_size, font_path)
                    if space_cache_key not in text_size_cache[language]:
                        space_bbox = draw.textbbox((0, 0), ' ', font=font)
                        text_size_cache[language][space_cache_key] = space_bbox[2] - space_bbox[0]
                    space_width = text_size_cache[language][space_cache_key]
                    
                    new_width = current_line_width + space_width + word_width if current_line else word_width
                    
                    if new_width <= bbox_width_pixels:
                        current_line = (current_line + ' ' + word) if current_line else word
                        current_line_width = new_width
                    else:
                        break  # Stop fitting more text
                        
                except Exception as e:
                    print(f"Error processing word '{word}': {e}")
                    break
            
            fitted_text_content = current_line
            
            # Clean up image
            del img, draw
        
        # Only create/update JSON if we have text content
        if fitted_text_content:
            success = create_or_update_json_annotation(
                output_folder_path, language, image_name, parent_box_id, textline_id,
                image_id, parent_label, textline_x1, textline_y1, bbox_width_inches, 
                bbox_height_inches, fitted_text_content, image_width, image_height, 
                categories, parent_bbox=parent_box_info[:4] if len(parent_box_info) >= 4 else None
            )
            
            # Save state after successful processing
            save_language_state(language, output_folder_path)
            
            print(f"✓ Processed textline {textline_id} for parent box {parent_box_id}: '{fitted_text_content[:50]}...'")
        else:
            print(f"No text fitted for textline {textline_id}, skipping JSON creation")
        
        # Clean cache periodically
        if len(text_size_cache[language]) > 2000:
            # Keep only recent entries
            cache_items = list(text_size_cache[language].items())
            text_size_cache[language].clear()
            for key, value in cache_items[-1000:]:
                text_size_cache[language][key] = value
        
        return fitted_text_content + r'\linebreak' if fitted_text_content else ''
        
    except Exception as e:
        print(f"Critical error in estimate_text_to_fit for textline of box {parent_box_id}: {e}")
        return ''

def get_processing_stats(language):
    """Get current processing statistics for a language"""
    state = global_text_state[language]
    return {
        'current_folder': state['current_folder'],
        'current_position': state['current_position'],
        'max_folder_reached': state['max_folder_reached'],
        'total_words_processed': state['total_words_processed'],
        'folders_exhausted': state['folders_exhausted'],
        'is_exhausted': language in exhausted_languages
    }

def reset_language_processing(language):
    """Reset processing for a language (use with caution)"""
    global_text_state[language] = {
        'current_position': 0,
        'current_folder': 1,
        'max_folder_reached': 1,
        'folders_exhausted': False,
        'total_words_processed': 0
    }
    # Remove from exhausted languages
    exhausted_languages.discard(language)
    # Clear line indices for this language
    keys_to_remove = [key for key in box_id_line_idx_map.keys() if key.startswith(f"{language}_")]
    for key in keys_to_remove:
        del box_id_line_idx_map[key]
    print(f"Reset processing state for language: {language}")

def is_language_exhausted(language):
    """Check if a language is exhausted"""
    return language in exhausted_languages

def get_exhausted_languages():
    """Get list of exhausted languages"""
    return list(exhausted_languages)

def skip_exhausted_languages(languages_list):
    """Filter out exhausted languages from a list"""
    return [lang for lang in languages_list if lang not in exhausted_languages]

def should_continue_processing(language):
    """Check if we should continue processing this language"""
    return language not in exhausted_languages

def reset_box_line_indices():
    """Reset all box line indices - useful when starting a new image"""
    box_id_line_idx_map.clear()    
def get_patch_color_with_gradient(image, bbox):
    x1, y1, width, height = bbox[:4]
    corners = [(x1, y1), (x1 + width, y1), (x1, y1 + height), (x1 + width, y1 + height)]
    image_width, image_height = image.size
    valid_corners = [(cx, cy) for cx, cy in corners if 0 <= cx < image_width and 0 <= cy < image_height]

    if len(valid_corners) < 2:
        return None, None, None

    corner_colors = [image.getpixel(corner) for corner in valid_corners]
    top_left = corner_colors[0]
    top_right = corner_colors[0] if len(corner_colors) < 2 else corner_colors[1]
    bottom_left = corner_colors[0] if len(corner_colors) < 2 else corner_colors[1]
    bottom_right = corner_colors[0] if len(corner_colors) < 2 else corner_colors[1]

    if (top_left == top_right) and (bottom_left == bottom_right) and (top_left != bottom_left):
        gradient_type = "vertical"
        start_color = top_left
        end_color = bottom_left
    elif (top_left == bottom_left) and (top_right == bottom_right) and (top_left != top_right):
        gradient_type = "horizontal"
        start_color = top_left
        end_color = top_right
    elif (top_left != top_right) and (top_left != bottom_left) and (top_left != bottom_right) and (bottom_left != bottom_right):
        gradient_type = "diagonal"
        start_color = top_left
        end_color = bottom_right
    elif (top_right != top_left) and (top_right != bottom_left) and (top_right != bottom_right) and (bottom_left != bottom_right):
        gradient_type = "diagonal_reverse"
        start_color = top_right
        end_color = bottom_left
    elif (top_left == top_right == bottom_left == bottom_right):
        gradient_type = "uniform"
        start_color = top_left
        end_color = top_left
    else:
        gradient_type = "horizontal"
        start_color = top_left
        end_color = top_right

    return gradient_type, start_color, end_color

def generate_latex_for_gradient(x1, y1, width, height, gradient_type, start_color, end_color):
    color1_latex = f"{start_color[0] / 255:.2f},{start_color[1] / 255:.2f},{start_color[2] / 255:.2f}"
    color2_latex = f"{end_color[0] / 255:.2f},{end_color[1] / 255:.2f},{end_color[2] / 255:.2f}"
    color1_name = f"color1_{x1}_{y1}"
    color2_name = f"color2_{x1}_{y1}"

    color_definitions = f"""
\\definecolor{{{color1_name}}}{{rgb}}{{{color1_latex}}}
\\definecolor{{{color2_name}}}{{rgb}}{{{color2_latex}}}
"""
    if gradient_type == "vertical":
        fill_command = f"\\shade[bottom color={{{color2_name}}}, top color={{{color1_name}}}] ({x1}pt,{y1}pt) rectangle ({x1 + width}pt,{y1 + height}pt);"
    elif gradient_type == "horizontal":
        fill_command = f"\\shade[left color={{{color1_name}}}, right color={{{color2_name}}}] ({x1}pt,{y1}pt) rectangle ({x1 + width}pt,{y1 + height}pt);"
    elif gradient_type == "diagonal":
        fill_command = f"\\shade[left color={{{color1_name}}}, right color={{{color2_name}}}, shading angle=45] ({x1}pt,{y1}pt) rectangle ({x1 + width}pt,{y1 + height}pt);"
    elif gradient_type == "diagonal_reverse":
        fill_command = f"\\shade[left color={{{color1_name}}}, right color={{{color2_name}}}, shading angle=-45] ({x1}pt,{y1}pt) rectangle ({x1 + width}pt,{y1 + height}pt);"
    elif gradient_type == "uniform":
        fill_command = f"\\fill[{color2_name}] ({x1}pt,{y1}pt) rectangle ({x1 + width}pt,{y1 + height}pt);"

    return color_definitions + fill_command

def get_most_used_colors(image, bbox, n_colors=2):
    x1, y1, width, height = bbox[:4]
    patch = image.crop((x1, y1, x1 + width, y1 + height))
    patch_data = np.array(patch).reshape(-1, 3)
    color_counts = Counter(map(tuple, patch_data))
    most_common_colors = color_counts.most_common(n_colors)
    return [color for color, count in most_common_colors]

def choose_text_color(bg_color, dominant_colors):
    tolerance = 10
    percentage_tolerance = 0.25
    black_color = np.array([0, 0, 0])
    bg_color = np.array(bg_color)
    dominant_colors = [np.array(color) for color in dominant_colors]

    def is_similar_color(color1, color2, tolerance, percentage_tolerance):
        abs_diff = np.abs(color1 - color2)
        relative_diff = abs_diff / 255.0
        return np.all(relative_diff <= percentage_tolerance) or np.all(abs_diff <= tolerance)

    if len(dominant_colors) > 1 and not is_similar_color(dominant_colors[1], bg_color, tolerance, percentage_tolerance):
        chosen_color = dominant_colors[1]
    elif not is_similar_color(dominant_colors[0], bg_color, tolerance, percentage_tolerance):
        chosen_color = dominant_colors[0]
    else:
        chosen_color = black_color
    if is_similar_color(chosen_color, bg_color, tolerance, percentage_tolerance):
        return black_color
    return chosen_color

def rgb_to_normalized(rgb):
    return [val / 255.0 for val in rgb]

def load_enough_text(language, max_lines=1000, input_text_folder="input_texts"):
    """
    Loads text from input_text/input_1/{language}.txt, falling back to input_text/input_2/{language}.txt
    when the first file's text is exhausted.
    
    Args:
        language (str): The language for which to load text.
        max_lines (int): Maximum number of lines to load.
        input_text_folder (str): Path to the input text folder.
    
    Returns:
        list: List of text lines.
    """
    texts = []
    folder_index = 1
    text_position_file = os.path.join('output_jsons', f"{language}_position.json")
    
    # Load current folder index
    if os.path.exists(text_position_file):
        try:
            with open(text_position_file, 'r', encoding='utf-8', errors='ignore') as pos_file:
                position_data = json.load(pos_file)
                folder_index = position_data.get('folder_index', 1)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error reading position file {text_position_file} for {language}: {e}")
            folder_index = 1

    text_file = os.path.join(input_text_folder, f"input_{folder_index}", f"{language}.txt")
    try:
        with open(text_file, 'r', encoding='utf-8', errors='ignore') as file:
            for i, line in enumerate(file):
                if i >= max_lines:
                    break
                texts.append(line.strip())
        if not texts:  # If file is empty, try the next folder
            folder_index = 2
            text_file = os.path.join(input_text_folder, f"input_{folder_index}", f"{language}.txt")
            with open(text_file, 'r', encoding='utf-8', errors='ignore') as file:
                for i, line in enumerate(file):
                    if i >= max_lines:
                        break
                    texts.append(line.strip())
    except FileNotFoundError:
        print(f"Text file {text_file} not found for {language}. Trying next folder.")
        folder_index = 2 if folder_index == 1 else 1
        text_file = os.path.join(input_text_folder, f"input_{folder_index}", f"{language}.txt")
        try:
            with open(text_file, 'r', encoding='utf-8', errors='ignore') as file:
                for i, line in enumerate(file):
                    if i >= max_lines:
                        break
                    texts.append(line.strip())
        except FileNotFoundError:
            print(f"Text file {text_file} not found for {language}. Using empty text.")
            texts = []

    return texts

def extract_dimensions_and_text_from_file(image_path, file_path, language, label_mapping, input_text_folder):
    image_path = os.path.abspath(image_path)
    file_path = os.path.abspath(file_path)

    with open(file_path, 'r') as file:
        lines = file.readlines()

    image_dimensions_line = lines[0].strip()
    image_dimensions = eval(image_dimensions_line)
    if not isinstance(image_dimensions, list) or len(image_dimensions) != 2:
        raise ValueError(f"Invalid image dimensions: {image_dimensions}")

    with Image.open(image_path) as img:
        pixel_width, pixel_height = img.size

    diagonal_pixels = math.sqrt(pixel_width**2 + pixel_height**2)
    diagonal_inches = math.sqrt(image_dimensions[0]**2 + image_dimensions[1]**2)
    dpi = diagonal_pixels / diagonal_inches

    box_details = lines[1:]
    bboxes = []
    for line in box_details:
        if line.strip():
            match = re.match(r'^\[([^\[\],]+?),\s*\[\s*(\d+(\.\d+)?)\s*,\s*(\d+(\.\d+)?)\s*,\s*(\d+(\.\d+)?)\s*,\s*(\d+(\.\d+)?)\s*\],\s*([^\[\],]+?),\s*(\S+)\]$', line.strip())
            if not match:
                continue
            try:
                label = match.group(1).strip().strip('"')
                dimensions = [float(match.group(i)) for i in [2, 4, 6, 8]]
                annotation_id = match.group(10).strip()
                image_id = match.group(11).strip()
                x1, y1, width, height = dimensions
                bboxes.append([x1, y1, width, height, label, annotation_id, image_id])
            except Exception as e:
                print(f"Error processing line '{line.strip()}' for {language}: {e}")

    texts = load_enough_text(language, max_lines=5000000, input_text_folder=input_text_folder)
    latex_code = generate_latex(image_path, image_dimensions, bboxes, texts, label_mapping, dpi, language, input_text_folder)

    main_output_folder = 'Output_Tex_Files'
    os.makedirs(main_output_folder, exist_ok=True)

    output_folder = os.path.join(main_output_folder, f'Tex_files_{language}')
    os.makedirs(output_folder, exist_ok=True)

    image_file_name = os.path.splitext(os.path.basename(image_path))[0]
    latex_output_file = os.path.join(output_folder, f"{image_file_name}.tex")
    with open(latex_output_file, "w", encoding='utf-8') as output_file:
        output_file.write(latex_code)

def get_bboxes_and_image_path():
    bbox_dir = 'BBOX_0'
    image_dir = 'images_val_0'
    if not os.path.exists(bbox_dir):
        raise FileNotFoundError(f"Directory not found: {bbox_dir}")

    bbox_files_and_paths = []
    for subdir, _, files in os.walk(bbox_dir):
        bbox_files = [f for f in files if f.endswith('.txt')]
        for bbox_file in bbox_files:
            bbox_file_path = os.path.join(subdir, bbox_file)
            file_name_with_id = os.path.basename(bbox_file).replace('.txt', '')
            file_name = "_".join(file_name_with_id.split('_')[:-1])
            image_name = file_name + '.png'
            image_path = os.path.join(image_dir, image_name)
            if os.path.exists(image_path) and not os.path.basename(image_path).startswith('._'):
                bbox_files_and_paths.append((bbox_file_path, image_path))

    if not bbox_files_and_paths:
        raise FileNotFoundError("No matching bounding box or image file found.")
    return bbox_files_and_paths

def split_into_sentences(text):
    sentence_endings = re.compile(r'(?<=[.!?।])\s+')
    return sentence_endings.split(text.strip())

def get_random_font(fonts_dir):
    fonts_dir = os.path.abspath(fonts_dir)
    fonts = [f for f in os.listdir(fonts_dir) if f.endswith('.ttf')]
    if not fonts:
        raise FileNotFoundError(f"No .ttf files found in directory: {fonts_dir}")
    return os.path.join(fonts_dir, random.choice(fonts))

def generate_latex(image_path, image_dimensions, bboxes, texts, label_mapping, dpi, language, input_text_folder):
    image_path = os.path.abspath(image_path)
    image_name = os.path.splitext(os.path.basename(image_path))[0]
    header_fonts_dir = os.path.join("fonts", language, "Header")
    paragraph_fonts_dir = os.path.join("fonts", language, "Paragraph")

    try:
        header_font_path = get_random_font(header_fonts_dir)
        paragraph_font_path = get_random_font(paragraph_fonts_dir)
        header_font = os.path.basename(header_font_path).replace('.ttf', '')
        paragraph_font = os.path.basename(paragraph_font_path).replace('.ttf', '')
    except FileNotFoundError as e:
        print(f"Font error for {language}: {e}")
        header_font = FONT_MAPPING.get(language, 'NotoSerif')
        paragraph_font = FONT_MAPPING.get(language, 'NotoSerif')
        header_font_path = os.path.join("fonts", language, "Header", f"{header_font}-Bold.ttf")
        paragraph_font_path = os.path.join("fonts", language, "Paragraph", f"{paragraph_font}-Regular.ttf")

    doc = Document(documentclass='article', document_options=['11pt'])
    is_arabic_script = language.lower() in ['urdu', 'kashmiri']

    doc.packages.append(Package('fontenc', options='T1'))
    doc.packages.append(Package('inputenc', options='utf8'))
    doc.packages.append(Package('lmodern'))
    doc.packages.append(Package('textcomp'))
    doc.packages.append(Package('lastpage'))
    doc.packages.append(Package('tikz'))
    doc.packages.append(Package('fontspec'))
    doc.packages.append(Package('polyglossia'))
    
    doc.packages.append(Package('geometry', options=f'paperwidth={image_dimensions[1]}pt,paperheight={image_dimensions[0]}pt,margin=0pt'))
    
    if is_arabic_script:
        doc.packages.append(Package('bidi'))
    
    language_mapping_polyglossia = {
        'assamese': 'bengali', 'bodo': 'hindi', 'dogri': 'hindi', 'gujarati': 'gujarati',
        'hindi': 'hindi', 'kannada': 'kannada', 'kashmiri': 'urdu', 'konkani': 'hindi',
        'maithili': 'hindi', 'malayalam': 'malayalam', 'manipuri': 'bengali', 'marathi': 'marathi',
        'nepali': 'nepali', 'odia': 'oriya', 'punjabi': 'punjabi', 'sanskrit': 'sanskrit',
        'santali': 'hindi', 'sindhi': 'sindhi', 'tamil': 'tamil', 'telugu': 'telugu', 'urdu': 'urdu',
        'bengali': 'bengali'
    }
    
    script_mapping = {
        'assamese': 'Bengali', 'bengali': 'Bengali', 'bodo': 'Devanagari', 'dogri': 'Devanagari',
        'gujarati': 'Gujarati', 'hindi': 'Devanagari', 'kannada': 'Kannada', 'kashmiri': 'Arabic',
        'konkani': 'Devanagari', 'maithili': 'Devanagari', 'malayalam': 'Malayalam', 'manipuri': 'Bengali',
        'marathi': 'Devanagari', 'nepali': 'Devanagari', 'odia': 'Oriya', 'punjabi': 'Gurmukhi',
        'sanskrit': 'Devanagari', 'santali': 'Devanagari', 'sindhi': 'Devanagari', 'tamil': 'Tamil',
        'telugu': 'Telugu', 'urdu': 'Arabic'
    }
    
    script = script_mapping.get(language, 'Devanagari')
    polyglossia_language = language_mapping_polyglossia.get(language, language)
    
    if is_arabic_script:
        if language.lower() == 'urdu':
            doc.preamble.append(NoEscape(r'\setmainlanguage{urdu}'))
        elif language.lower() == 'kashmiri':
            doc.preamble.append(NoEscape(r'\setmainlanguage{urdu}'))
        else:
            doc.preamble.append(NoEscape(r'\setmainlanguage{arabic}'))
        doc.preamble.append(NoEscape(r'\setRTL'))
    elif language.lower() not in ['odia', 'punjabi', 'sindhi', 'nepali', 'gujarati','manipuri']:
        doc.preamble.append(NoEscape(f'\\setmainlanguage{{{polyglossia_language}}}'))
    
    doc.preamble.append(NoEscape(f'\\setotherlanguage{{english}}'))
    
    script_lowercase = script.lower().replace(' ', '')
    script_name_fixes = {
        'oriya': 'oriya', 'arabic': 'arabic', 'bengali': 'bengali', 'devanagari': 'devanagari',
        'gujarati': 'gujarati', 'gurmukhi': 'gurmukhi', 'kannada': 'kannada', 'malayalam': 'malayalam',
        'tamil': 'tamil', 'telugu': 'telugu'
    }
    script_polyglossia = script_name_fixes.get(script_lowercase, script_lowercase)
    
    if is_arabic_script:
        doc.preamble.append(NoEscape(f'\\newfontfamily\\arabicfont[Script=Arabic,Path={os.path.dirname(paragraph_font_path)}/]{{{os.path.basename(paragraph_font_path).replace(".ttf", "")}}}'))
        if language.lower() == 'urdu':
            doc.preamble.append(NoEscape(f'\\newfontfamily\\urdufont[Script=Arabic,Language=Urdu,Path={os.path.dirname(paragraph_font_path)}/]{{{os.path.basename(paragraph_font_path).replace(".ttf", "")}}}'))
        doc.preamble.append(NoEscape(f'\\newfontfamily\\headerfont[Script=Arabic,Path={os.path.dirname(header_font_path)}/]{{{os.path.basename(header_font_path).replace(".ttf", "")}}}'))
        doc.preamble.append(NoEscape(f'\\newfontfamily\\paragraphfont[Script=Arabic,Path={os.path.dirname(paragraph_font_path)}/]{{{os.path.basename(paragraph_font_path).replace(".ttf", "")}}}'))
    else:
        doc.preamble.append(NoEscape(f'\\newfontfamily\\{script_polyglossia}font[Script={script},Path={os.path.dirname(paragraph_font_path)}/]{{{os.path.basename(paragraph_font_path).replace(".ttf", "")}}}'))
        doc.preamble.append(NoEscape(f'\\newfontfamily\\headerfont[Script={script},Path={os.path.dirname(header_font_path)}/]{{{os.path.basename(header_font_path).replace(".ttf", "")}}}'))
        doc.preamble.append(NoEscape(f'\\newfontfamily\\paragraphfont[Script={script},Path={os.path.dirname(paragraph_font_path)}/]{{{os.path.basename(paragraph_font_path).replace(".ttf", "")}}}'))

    doc.preamble.append(NoEscape(r'''
    \makeatletter
    \newcommand{\zettaHuge}{\@setfontsize\zettaHuge{200}{220}}
    \newcommand{\exaHuge}{\@setfontsize\exaHuge{165}{180}}
    \newcommand{\petaHuge}{\@setfontsize\petaHuge{135}{150}}
    \newcommand{\teraHuge}{\@setfontsize\teraHuge{110}{120}}
    \newcommand{\gigaHuge}{\@setfontsize\gigaHuge{90}{100}}
    \newcommand{\megaHuge}{\@setfontsize\megaHuge{75}{85}}
    \newcommand{\superHuge}{\@setfontsize\superHuge{62}{70}}
    \newcommand{\verylarge}{\@setfontsize\verylarge{37}{42}}
    \newcommand{\veryLarge}{\@setfontsize\veryLarge{43}{49}}
    \newcommand{\veryHuge}{\@setfontsize\veryHuge{62}{70}}
    \newcommand{\alphaa}{\@setfontsize\alphaa{60}{66}}
    \newcommand{\betaa}{\@setfontsize\betaa{57}{63}}
    \newcommand{\gammaa}{\@setfontsize\gammaa{55}{61}}
    \newcommand{\deltaa}{\@setfontsize\deltaa{53}{59}}
    \newcommand{\epsilona}{\@setfontsize\epsilona{51}{57}}
    \newcommand{\zetaa}{\@setfontsize\zetaa{47}{53}}
    \newcommand{\etaa}{\@setfontsize\etaa{45}{51}}
    \newcommand{\iotaa}{\@setfontsize\iotaa{41}{47}}
    \newcommand{\kappaa}{\@setfontsize\kappaa{39}{45}}
    \newcommand{\lambdaa}{\@setfontsize\lambdaa{35}{41}}
    \newcommand{\mua}{\@setfontsize\mua{33}{39}}
    \newcommand{\nua}{\@setfontsize\nua{31}{37}}
    \newcommand{\xia}{\@setfontsize\xia{29}{35}}
    \newcommand{\pia}{\@setfontsize\pia{27}{33}}
    \newcommand{\rhoa}{\@setfontsize\rhoa{24}{30}}
    \newcommand{\sigmaa}{\@setfontsize\sigmaa{22}{28}}
    \newcommand{\taua}{\@setfontsize\taua{18}{24}}
    \newcommand{\upsilona}{\@setfontsize\upsilona{16}{22}}
    \newcommand{\phia}{\@setfontsize\phia{15}{20}}
    \newcommand{\chia}{\@setfontsize\chia{13}{18}}
    \newcommand{\psia}{\@setfontsize\psia{11}{16}}
    \newcommand{\omegaa}{\@setfontsize\omegaa{6}{7}}
    \newcommand{\oomegaa}{\@setfontsize\oomegaa{4}{5}}
    \newcommand{\ooomegaa}{\@setfontsize\ooomegaa{3}{4}}
    \newcommand{\oooomegaaa}{\@setfontsize\oooomegaaa{2}{3}}
    \makeatother
    '''))

    doc.append(NoEscape(r'\begin{center}'))
    doc.append(NoEscape(r'\begin{tikzpicture}[x=1pt, y=1pt]'))
    
    image_height, image_width = image_dimensions
    doc.append(NoEscape(f'\\node[anchor=south west, inner sep=0pt] at (0,0) {{\\includegraphics[width={image_width}pt,height={image_height}pt]{{{image_path}}}}};'))
    doc.append(NoEscape(r'\tikzset{headertext/.style={font=\headerfont, text=black}}'))
    doc.append(NoEscape(r'\tikzset{paragraphtext/.style={font=\paragraphfont, text=black}}'))

    font_sizes = list(font_size_mapping.keys())
    image = Image.open(image_path).convert('RGB')

    label_counter = {'ordered-list': 1, 'unordered-list': None, 'options': 'A'}
    label_limit = 'D'

    for bbox in bboxes:
        x1, y1, width, height, label, box_id, image_id = bbox
        ymin = image_height - (y1 + height)
        ymax = image_height - y1
        xmin = x1
        xmax = x1 + width
        padding_points = 25

        if height > 26:
            width_with_padding = width - padding_points
            height_with_padding = height
            ymin_with_padding = ymin + padding_points
            ymax_with_padding = ymax - padding_points
            xmin_with_padding = xmin
            xmax_with_padding = xmax
        else:
            width_with_padding = width - padding_points
            height_with_padding = height
            ymin_with_padding = ymin + padding_points
            ymax_with_padding = ymax - padding_points
            xmin_with_padding = xmin
            xmax_with_padding = xmax

        if width_with_padding <= 0:
            width_with_padding = 0.01
        if height_with_padding <= 0:
            height_with_padding = 0.01

        label_config = label_mapping.get(label.lower(), {"font_size": "\\Huge", "style": ""})
        if isinstance(label_config, str):
            label_config = {"font_size": "\\Huge", "style": ""}

        font_size_keys = list(font_size_mapping.keys())
        index = font_size_keys.index(label_config.get("font_size", "\\Huge")) + 1
        font_size_command = font_size_keys[index] if index < len(font_size_keys) else font_size_keys[-1]
        style_command = label_config.get("style", "")

        headline_labels = [
            "headline", "header", "sub-headline", "section-title", "sub-section-title", "dateline",
            "caption", "table caption", "table note", "editor's note", "kicker", "jump line",
            "subsub-section-title", "chapter-title", "first-level title", "second-level title",
            "third-level title", "fourth-level title", "fifth-level title", "title", "byline",
            "kicker", "subsub-headline", "folio","figure-caption"
        ]

        tikz_text_style = "headertext" if label.lower() in [hl.lower() for hl in headline_labels] else "paragraphtext"
        bbox_width_inches = width_with_padding / dpi
        bbox_height_inches = height_with_padding / dpi

        if label not in ["header", "footer", "formula", "QR code", "table", "page-number", "figure", "page_number", "mugshot", "code", "correlation", "bracket", "examinee info", "sealing line", "weather forecast", "barcode", "bill", "advertisement", "underscore", "blank", "other question number", "second-level-question number", "third-level question number", "first-level-question"]:
            if label.lower() == "dateline":
                dateline_path = os.path.join("Datelines", f"{language}.txt")
                try:
                    with open(dateline_path, 'r', encoding='utf-8') as file:
                        dateline_lines = [line.strip() for line in file.readlines() if line.strip()]
                except FileNotFoundError:
                    print(f"Dateline file {dateline_path} not found for {language}.")
                    dateline_lines = []

                if dateline_lines:
                    random_line = random.choice(dateline_lines)
                    font_size_command = font_size_mapping.get('dateline', '\\LARGE')
                    index = font_size_keys.index(font_size_command) + 1
                    font_size_command = font_size_keys[index] if index < len(font_size_keys) else font_size_keys[-1]
                    style_command = ""

                    # hindi_text_to_fit = estimate_text_to_fit(
                    #     random_line, bbox_width_inches, bbox_height_inches, box_id,
                    #     language, x1, y1, font_size_command, bboxes, dpi, paragraph_font_path, image_name, image_height, image_width, input_text_folder
                    # )

                    # if not hindi_text_to_fit:
                    #     for font_size in font_sizes[font_sizes.index(font_size_command) + 1:]:
                    #         hindi_text_to_fit = estimate_text_to_fit(
                    #             random_line, bbox_width_inches, bbox_height_inches, box_id,
                    #             language, x1, y1, font_size, bboxes, dpi, paragraph_font_path, image_name, image_height, image_width, input_text_folder
                    #         )
                    #         if hindi_text_to_fit:
                    #             font_size_command = font_size
                    #             break
                    # print(label)
                    if random_line:
                        font_size_pts = font_size_mapping.get(font_size_command, 10)
                        baseline_skip = font_size_pts * 1.1
                        alignment = 'right' if is_arabic_script else 'left'
                        if is_arabic_script:
                            doc.append(NoEscape(
                                f'\\node[{tikz_text_style}, anchor=north west, text width={width-5}pt, align={alignment}]'
                                f'at ({xmin}, {ymax + 0}) '
                                f'{{\\beginR\\setlength{{\\baselineskip}}{{{baseline_skip}pt}} {font_size_command} {style_command} {random_line}\\endR}};'
                            ))
                        else:
                            doc.append(NoEscape(
                                f'\\node[{tikz_text_style}, anchor=north west, text width={width-5}pt, align={alignment}]'
                                f'at ({xmin}, {ymax + 0}) '
                                f'{{\\setlength{{\\baselineskip}}{{{baseline_skip}pt}} {font_size_command} {style_command} {random_line}}};'
                            ))
                    else:
                        print(f"Dateline text does not fit for {language}.")
                else:
                    print(f"No valid dateline content for {language}.")
            elif label.lower() in ["ordered-list", "unordered-list", "catalogue", "options", "sub-ordered-list", "subsub-ordered-list", "sub-unordered-list", "subsub-unordered-list"]:
                label_config = label_mapping.get(label.lower(), {"font_size": "\\Huge", "style": ""})
                if isinstance(label_config, str):
                    label_config = {"font_size": "\\Huge", "style": ""}

                font_size_keys = list(font_size_mapping.keys())
                index = font_size_keys.index(label_config.get("font_size", "\\Large")) + 4
                font_size_command = font_size_keys[index] if index < len(font_size_keys) else font_size_keys[-1]
                style_command = label_config.get("style", "")

                estimated_text = estimate_text_to_fit(
                    ' '.join(texts), bbox_width_inches, bbox_height_inches, box_id,
                    language, x1, y1, font_size_command, bboxes, dpi, paragraph_font_path, image_name, image_height, image_width, input_text_folder
                )
                estimated_lines = estimated_text.split('\\linebreak')

                if label.lower() in ["ordered-list", "sub-ordered-list", "subsub-ordered-list"]:
                    prefix_format = lambda idx: f"{label_counter['ordered-list']}. "
                    label_counter['ordered-list'] += 1
                elif label.lower() in ["unordered-list", "sub-unordered-list", "subsub-unordered-list"]:
                    prefix_format = lambda idx: "• "
                elif label.lower() == "options":
                    current_counter = label_counter['options']
                    prefix_format = lambda idx: f"{current_counter}. "
                    if current_counter == label_limit:
                        label_counter['options'] = 'A'
                    else:
                        label_counter['options'] = chr(ord(current_counter) + 1)
                else:
                    prefix_format = lambda idx: ""
                # print(label)
                enumerated_lines = [f"{prefix_format(idx)}{line.strip()}" for idx, line in enumerate(estimated_lines) if line.strip()]
                formatted_text = '\\linebreak'.join(enumerated_lines)
                alignment = 'right' if is_arabic_script else 'left'
                if is_arabic_script:
                    doc.append(NoEscape(
                        f'\\node[paragraphtext, anchor=north west, text width={width-5}pt, align={alignment}] at ({xmin},{ymax+3.5}) '
                        f'{{\\beginR {font_size_command}{{{formatted_text}}}\\endR}};'
                    ))
                else:
                    doc.append(NoEscape(
                        f'\\node[paragraphtext, anchor=north west, text width={width-5}pt, align={alignment}] at ({xmin},{ymax+3.5}) '
                        f'{{{font_size_command}{{{formatted_text}}}}};'
                    ))
            elif (label.lower() not in ["index", "formula", "figure_1", "formula_1", "header", "headline", "sub-headline", "options", "figure", "credit", "dateline", "table_row1_col1", "table_row1_col2", "table_row1_col3"]):
                if label.lower().startswith("paragraph") or label.lower() in ["answer", "table caption", "caption"]:
                    if width_with_padding <= 35:
                        continue
                    alignment = 'justify'
                else:
                    alignment = 'left'
                if is_arabic_script:
                    alignment = 'right'

                label_config = label_mapping.get(label.lower(), {"font_size": "\\Large", "style": ""})
                if isinstance(label_config, str):
                    label_config = {"font_size": "\\Large", "style": ""}

                font_size_keys = list(font_size_mapping.keys())
                index = font_size_keys.index(label_config.get("font_size", "\\Large")) + 4
                font_size_command = font_size_keys[index] if index < len(font_size_keys) else font_size_keys[-1]
                style_command = label_config.get("style", "")

                hindi_text_to_fit = estimate_text_to_fit(
                    ' '.join(texts), bbox_width_inches, bbox_height_inches, box_id,
                    language, x1, y1, font_size_command, bboxes, dpi, paragraph_font_path, image_name, image_height, image_width, input_text_folder
                )

                if not hindi_text_to_fit:
                    for font_size in font_sizes[font_sizes.index(font_size_command) + 1:]:
                        hindi_text_to_fit = estimate_text_to_fit(
                            ' '.join(texts), bbox_width_inches, bbox_height_inches, box_id,
                            language, x1, y1, font_size, bboxes, dpi, paragraph_font_path, image_name, image_height, image_width, input_text_folder
                        )
                        if hindi_text_to_fit:
                            font_size_command = font_size
                            break

                font_size_pts = font_size_mapping.get(font_size_command, 10)
                baseline_skip = font_size_pts * 1.1
                # print(label)
                if is_arabic_script:
                    doc.append(NoEscape(
                        f'\\node[{tikz_text_style}, anchor=north west, text width={width-5}pt, align={alignment}] '
                        f'at ({xmin},{ymax+3.5})'
                        f'{{\\beginR\\setlength{{\\baselineskip}}{{{baseline_skip}pt}} \\par\n'
                        f'{font_size_command} {style_command}{{{hindi_text_to_fit}}}\\endR}};'
                    ))
                else:
                    doc.append(NoEscape(
                        f'\\node[{tikz_text_style}, anchor=north west, text width={width-5}pt, align={alignment}] '
                        f'at ({xmin},{ymax+3.5})'
                        f'{{\\setlength{{\\baselineskip}}{{{baseline_skip}pt}} \\par\n'
                        f'{font_size_command} {style_command}{{{hindi_text_to_fit}}}}};'
                    ))
            elif label in ["headline", "sub-headline", "credit"] and height < width:
                label_config = label_mapping.get(label.lower(), {"font_size": "", "style": ""})
                if isinstance(label_config, str):
                    label_config = {"font_size": "", "style": ""}

                font_size_keys = list(font_size_mapping.keys())
                index = font_size_keys.index(label_config.get("font_size", "\\Large")) + 4
                font_size_command = font_size_keys[index] if index < len(font_size_keys) else font_size_keys[-1]
                style_command = label_config.get("style", "")

                hindi_text_to_fit = estimate_text_to_fit(
                    ' '.join(texts), bbox_width_inches, bbox_height_inches, box_id,
                    language, x1, y1, font_size_command, bboxes, dpi, header_font_path, image_name, image_height, image_width, input_text_folder
                )

                if not hindi_text_to_fit:
                    for font_size in font_sizes[font_sizes.index(font_size_command) + 1:]:
                        hindi_text_to_fit = estimate_text_to_fit(
                            ' '.join(texts), bbox_width_inches, bbox_height_inches, box_id,
                            language, x1, y1, font_size, bboxes, dpi, header_font_path, image_name, image_height, image_width, input_text_folder
                        )
                        if hindi_text_to_fit:
                            font_size_command = font_size
                            break

                if not hindi_text_to_fit:
                    index = font_size_keys.index("\\large") + 1
                    font_size_command = font_size_keys[index] if index < len(font_size_keys) else font_size_keys[-1]
                    hindi_text_to_fit = estimate_text_to_fit(
                        ' '.join(texts), bbox_width_inches, bbox_height_inches, box_id,
                        language, x1, y1, font_size_command, bboxes, dpi, header_font_path, image_name, image_height, image_width, input_text_folder
                    )
                    if not hindi_text_to_fit:
                        hindi_text_to_fit = " "

                font_size_pts = font_size_mapping.get(font_size_command, 10)
                baseline_skip = font_size_pts * 1.1
                color_str = 'text=black'
                alignment = 'right' if is_arabic_script else 'left'
                # print(label)
                if is_arabic_script:
                    doc.append(NoEscape(
                        f'\\node[{tikz_text_style}, anchor=north west, text width={width-5}pt, align={alignment}, {color_str}] '
                        f'at ({xmin},{ymax+3.5})'
                        f'{{\\beginR\\setlength{{\\baselineskip}}{{{baseline_skip}pt}} \\par\n'
                        f'{font_size_command} {style_command}{{{hindi_text_to_fit}}}\\endR}};'
                    ))
                else:
                    doc.append(NoEscape(
                        f'\\node[{tikz_text_style}, anchor=north west, text width={width-5}pt, align={alignment}, {color_str}] '
                        f'at ({xmin},{ymax+3.5})'
                        f'{{\\setlength{{\\baselineskip}}{{{baseline_skip}pt}} \\par\n'
                        f'{font_size_command} {style_command}{{{hindi_text_to_fit}}}}};'
                    ))

    doc.append(NoEscape(r'\end{tikzpicture}'))
    doc.append(NoEscape(r'\end{center}'))
    return doc.dumps()

def read_bboxes_from_file(file_path):
    file_path = os.path.abspath(file_path)
    bboxes = []
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            try:
                match = re.match(r'^\[([^\[\],]+?),\s*\[\s*(\d+(\.\d+)?)\s*,\s*(\d+(\.\d+)?)\s*,\s*(\d+(\.\d+)?)\s*,\s*(\d+(\.\d+)?)\s*\],\s*([^\[\],]+?),\s*([^\[\],]+?)\]$', line.strip())
                if not match:
                    continue
                label = match.group(1).strip().strip('"')
                bbox_values = [float(match.group(i)) for i in range(2, 10, 2)]
                annotation_id = match.group(9).strip()
                image_id = match.group(10).strip()
                bboxes.append((label, bbox_values, annotation_id, image_id))
            except Exception as e:
                print(f"Error processing line '{line}': {e}")
    return bboxes

def find_closest_font_size(height, font_size_mapping):
    valid_sizes = {size: value for size, value in font_size_mapping.items() if value <= height}
    if not valid_sizes:
        return None
    return max(valid_sizes, key=lambda size: font_size_mapping[size])

def set_font_size_per_category(bboxes, font_size_mapping):
    category_to_heights = defaultdict(list)
    for label, coords, bbox_id, _ in bboxes:
        height = coords[3]
        category_to_heights[label].append(height)

    category_font_sizes = {}
    for category, heights in category_to_heights.items():
        min_height = min(heights)
        closest_font_size = find_closest_font_size(min_height, font_size_mapping)
        if closest_font_size:
            category_font_sizes[category] = closest_font_size
        else:
            print(f"Category '{category}' has no suitable font size for height {min_height}.")
    return category_font_sizes

def process_image_and_bboxes(bbox_file_path, image_path):
    image_path = os.path.abspath(image_path)
    bbox_file_path = os.path.abspath(bbox_file_path)
    
    with Image.open(image_path) as img:
        image_width, image_height = img.size
    if image_height > 3500:
        label_mapping = label_mapping_1
    elif 2500 <= image_height <= 3000:
        label_mapping = label_mapping_2
    elif 2000 <= image_height < 2500:
        label_mapping = label_mapping_3
    elif 1500 <= image_height < 2000:
        label_mapping = label_mapping_4
    elif 500 <= image_height < 1500:
        label_mapping = label_mapping_5
    else:
        label_mapping = label_mapping_default
    bboxes = read_bboxes_from_file(bbox_file_path)
    return bboxes, label_mapping

import argparse
import time
import os
import sys
def parse_arguments():
    """Parse command line arguments for language selection, text file, input text folder, and file count."""
    parser = argparse.ArgumentParser(
        description='Generate LaTeX documents with support for multiple languages, including Arabic script languages.'
    )
    
    parser.add_argument(
        '--languages', 
        nargs='+', 
        default=['urdu', 'kashmiri'],
        help='List of languages to process. Default: urdu kashmiri'
    )
    
    parser.add_argument(
        '--text-file',
        type=str,
        help='Path to the text file containing input text. If not provided, defaults to input_text_folder/input_1/{language}.txt'
    )
    
    parser.add_argument(
        '--input-text-folder',
        type=str,
        default='input_texts',
        help='Path to the folder containing input text subfolders (input_1, input_2). Default: input_texts'
    )
    
    parser.add_argument(
        '--file-count',
        type=int,
        default=None,
        help='Number of files to generate for each language. If not provided, processes all available files.'
    )
    
    return parser.parse_args()

def main():
    args = parse_arguments()
    languages = args.languages
    input_text_folder = args.input_text_folder
    file_count = args.file_count
    
    print(f"Processing the following languages: {', '.join(languages)}")
    print(f"Using input text folder: {input_text_folder}")
    if file_count is not None:
        print(f"Generating up to {file_count} files per language")
    else:
        print("Generating all available files per language")
    
    start_time = time.time()

    bbox_files_and_paths = get_bboxes_and_image_path()
    total_files = len(bbox_files_and_paths)
    
    if not bbox_files_and_paths:
        print("No bounding box or image files found. Exiting.")
        return

    # Distribute files across languages
    for lang_idx, language in enumerate(languages):
        print(f"Processing language: {language}")
        text_file = args.text_file if args.text_file else os.path.join(input_text_folder, "input_1", f"{language}.txt")
        
        if not args.text_file and not os.path.exists(text_file):
            print(f"Text file {text_file} not found for {language}. Skipping.")
            continue

        # Calculate start index for this language to ensure different files
        files_to_process = []
        if file_count is None:
            # If no file-count specified, use all files for each language
            files_to_process = bbox_files_and_paths
        else:
            # Assign files in a round-robin fashion
            for i in range(file_count):
                file_idx = (lang_idx + i * len(languages)) % total_files
                files_to_process.append(bbox_files_and_paths[file_idx])
        
        print(f"Processing {len(files_to_process)} files for {language}")
        
        for bbox_file_path, image_path in files_to_process:
            bboxes, label_mapping = process_image_and_bboxes(bbox_file_path, image_path)
            font_size_by_label = set_font_size_per_category(bboxes, font_size_mapping)

            for label, font_size in font_size_by_label.items():
                if label in label_mapping:
                    label_mapping[label]["font_size"] = font_size

            extract_dimensions_and_text_from_file(image_path, bbox_file_path, language, label_mapping, input_text_folder)

    end_time = time.time()
    execution_time = end_time - start_time
    print(f"Total Execution Time: {execution_time} seconds")
if __name__ == "__main__":
    main()
