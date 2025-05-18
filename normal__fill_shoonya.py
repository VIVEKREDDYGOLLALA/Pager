import textwrap
import random
import requests
from io import BytesIO
import time
from pylatex import Document, NoEscape, Package
from pylatex.base_classes import Environment
from PIL import ImageFont, ImageDraw, Image
import numpy as np
from sklearn.cluster import KMeans
from collections import Counter
import os
import re
import json
import ast
import math
from PIL import Image
from label_mapping import label_mapping_1, label_mapping_2, label_mapping_3, label_mapping_4, label_mapping_5, label_mapping_default


asterisk_added = {}
start_time = time.time()

class Center(Environment):
    packages = [Package('amsmath')]
    _latex_name = 'center'

# Global variable to store JSON annotations
output_json = {
    "annotations": []
}

font_size_mapping = {
    '\\zettaHuge': 200, '\\exaHuge': 165, '\\petaHuge': 135, '\\teraHuge': 110, '\\gigaHuge': 90,
    '\\megaHuge': 75, '\\superHuge': 62, '\\veryHuge': 49, '\\veryLarge': 43, '\\verylarge': 37,
    '\\Huge': 25, '\\huge': 20, '\\LARGE': 17, '\\Large': 15, '\\large': 12,
    '\\normalsize': 10, '\\small': 9, '\\footnotesize': 8, '\\scriptsize': 7, '\\tiny': 5,
    '\\alphaa': 60, '\\betaa': 57, '\\gammaa': 55, '\\deltaa': 53, '\\epsilona': 51,
    '\\zetaa': 47, '\\etaa': 45, '\\iotaa': 41, '\\kappaa': 39, '\\lambdaa': 35,
    '\\mua': 33, '\\nua': 31, '\\xia': 29, '\\pia': 27, '\\rhoa': 24,
    '\\sigmaa': 22, '\\taua': 18, '\\upsilona': 16, '\\phia': 15, '\\chia': 13,
    '\\psia': 11, '\\omegaa': 6, '\\oomegaa': 4, '\\ooomegaa': 3, '\\oooomegaaa': 2
}

def estimate_text_to_fit(hindi_text, bbox_width_inches, bbox_height_inches, box_id, output_json_path, x1, y1, font_size, bboxes, dpi):
    output_folder_path = 'output_jsons2' 
    os.makedirs(output_folder_path, exist_ok=True) 
    # print(font_size)
    font_path = r"fonts/bengali/Header/Atma-Bold.ttf"
    
    base_dpi = 72

    point_size = font_size_mapping.get(font_size, 12)
    # print(point_size)
    if point_size <= 0:
        # print(f"Warning: Invalid font size {point_size}. Using default size 12.")
        point_size = 18 # Set to a default size if calculation results in 0 or negative value

    font = ImageFont.truetype(font_path, int(point_size))

    img = Image.new('RGB', (int(bbox_width_inches * dpi), int(bbox_height_inches * dpi)), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    words = hindi_text.split()

    while True:
        random_start = random.randint(0, max(0, len(words) - 1))
        rotated_words = words[random_start:] + words[:random_start]
        if rotated_words:
            words = rotated_words
            break

    truncated_text_lines = []
    truncated_text_with_linebreaks = []
    current_line = ''
    current_line_width = 0

    line_height = point_size * 1.5
    adjusted_line_height = point_size * 1.5
    # print(adjusted_line_height)
    max_lines = int(bbox_height_inches * dpi / line_height)

    if max_lines > 3:
        max_lines = int(bbox_height_inches * dpi / adjusted_line_height)

    for word in words:
        word_bbox = draw.textbbox((0, 0), word, font=font)
        word_width = word_bbox[2] - word_bbox[0]
        space_bbox = draw.textbbox((0, 0), ' ', font=font)
        space_width = space_bbox[2] - space_bbox[0]
        new_line_width = current_line_width + space_width + word_width if current_line else word_width

        if word_width > bbox_width_inches * dpi:
            # print(f"Warning: Word '{word}' is too wide to fit in the box. Making truncated lines empty.")
            truncated_text_lines.clear() 
            truncated_text_with_linebreaks.clear()  
            break 
        
        if new_line_width <= bbox_width_inches * dpi:
            if current_line:
                current_line += ' ' + word
                current_line_width = new_line_width
            else:
                current_line = word
                current_line_width = word_width
        else:
            truncated_text_lines.append(current_line)
            truncated_text_with_linebreaks.append(current_line + r'\linebreak')
            current_line = word
            current_line_width = word_width
            if len(truncated_text_lines) >= max_lines:
                break

    if current_line and len(truncated_text_lines) < max_lines:
        truncated_text_lines.append(current_line)
        truncated_text_with_linebreaks.append(current_line + r'\linebreak')

    if not truncated_text_lines:
        # print("No text fits. Reading words from 'single.txt'...")
        try:
            with open("single.txt", "r", encoding="utf-8") as f:
                words = f.read().split()
        except FileNotFoundError:
            # print("Error: 'single.txt' not found. Using placeholder text.")
            words = ["..."]

        current_line = ''
        current_line_width = 0

        for word in words:
            word_bbox = draw.textbbox((0, 0), word, font=font)
            word_width = word_bbox[2] - word_bbox[0]
            space_bbox = draw.textbbox((0, 0), ' ', font=font)
            space_width = space_bbox[2] - space_bbox[0]
            new_line_width = current_line_width + space_width + word_width if current_line else word_width

            if word_width > bbox_width_inches * dpi:
                # print(f"Warning: Word '{word}' is too wide to fit in the box. Making truncated lines empty.")
                truncated_text_lines.clear() 
                truncated_text_with_linebreaks.clear()  
                break 

            if new_line_width <= bbox_width_inches * dpi:
                if current_line:
                    current_line += ' ' + word
                    current_line_width = new_line_width
                else:
                    current_line = word
                    current_line_width = word_width
            else:
                truncated_text_lines.append(current_line)
                truncated_text_with_linebreaks.append(current_line + r'\linebreak')
                current_line = word
                current_line_width = word_width
                if len(truncated_text_lines) >= max_lines:
                    break

        if current_line and len(truncated_text_lines) < max_lines:
            truncated_text_lines.append(current_line)
            truncated_text_with_linebreaks.append(current_line + r'\linebreak')

    current_box = next((bbox for bbox in bboxes if bbox[5] == box_id), None)
    if current_box and max_lines > 0 and '\n'.join(truncated_text_with_linebreaks[:max_lines]):
        image_id = current_box[6]
        label = current_box[4]

        annotation = {
            "id": box_id,
            "image_id": image_id,
            "label": label,
            "bbox": {
                "x1": x1,
                "y1": y1,
                "width": bbox_width_inches * dpi,
                "height": bbox_height_inches * dpi
            },
            "textlines": []
        }

        for idx, line in enumerate(truncated_text_lines):
            annotation['textlines'].append({
                "line_idx": idx,
                "bbox": [x1, y1 + idx * adjusted_line_height, bbox_width_inches * dpi, adjusted_line_height],
            })

        image_json_file = os.path.join(output_folder_path, f"{image_id}.json")

        if os.path.exists(image_json_file):
            with open(image_json_file, 'r', encoding='utf-8') as json_file:
                try:
                    existing_data = json.load(json_file)
                except json.JSONDecodeError:
                    existing_data = {"annotations": []}
        else:
            existing_data = {"annotations": []}

        if not any(ann["id"] == box_id for ann in existing_data["annotations"]):
            existing_data["annotations"].append(annotation)

            try:
                with open(image_json_file, 'w', encoding='utf-8') as json_file:
                    json.dump(existing_data, json_file, indent=4, ensure_ascii=False)
            except Exception as e:
                print(f"Error creating JSON file: {e}")

    return '\n'.join(truncated_text_with_linebreaks[:max_lines])


def get_patch_color_with_gradient(image, bbox):
    # Use the floating-point values directly
    x1, y1, width, height = bbox[:4]
    
    corners = [
        (x1, y1),  # Top-left
        (x1 + width, y1),  # Top-right
        (x1, y1 + height),  # Bottom-left
        (x1 + width, y1 + height)  # Bottom-right
    ]

    # Get image dimensions
    image_width, image_height = image.size

    # Check for valid corners and handle out-of-bound cases
    valid_corners = []
    for corner in corners:
        cx, cy = corner
        # Ensure that the corner coordinates are within the image bounds
        if 0 <= cx < image_width and 0 <= cy < image_height:
            valid_corners.append(corner)
        else:
            print(f"Skipping out-of-bound corner: {corner}")

    # If we don't have enough valid corners, we cannot proceed
    if len(valid_corners) < 2:
        # print("Skipping bounding box due to insufficient valid corners.")
        return None, None, None  # Return None when corners are out of bounds

    # Get pixel colors for valid corners
    corner_colors = [image.getpixel(corner) for corner in valid_corners]
    
    # Ensure we have enough colors to determine the gradient
    if len(corner_colors) < 2:
        # print("Not enough valid corner colors to determine gradient.")
        return None, None, None

    # Defaulting to first two colors to determine gradient (if more than two corners are valid)
    top_left = corner_colors[0]
    top_right = corner_colors[0] if len(corner_colors) < 2 else corner_colors[1]
    bottom_left = corner_colors[0] if len(corner_colors) < 2 else corner_colors[1]
    bottom_right = corner_colors[0] if len(corner_colors) < 2 else corner_colors[1]

    # Determine gradient type and colors
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
    from collections import Counter
    import numpy as np

    x1, y1, width, height = bbox[:4]
    patch = image.crop((x1, y1, x1 + width, y1 + height))
    patch_data = np.array(patch).reshape(-1, 3)
    color_counts = Counter(map(tuple, patch_data))
    most_common_colors = color_counts.most_common(n_colors)
    dominant_colors = [color for color, count in most_common_colors]
    
    # Fallback if not enough colors are available
    while len(dominant_colors) < n_colors:
        dominant_colors.append((0, 0, 0))  # Append black as the fallback color
    
    return dominant_colors

def choose_text_color(bg_color, dominant_colors):
    import numpy as np

    tolerance = 10
    percentage_tolerance = 0.25
    black_color = np.array([0, 0, 0])
    bg_color = np.array(bg_color)
    dominant_colors = [np.array(color) for color in dominant_colors]

    def is_similar_color(color1, color2, tolerance, percentage_tolerance):
        abs_diff = np.abs(color1 - color2)
        relative_diff = abs_diff / 255.0 
        return np.all(relative_diff <= percentage_tolerance) or np.all(abs_diff <= tolerance)

    # Ensure at least one valid color is chosen
    if len(dominant_colors) > 1 and not is_similar_color(dominant_colors[1], bg_color, tolerance, percentage_tolerance):
        chosen_color = dominant_colors[1]
    elif len(dominant_colors) > 0 and not is_similar_color(dominant_colors[0], bg_color, tolerance, percentage_tolerance):
        chosen_color = dominant_colors[0]
    else:
        chosen_color = black_color

    if is_similar_color(chosen_color, bg_color, tolerance, percentage_tolerance):
        return black_color

    return chosen_color


def rgb_to_normalized(rgb):
    return [val / 255.0 for val in rgb]


def extract_dimensions_and_text_from_file(image_path, file_path, hindi_text_file, label_mapping):
    # Read the entire file and split the lines
    with open(file_path, 'r') as file:
        lines = file.readlines()
    
    # The first line contains the image dimensions in physical units (inches)
    image_dimensions_line = lines[0].strip()
    
    # Ensure we only attempt to parse image dimensions
    image_dimensions = eval(image_dimensions_line)  # Example: [9.5, 6.5] in inches
    if not isinstance(image_dimensions, list) or len(image_dimensions) != 2:
        raise ValueError(f"Invalid image dimensions: {image_dimensions}")

    # Get image pixel dimensions using PIL
    with Image.open(image_path) as img:
        pixel_width, pixel_height = img.size

    # Calculate diagonal in pixels and inches
    diagonal_pixels = math.sqrt(pixel_width**2 + pixel_height**2)
    diagonal_inches = math.sqrt(image_dimensions[0]**2 + image_dimensions[1]**2)

    # Calculate DPI
    dpi = diagonal_pixels / diagonal_inches

    # Process remaining lines as bounding boxes
    box_details = lines[1:]  # Skip the first line (image dimensions)
    
    bboxes = []
    for line in box_details:
        if line.strip():
            # Updated regex pattern to match label, bbox dimensions, annotation ID, and optional image ID
            match = re.match(r'^\[([^\[\],]+?),\s*\[\s*(\d+(\.\d+)?)\s*,\s*(\d+(\.\d+)?)\s*,\s*(\d+(\.\d+)?)\s*,\s*(\d+(\.\d+)?)\s*\],\s*([^\[\],]+?),\s*(\S+)\]$', line.strip())

            if not match:
                # print(f"Skipping malformed line (regex match failed): {line.strip()}")
                continue

            try:
                # Extract label
                label = match.group(1).strip().strip('"')
                
                # Extract bounding box values (x1, y1, width, height)
                dimensions = [float(match.group(i)) for i in [2, 4, 6, 8]]  # Extract float values for dimensions
                
                # Extract annotation_id and image_id as strings
                annotation_id = match.group(10).strip()
                image_id = match.group(11).strip()
                
                if len(dimensions) == 4:
                    x1, y1, width, height = dimensions
                    # Append bounding box details to the list
                    bboxes.append([x1, y1, width, height, label, annotation_id, image_id])
            
            except Exception as e:
                print(f"Error processing line '{line.strip()}': {e}")

    # Read Hindi texts
    hindi_texts = []
    with open(hindi_text_file, 'r', encoding='utf-8') as file:
        hindi_texts = file.read().splitlines()

    # Generate LaTeX code (apply uniform font size for 'paragraph' and 'answer' labels)
    latex_code = generate_latex(image_path, image_dimensions, bboxes, hindi_texts, label_mapping, dpi)

    # Prepare output folder and file paths
    # base_path = 'Tex_files_label22'
    # subfolder_name = os.path.splitext(os.path.basename(file_path))[0]
    # output_folder = os.path.join(base_path, subfolder_name)
    # os.makedirs(output_folder, exist_ok=True)

    # Save LaTeX file with the image file name
    # image_file_name = os.path.splitext(os.path.basename(image_path))[0]
    # latex_output_file = os.path.join(output_folder, f"{image_file_name}.tex")
    # with open(latex_output_file, "w", encoding='utf-8') as output_file:
    #     output_file.write(latex_code)


def get_bboxes_and_image_path(base_path):
    bbox_dir = os.path.join(base_path, 'BBOX')
    image_dir = os.path.join(base_path, 'images_val')

    if not os.path.exists(bbox_dir):
        print(f"Warning: Directory not found: {bbox_dir}. Skipping...")
        return []  # Skip processing if bbox directory is missing

    bbox_files_and_paths = []
    for subdir, _, files in os.walk(bbox_dir):
        bbox_files = [f for f in files if f.endswith('.txt')]

        for bbox_file in bbox_files:
            bbox_file_path = os.path.join(subdir, bbox_file)

            # Extract file name without extension
            file_name_with_id = os.path.basename(bbox_file).replace('.txt', '')
            file_name = "_".join(file_name_with_id.split('_')[:-1])
            image_name = file_name + '.png'
            image_path = os.path.join(image_dir, image_name)

            # Check if the corresponding image exists
            if os.path.exists(image_path) and not os.path.basename(image_path).startswith('._'):
                bbox_files_and_paths.append((bbox_file_path, image_path))
            else:
                print(f"Warning: Missing image file for {bbox_file}. Skipping...")

    if not bbox_files_and_paths:
        print("Warning: No matching bounding box or image file found. Skipping processing.")

    return bbox_files_and_paths


def split_into_sentences(text):
    sentence_endings = re.compile(r'(?<=[.!?।])\s+')
    sentences = sentence_endings.split(text.strip())
    return sentences


header_fonts_dir = "fonts/bengali/Header"
paragraph_fonts_dir = "fonts/bengali/Paragraph"

# Function to randomly select a font file from a directory
def get_random_font(fonts_dir):
    fonts = [f for f in os.listdir(fonts_dir) if f.endswith('.ttf')]
    if not fonts:
        raise FileNotFoundError(f"No .ttf files found in directory: {fonts_dir}")
    return random.choice(fonts)



def generate_latex(image_path, image_dimensions, bboxes, hindi_texts, label_mapping,dpi):
    header_font = get_random_font(header_fonts_dir)
    paragraph_font = get_random_font(paragraph_fonts_dir)
    doc = Document(documentclass='article')

    # Import necessary packages
    doc.packages.append(Package('tikz'))
    doc.packages.append(Package('fontspec'))

    # Define Arabic font settings
    doc.packages.append(NoEscape(f'\\newfontfamily\\headerfont[Script=Devanagari]{{{header_font}}}'))
    doc.packages.append(NoEscape(f'\\newfontfamily\\paragraphfont[Script=Devanagari]{{{paragraph_font}}}'))


    # Set geometry for custom page dimensions
    doc.packages.append(Package('geometry', options=f'paperwidth={image_dimensions[1]}pt,paperheight={image_dimensions[0]}pt,margin=0pt'))

    doc.append(NoEscape(r'''

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

    font_sizes = [
        '\\zettaHuge', '\\exaHuge', '\\petaHuge', '\\teraHuge', '\\gigaHuge', '\\megaHuge', '\\superHuge', 
        '\\veryHuge', '\\alphaa', '\\betaa', '\\gammaa', '\\deltaa', '\\epsilona','\\zetaa', 
        '\\etaa', '\\veryLarge', '\\iotaa', '\\kappaa', '\\verylarge', '\\lambdaa', '\\mua', '\\nua', '\\xia', 
        '\\pia', '\\Huge', '\\rhoa', '\\sigmaa', '\\huge', '\\taua', '\\upsilona', '\\LARGE', '\\phia', '\\Large', 
        '\\chia', '\\large', '\\psia', '\\normalsize', '\\small', '\\footnotesize', '\\ooomegaa', '\\scriptsize', 
        '\\omegaa', '\\tiny', '\\oomegaa', '\\oooomegaaa'
    ]

    image = Image.open(image_path).convert('RGB')
    padding_points = 0
    label_counter = {'ordered-list': 1, 'unordered-list': None, 'options': 'A'}
    label_limit = 'D'  # The label resets after 'D' for option type
    for bbox in bboxes:
        x1, y1, width, height, label, box_id,image_id = bbox
        ymin = image_height - (y1 + height)
        ymax = image_height - y1 
        xmin = x1
        xmax = x1 + width

        # Add padding only if the height is greater than 13 points
        if height > 26:
            width_with_padding = width - padding_points
            height_with_padding = height- padding_points
            ymin_with_padding = ymin + padding_points
            ymax_with_padding = ymax - padding_points
            xmin_with_padding = xmin + padding_points
            xmax_with_padding = xmax - padding_points

            if width_with_padding <= 0:
                width_with_padding = 0.01

            if height_with_padding <= 0:
                height_with_padding = 0.01
        else:
            width_with_padding = width - padding_points
            height_with_padding = height
            ymin_with_padding = ymin
            ymax_with_padding = ymax
            xmin_with_padding = xmin
            xmax_with_padding = xmax

            if width_with_padding <= 0:
                width_with_padding = 0.01

            if height_with_padding <= 0:
                height_with_padding = 0.01

        label_config = label_mapping.get(label.lower(), {"font_size": "\\Huge", "style": ""})
        if isinstance(label_config, str):
            label_config = {"font_size": "\\Huge", "style": ""}
            
        font_size_command = label_config.get("font_size", "\\Huge")
        style_command = label_config.get("style", "")

        headline_labels = [
            "headline", "header", "sub-headline", "section-title", "sub-section-title", "author","dateline","caption","table caption","table note","editor's note","kicker","junp line",
            "subsub-section-title", "chapter-title", "first-level title", "second-level title", 
            "third-level title", "fourth-level title", "fifth-level title", "title", "byline", 
            "kicker","subsub-headline"
        ]

        tikz_text_style = (
            "headertext" if label.lower() in [hl.lower() for hl in headline_labels] else "paragraphtext"
        )

        bbox_width_inches = width_with_padding / dpi
        bbox_height_inches = height_with_padding / dpi

        if label not in ["header","footer","figure_1","unknown", "formula", "formula_1", "QR code", "table", "page-number", "figure", "page_number", "mugshot", "code", "correlation", "bracket", "examinee info", "sealing line", "weather forecast", "barcode", "bill", "advertisement", "underscore", "blank", "other question number", "second-level-question number", "third-level question number", "first-level-question"]:
            if label.lower() == "dateline":
                def read_datelines_as_lines(filename="datelines.txt"):
                    """Read the datelines.txt file and return the content as a list of lines."""
                    try:
                        with open(filename, 'r') as file:
                            lines = file.readlines()
                            if not lines:
                                print("The datelines file is empty.")
                            else:
                                print(f"Dateline lines read from file: {len(lines)} lines")
                        return [line.strip() for line in lines if line.strip()]  # Remove empty lines and strip whitespace
                    except FileNotFoundError:
                        # print(f"File {filename} not found.")
                        return []
                    except Exception as e:
                        # print(f"An error occurred while reading the file: {e}")
                        return []

                # Fetch the dateline lines
                dateline_lines = read_datelines_as_lines()

                if dateline_lines:
                    # Randomly select one line
                    random_line = random.choice(dateline_lines)

                    # Font size mapping for dateline
                    font_size_keys = list(font_size_mapping.keys())  
                    index = font_size_keys.index(label_config.get("font_size", "\\Large"))-1
                    font_size_command = font_size_keys[index] if index < len(font_size_keys) else font_size_keys[-1] 
                    style_command = label_config.get("style", "")
                    

                    # Estimate fitting text for the selected dateline line
                    hindi_text_to_fit = estimate_text_to_fit(
                        random_line, bbox_width_inches, bbox_height_inches, box_id,
                        json_file_path, x1, y1, font_size_command, bboxes,dpi
                    )

                    # If the line does not fit, reduce the font size dynamically
                    if not hindi_text_to_fit:
                        for font_size in font_sizes[font_sizes.index(font_size_command) + 1:]:
                            hindi_text_to_fit = estimate_text_to_fit(
                                random_line, bbox_width_inches, bbox_height_inches, box_id,
                                json_file_path, x1, y1, font_size, bboxes,dpi
                            )
                            if hindi_text_to_fit:
                                font_size_command = font_size 
                                break

                    # If the line fits, create the TikZ node
                    if hindi_text_to_fit:
                        font_size_pts = font_size_mapping.get(font_size_command, 10)  # Default to 10pt if undefined
                        baseline_skip = font_size_pts * 1.1
                    else:
                        print("The randomly selected dateline line does not fit the bounding box. Check dimensions or text length.")
                else:
                    print("No valid dateline content found in the file.")



            elif label.lower() in ["ordered-list", "unordered-list", "catalogue", "options", "sub-ordered-list", "subsub-ordered-list", "sub-unordered-list", "subsub-unordered-list"]:
                label_config = label_mapping.get(label.lower(), {"font_size": "\\Huge", "style": ""})

                if isinstance(label_config, str):
                    label_config = {"font_size": "\\Huge", "style": ""}

                font_size_keys = list(font_size_mapping.keys())  
                index = font_size_keys.index(label_config.get("font_size", "\\Large"))-1
                font_size_command = font_size_keys[index] if index < len(font_size_keys) else font_size_keys[-1] 
                style_command = label_config.get("style", "")
                # style_command = label_config.get("style", "")

                # Estimate text and split into lines
                estimated_text = estimate_text_to_fit(
                    ' '.join(hindi_texts),
                    bbox_width_inches, bbox_height_inches,
                    box_id, json_file_path, x1, y1,
                    font_size_command, bboxes,dpi
                )
                estimated_lines = estimated_text.split('\\linebreak')

                # Initialize prefix_format based on label type
                if label.lower() in ["ordered-list", "sub-ordered-list", "subsub-ordered-list"]:
                    # Use numbers for ordered-lists and sub-ordered-lists
                    prefix_format = lambda idx: f"{label_counter['ordered-list']}. "
                    label_counter['ordered-list'] += 1  # Increment the counter
                elif label.lower() in ["unordered-list", "sub-unordered-list", "subsub-unordered-list"]:
                    # Use bullet points for unordered-lists and sub-unordered-lists
                    prefix_format = lambda idx: "• "
                elif label.lower() == "options":
                    # Use letters for options
                    current_counter = label_counter['options']
                    prefix_format = lambda idx: f"{current_counter}. "

                    # Update the counter (cycle back to 'A' after 'D')
                    if current_counter == label_limit:
                        label_counter['options'] = 'A'
                    else:
                        label_counter['options'] = chr(ord(current_counter) + 1)
                else:
                    # Default case: No prefix
                    prefix_format = lambda idx: ""

                # Generate formatted lines with prefix
                enumerated_lines = [f"{prefix_format(idx)}{line.strip()}" for idx, line in enumerate(estimated_lines) if line.strip()]
                formatted_text = '\\linebreak'.join(enumerated_lines)
                # doc.append(NoEscape(
                #     f'\\node[paragraphtext, anchor=north west, text width={width_with_padding}pt] at ({xmin},{ymax+3.5}) {{{font_size_command}{{{formatted_text}}}}};'
                # ))


            elif (label.lower() not in ["index", "formula", "figure_1", "formula_1","header", "headline", "sub-headline", "options", "figure", "credit", "dateline", "table_row1_col1", "table_row1_col2", "table_row1_col3"] 
                and not re.match(r'table_row[1-9][0-9]*_col[1-9][0-9]*', label.lower()) 
                or re.match(r'.*(?<!_1)_1$', label.lower())):
                if label.lower().startswith("paragraph") or label.lower() == "answer"or label.lower() == "table caption" or label.lower() == "caption"or label.lower() == "author":
                    alignment = 'justify'
                else:
                    alignment = 'left'

                label_config = label_mapping.get(label.lower(), {"font_size": "\\Large", "style": ""})
                if isinstance(label_config, str):
                    label_config = {"font_size": "\\Large", "style": ""}
                
                font_size_keys = list(font_size_mapping.keys())  
                index = font_size_keys.index(label_config.get("font_size", "\\Large")) -1
                font_size_command = font_size_keys[index] if index < len(font_size_keys) else font_size_keys[-1] 
                style_command = label_config.get("style", "")
                # if(label.lower()=='paragraph'):
                #     print(label_config)
                style_command = label_config.get("style", "")
                # print(label)
                # print(font_size_command)
                hindi_text_to_fit = estimate_text_to_fit(' '.join(hindi_texts), bbox_width_inches, bbox_height_inches, box_id, json_file_path, x1, y1, font_size_command,bboxes,dpi)

                if not hindi_text_to_fit:
                    # Attempt to fit text using smaller font sizes
                    for font_size in font_sizes[font_sizes.index(font_size_command) + 1:]:
                        hindi_text_to_fit = estimate_text_to_fit(
                            ' '.join(hindi_texts), bbox_width_inches, bbox_height_inches,
                            box_id, json_file_path, x1, y1, font_size, bboxes,dpi
                        )
                        if hindi_text_to_fit:
                            font_size_command = font_size
                            break

                # Determine the font size in points and calculate baseline skip
                font_size_pts = font_size_mapping.get(font_size_command, 10)
                baseline_skip = font_size_pts * 1.1

            elif label in ["headline", "sub-headline","credit"] and height < width:
                # print("header was there")
                label_config = label_mapping.get(label.lower(), {"font_size": "", "style": ""})
                if isinstance(label_config, str):
                    label_config = {"font_size": "", "style": ""}
                font_size_keys = list(font_size_mapping.keys())  
                index = font_size_keys.index(label_config.get("font_size", "\\Large")) -1
                font_size_command = font_size_keys[index] if index < len(font_size_keys) else font_size_keys[-1] 
                style_command = label_config.get("style", "")
                # style_command = label_config.get("style", "")
                hindi_text_to_fit = estimate_text_to_fit(' '.join(hindi_texts), bbox_width_inches, bbox_height_inches,box_id,json_file_path, x1, y1, font_size_command,bboxes,dpi)
                # print(hindi_text_to_fit)

                if not hindi_text_to_fit:
                    # print("no hindi_text")
                    for font_size in font_sizes[font_sizes.index(font_size_command) + 1:]:
                        hindi_text_to_fit = estimate_text_to_fit(' '.join(hindi_texts), bbox_width_inches, bbox_height_inches,box_id,json_file_path, x1, y1, font_size,bboxes,dpi)
                        # print(font_size)
                        if hindi_text_to_fit:
                            # print("got hindi text")
                            # print(hindi_text_to_fit)
                            font_size_command = font_size
                            break
                # Determine the font size in points and calculate baseline skip
                font_size_pts = font_size_mapping.get(font_size_command, 10)
                baseline_skip = font_size_pts * 1.1
                color_str = 'text=black' 
    doc.append(NoEscape(r'\end{tikzpicture}'))
    doc.append(NoEscape(r'\end{center}'))
    return doc.dumps()

def read_bboxes_from_file(file_path):
    bboxes = []
    
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if not line:
                continue

            try:
                # Updated regex pattern to handle the format correctly, with annotation_id and image_id as strings
                match = re.match(r'^\[([^\[\],]+?),\s*\[\s*(\d+(\.\d+)?)\s*,\s*(\d+(\.\d+)?)\s*,\s*(\d+(\.\d+)?)\s*,\s*(\d+(\.\d+)?)\s*\],\s*([^\[\],]+?),\s*([^\[\],]+?)\]$', line.strip())

                if not match:
                    # print(f"Skipping malformed line (regex match failed): {line}")
                    continue

                # Extract label
                label = match.group(1).strip().strip('"')
                
                # Extract bounding box values (x1, y1, width, height)
                bbox_values = [float(match.group(i)) for i in range(2, 10, 2)]  # Extract x1, y1, width, height as floats

                # Extract annotation_id and image_id as strings (no conversion to int)
                annotation_id = match.group(9).strip()  # Capture annotation_id as a string
                image_id = match.group(10).strip()      # Capture image_id as a string

                # Append the extracted values as a tuple
                bboxes.append((label, bbox_values, annotation_id, image_id))

            except Exception as e:
                print(f"Error processing line '{line}': {e}")
    
    return bboxes



from collections import defaultdict

def find_closest_font_size(height, font_size_mapping):
    """
    Find the closest font size based on the given height, ensuring it is less than or equal to the height.
    """
    valid_sizes = {size: value for size, value in font_size_mapping.items() if value <= height}
    if not valid_sizes:
        return None  # No valid font size found for the height
    return max(valid_sizes, key=lambda size: font_size_mapping[size])

def set_font_size_per_category(bboxes, font_size_mapping):
    """
    Assign a font size for each category based on the minimum bounding box height within that category.

    Parameters:
        bboxes (list): List of bounding boxes in the format [(label, coords, bbox_id, ...)].
        font_size_mapping (dict): Mapping of font size names to their respective height values.

    Returns:
        dict: A dictionary mapping categories to their assigned font size.
    """
    # Group bounding boxes by their category (label)
    category_to_heights = defaultdict(list)
    for label, coords, bbox_id, _ in bboxes:  # Adjusted to match the given bbox format
        height = coords[3]  # Height is the 4th value in the coordinates
        category_to_heights[label].append(height)

    # Assign font size for each category based on the minimum height in that category
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
    """
    Process image and bounding boxes, extract dimensions, and apply the label mapping function.

    Parameters:
    - bbox_file_path (str): Path to the bounding box file.
    - image_path (str): Path to the image file.

    Returns:
    - tuple: A tuple containing the bounding boxes and the assigned label mapping for the image.
    """
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

hindi_text_file = r"output_texts/assamese.txt"
base_path = ''
json_file_path=r'Output/output_annotations.json'

# Start time for execution tracking
start_time = time.time()

# Get bounding box and image file paths
bbox_files_and_paths = get_bboxes_and_image_path(base_path)
for bbox_file_path, image_path in bbox_files_and_paths:
    bboxes, label_mapping = process_image_and_bboxes(bbox_file_path, image_path)
    extract_dimensions_and_text_from_file(image_path, bbox_file_path, hindi_text_file, label_mapping)

end_time = time.time()
execution_time = end_time - start_time
print(f"Execution Time: {execution_time} seconds")
