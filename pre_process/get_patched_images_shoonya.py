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
asterisk_added = {}
start_time = time.time()

class Center(Environment):
    packages = [Package('amsmath')]
    _latex_name = 'center'

# Global variable to store JSON annotations
output_json = {
    "annotations": []
}

# font_size_mapping = {
#     '\\tiny': 5, '\\scriptsize': 7, '\\footnotesize': 8, '\\small': 9, '\\normalsize': 10,
#     '\\large': 12, '\\Large': 15, '\\LARGE': 17, '\\huge': 20, '\\Huge': 25, '\\verylarge': 37,
#     '\\veryLarge': 43, '\\veryhuge': 49, '\\veryHuge': 62, '\\alphaa': 60, '\\betaa': 57,
#     '\\gammaa': 55, '\\deltaa': 53, '\\epsilona': 51, '\\zetaa': 47, '\\etaa': 45,
#     '\\iotaa': 41, '\\kappaa': 39, '\\lambdaa': 35, '\\mua': 33, '\\nua': 31,
#     '\\xia': 29, '\\pia': 27, '\\rhoa': 24, '\\sigmaa': 22, '\\taua': 18,
#     '\\upsilona': 16, '\\phia': 15, '\\chia': 13, '\\psia': 11, '\\omegaa': 6,
#     '\\oomegaa': 4, '\\ooomegaa': 3, '\\oooomegaaa': 2
# }

# def estimate_text_to_fit(hindi_text, bbox_width_inches, bbox_height_inches, box_id, output_json_path, x1, y1, font_size, bboxes):
#     print(bboxes)
#     output_folder_path = 'output_jsons'  # Change this to your desired output folder path
#     os.makedirs(output_folder_path, exist_ok=True)  # Create the folder if it doesn't exist

#     font_path = r"fonts/deva_headers/GajrajOne-Regular.ttf"

#     # Initialize font size mapping and sizes
#     point_size = font_size_mapping.get(font_size, 12)
#     font = ImageFont.truetype(font_path, point_size)

#     # Image setup
#     img = Image.new('RGB', (int(bbox_width_inches * 72), int(bbox_height_inches * 72)), (255, 255, 255))
#     draw = ImageDraw.Draw(img)

#     words = hindi_text.split()

#     # Ensure the rotated words list is not empty
#     while True:
#         random_start = random.randint(0, max(0, len(words) - 1))
#         rotated_words = words[random_start:] + words[:random_start]

#         if rotated_words:  # Check if the rotated list is not empty
#             words = rotated_words
#             break

#         if not rotated_words:  # If rotated_words is empty, read words from single.txt
#             print("Rotated words are empty. Reading words from 'single.txt'...")
#             try:
#                 with open("single.txt", "r", encoding="utf-8") as f:
#                     words = f.read().split()  # Read words from single.txt
#             except FileNotFoundError:
#                 print("Error: 'single.txt' not found. Exiting loop.")
#                 break

#             if not words:  # If no words are found in single.txt
#                 print("No words available in 'single.txt'. Exiting loop.")
#                 break

#             # Recheck the condition with new words from the file
#             random_start = random.randint(0, max(0, len(words) - 1))
#             rotated_words = words[random_start:] + words[:random_start]

#             if rotated_words:  # If the new list is non-empty, update and break
#                 words = rotated_words
#                 break

        
#     truncated_text_lines = []
#     truncated_text_with_linebreaks = []
#     current_line = ''
#     current_line_width = 0

#     line_height = point_size * 1.5
#     adjusted_line_height = point_size * 1.5

#     # Calculate the maximum number of lines that can fit in the bounding box
#     max_lines = int(bbox_height_inches * 72 / line_height)

#     # Add condition to check if max_lines is greater than 3
#     if max_lines > 3:
#         max_lines = int(bbox_height_inches * 72 / adjusted_line_height)

#     print(f"max_lines: {max_lines}, type: {type(max_lines)}")  # Debug print

#     for word in words:
#         word_bbox = draw.textbbox((0, 0), word, font=font)
#         word_width = word_bbox[2] - word_bbox[0]
#         space_bbox = draw.textbbox((0, 0), ' ', font=font)
#         space_width = space_bbox[2] - space_bbox[0]
#         new_line_width = current_line_width + space_width + word_width if current_line else word_width

#         if new_line_width <= bbox_width_inches * 72:
#             if current_line:
#                 current_line += ' ' + word
#                 current_line_width = new_line_width
#             else:
#                 current_line = word
#                 current_line_width = word_width
#         else:
#             truncated_text_lines.append(current_line)
#             truncated_text_with_linebreaks.append(current_line + r'\linebreak')
#             current_line = word
#             current_line_width = word_width

#             if len(truncated_text_lines) >= max_lines:
#                 break

#     if current_line and len(truncated_text_lines) < max_lines:
#         truncated_text_lines.append(current_line)
#         truncated_text_with_linebreaks.append(current_line + r'\linebreak')

#     # Find the corresponding bbox in `bboxes` list using `box_id`
#     current_box = next((bbox for bbox in bboxes if bbox[5] == box_id), None)

#     # Only create annotation if there is meaningful text inside the box
#     if current_box and max_lines > 0 and '\n'.join(truncated_text_with_linebreaks[:max_lines]):
#         image_id = current_box[6]  # Get the image ID from bbox[6]
#         label = current_box[4]     # Get the label from bbox[4]

#         # Prepare the annotation data
#         annotation = {
#             "id": box_id,
#             "image_id": image_id,
#             "label": label,
#             "bbox": {
#                 "x1": x1,
#                 "y1": y1,
#                 "width": bbox_width_inches * 72,  # Convert to pixels
#                 "height": bbox_height_inches * 72  # Convert to pixels
#             },
#             # "text": '\n'.join(truncated_text_lines),
#             "textlines": []
#         }

#         # Populate the textlines with their bounding box dimensions
#         for idx, line in enumerate(truncated_text_lines):
#             annotation['textlines'].append({
#                 "line_idx": idx,
#                 "bbox": [x1, y1 + idx * adjusted_line_height, bbox_width_inches * 72, adjusted_line_height],
#                 # "text": line
#             })

#         # Create or load the JSON file for the specific image_id
#         image_json_file = os.path.join(output_folder_path, f"{image_id}.json")

#         # Check if the JSON file already exists
#         if os.path.exists(image_json_file):
#             # Load existing annotations
#             with open(image_json_file, 'r', encoding='utf-8') as json_file:
#                 try:
#                     existing_data = json.load(json_file)
#                 except json.JSONDecodeError:
#                     existing_data = {"annotations": []}
#         else:
#             existing_data = {"annotations": []}

#         # Add the current annotation to the existing data
#         existing_data["annotations"].append(annotation)

#         # Write the accumulated annotations to the specific output file
#         try:
#             with open(image_json_file, 'w', encoding='utf-8') as json_file:
#                 json.dump(existing_data, json_file, indent=4, ensure_ascii=False)
#             print(f"Successfully saved annotations to {image_json_file}.")
#         except Exception as e:
#             print(f"Error creating JSON file: {e}")

#     return '\n'.join(truncated_text_with_linebreaks[:max_lines])

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
        print("Skipping bounding box due to insufficient valid corners.")
        return None, None, None  # Return None when corners are out of bounds

    # Get pixel colors for valid corners
    corner_colors = [image.getpixel(corner) for corner in valid_corners]
    
    # Ensure we have enough colors to determine the gradient
    if len(corner_colors) < 2:
        print("Not enough valid corner colors to determine gradient.")
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
    try:
        # Generate color definitions for LaTeX
        color1_latex = f"{start_color[0] / 255:.2f},{start_color[1] / 255:.2f},{start_color[2] / 255:.2f}"
        color2_latex = f"{end_color[0] / 255:.2f},{end_color[1] / 255:.2f},{end_color[2] / 255:.2f}"

        color1_name = f"color1_{x1}_{y1}"
        color2_name = f"color2_{x1}_{y1}"

        color_definitions = f"""
\\definecolor{{{color1_name}}}{{rgb}}{{{color1_latex}}}
\\definecolor{{{color2_name}}}{{rgb}}{{{color2_latex}}}
"""

        # Generate the fill command based on gradient type
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
        else:
            raise ValueError(f"Unknown gradient type: {gradient_type}")

        return color_definitions + fill_command

    except Exception as e:
        print(f"Error generating LaTeX for gradient at ({x1}, {y1}): {e}")
        return ""



# def get_most_used_colors(image, bbox, n_colors=2):
#     from collections import Counter
#     import numpy as np

#     x1, y1, width, height = bbox[:4]
#     patch = image.crop((x1, y1, x1 + width, y1 + height))
#     patch_data = np.array(patch).reshape(-1, 3)
#     color_counts = Counter(map(tuple, patch_data))
#     most_common_colors = color_counts.most_common(n_colors)
#     dominant_colors = [color for color, count in most_common_colors]
    
#     # Fallback if not enough colors are available
#     while len(dominant_colors) < n_colors:
#         dominant_colors.append((0, 0, 0))  # Append black as the fallback color
    
#     return dominant_colors

# def choose_text_color(bg_color, dominant_colors):
#     import numpy as np

#     tolerance = 10
#     percentage_tolerance = 0.25
#     black_color = np.array([0, 0, 0])
#     bg_color = np.array(bg_color)
#     dominant_colors = [np.array(color) for color in dominant_colors]

#     def is_similar_color(color1, color2, tolerance, percentage_tolerance):
#         abs_diff = np.abs(color1 - color2)
#         relative_diff = abs_diff / 255.0 
#         return np.all(relative_diff <= percentage_tolerance) or np.all(abs_diff <= tolerance)

#     # Ensure at least one valid color is chosen
#     if len(dominant_colors) > 1 and not is_similar_color(dominant_colors[1], bg_color, tolerance, percentage_tolerance):
#         chosen_color = dominant_colors[1]
#     elif len(dominant_colors) > 0 and not is_similar_color(dominant_colors[0], bg_color, tolerance, percentage_tolerance):
#         chosen_color = dominant_colors[0]
#     else:
#         chosen_color = black_color

#     if is_similar_color(chosen_color, bg_color, tolerance, percentage_tolerance):
#         return black_color

#     return chosen_color


def rgb_to_normalized(rgb):
    return [val / 255.0 for val in rgb]


def extract_dimensions_and_text_from_file(image_path, file_path):
    # Read the entire file and split the lines
    with open(file_path, 'r') as file:
        lines = file.readlines()
    
    # The first line contains the image dimensions
    image_dimensions_line = lines[0].strip()
    
    # Ensure we only attempt to parse image dimensions
    image_dimensions = eval(image_dimensions_line)  # [950, 650]
    if not isinstance(image_dimensions, list) or len(image_dimensions) != 2:
        raise ValueError(f"Invalid image dimensions: {image_dimensions}")
    
    # Process remaining lines as bounding boxes
    box_details = lines[1:]  # Skip the first line (image dimensions)
    
    bboxes = []
    
    for line in box_details:
        if line.strip():
            # Updated regex pattern to match label, bbox dimensions, annotation ID, and optional image ID
            match = re.match(r'^\[([^\[\],]+?),\s*\[\s*(\d+(\.\d+)?)\s*,\s*(\d+(\.\d+)?)\s*,\s*(\d+(\.\d+)?)\s*,\s*(\d+(\.\d+)?)\s*\],\s*([^\[\],]+?),\s*(\S+)\]$', line.strip())

            if not match:
                print(f"Skipping malformed line (regex match failed): {line.strip()}")
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
    # with open(hindi_text_file, 'r', encoding='utf-8') as file:
    #     hindi_texts = file.read().splitlines()

    # Generate LaTeX code (apply uniform font size for 'paragraph' and 'answer' labels)
    latex_code = generate_latex(image_path, image_dimensions, bboxes)

    # Prepare output folder and file paths
    base_path = 'Patched_tex_files'
    subfolder_name = os.path.splitext(os.path.basename(file_path))[0]
    output_folder = os.path.join(base_path, subfolder_name)
    os.makedirs(output_folder, exist_ok=True)

    # Save LaTeX file with the image file name
    image_file_name = os.path.splitext(os.path.basename(image_path))[0]
    latex_output_file = os.path.join(output_folder, f"{image_file_name}.tex")
    with open(latex_output_file, "w", encoding='utf-8') as output_file:
        output_file.write(latex_code)


def get_bboxes_and_image_path(base_path):
    bbox_dir = os.path.join(base_path, 'BBOX_val')
    image_dir = os.path.join(base_path, 'images_val')

    # Debug print to check if bbox_dir exists
    print(f"Looking for bounding box files in: {bbox_dir}")
    if not os.path.exists(bbox_dir):
        raise FileNotFoundError(f"Directory not found: {bbox_dir}")

    bbox_files_and_paths = []
    for subdir, _, files in os.walk(bbox_dir):
        print(f"Subdirectory: {subdir}")
        print(f"Files: {files}")

        bbox_files = [f for f in files if f.endswith('.txt')]
        print(f"Bounding box files: {bbox_files}")
        
        for bbox_file in bbox_files:
            bbox_file_path = os.path.join(subdir, bbox_file)

            # Remove the '.txt' extension to get the base bbox file name
            file_name_with_id = os.path.basename(bbox_file).replace('.txt', '')
            file_name = "_".join(file_name_with_id.split('_')[:-1])
            image_name = file_name + '.png'
            image_path = os.path.join(image_dir, image_name)

            # Debug prints
            print(f"Checking for bounding box file: {bbox_file_path}")
            print(f"Expected corresponding image file: {image_path}")

            # Check if the corresponding image exists
            if os.path.exists(image_path) and not os.path.basename(image_path).startswith('._'):
                # Add the bounding box and image paths to the list
                bbox_files_and_paths.append((bbox_file_path, image_path))

    if not bbox_files_and_paths:
        raise FileNotFoundError("No matching bounding box or image file found.")

    return bbox_files_and_paths


def split_into_sentences(text):
    sentence_endings = re.compile(r'(?<=[.!?।])\s+')
    sentences = sentence_endings.split(text.strip())
    return sentences

# Define the directories for header and paragraph fonts
header_fonts_dir = "fonts/santhali_headers"
paragraph_fonts_dir = "fonts/santhali_paragraphs"

# Function to randomly select a font file from a directory
def get_random_font(fonts_dir):
    fonts = [f for f in os.listdir(fonts_dir) if f.endswith('.ttf')]
    if not fonts:
        raise FileNotFoundError(f"No .ttf files found in directory: {fonts_dir}")
    return random.choice(fonts)



def generate_latex(image_path, image_dimensions, bboxes):
    # Select random fonts
    header_font = get_random_font(header_fonts_dir)
    paragraph_font = get_random_font(paragraph_fonts_dir)

    doc = Document(documentclass='article')
    doc.packages.append(Package('tikz'))
    doc.packages.append(Package('fontspec'))
    doc.packages.append(NoEscape(f'\\newfontfamily\\hindifont[Script=Devanagari]{{{header_font}}}'))
    doc.packages.append(NoEscape(f'\\newfontfamily\\paragraphfont[Script=Devanagari]{{{paragraph_font}}}'))
    doc.packages.append(Package('geometry', options=f'paperwidth={image_dimensions[1]}pt,paperheight={image_dimensions[0]}pt,margin=0pt'))
    doc.append(NoEscape(r'''

    \makeatletter
    \newcommand{\verylarge}{\@setfontsize\verylarge{37}{42}}
    \newcommand{\veryLarge}{\@setfontsize\veryLarge{43}{49}}
    \newcommand{\veryhuge}{\@setfontsize\veryhuge{49}{55}}
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
    doc.append(NoEscape(r'\tikzset{hinditext/.style={font=\hindifont, text=black}}'))
    doc.append(NoEscape(r'\tikzset{paragraphtext/.style={font=\paragraphfont, text=black}}'))

    font_sizes = [
        '\\veryHuge', '\\alphaa', '\\betaa', '\\gammaa', '\\deltaa', '\\epsilona', '\\veryhuge', '\\zetaa', '\\etaa', '\\veryLarge', '\\iotaa', '\\kappaa', '\\verylarge',
        '\\lambdaa', '\\mua', '\\nua', '\\xia', '\\pia', '\\Huge', '\\rhoa', '\\sigmaa', '\\huge', '\\taua', '\\upsilona', '\\LARGE', '\\phia', '\\Large', '\\chia', '\\large', '\\psia', '\\normalsize', '\\small', 
        '\\footnotesize','\\ooomegaa', '\\scriptsize', '\\omegaa','\\tiny','\\oomegaa','\\oooomegaa', 
    ]

    image = Image.open(image_path).convert('RGB')
    padding_points = 5

    for bbox in bboxes:
        x1, y1, width, height, label, box_id,image_id = bbox
        ymin = image_height - (y1 + height)
        ymax = image_height - y1 
        xmin = x1
        xmax = x1 + width

        if height > 26:
            width_with_padding = width - padding_points
            height_with_padding = height - padding_points
            ymin_with_padding = ymin + padding_points
            ymax_with_padding = ymax - padding_points
            xmin_with_padding = xmin + padding_points
            xmax_with_padding = xmax - padding_points

            if width_with_padding <= 0:
                width_with_padding = 0.01

            if height_with_padding <= 0:
                height_with_padding = 0.01
        else:
            width_with_padding = width 
            height_with_padding = height
            ymin_with_padding = ymin
            ymax_with_padding = ymax
            xmin_with_padding = xmin
            xmax_with_padding = xmax
        if (
            label not in ["figure_1", "formula_1","table", "formula", "QR code", "page number", "figure", "page_number", 
                        "mugshot", "code", "correlation", "bracket", "examinee info", "sealing line", 
                        "weather forecast", "barcode", "bill", "advertisement", "underscore", "blank", 
                        "other question number", "second-level question number", "third-level question number", 
                        "first-level question number"]
            # or re.match(r'table_row[1-9][0-9]*_col[1-9][0-9]*', label.lower())
            # and not re.match(r'.*_2.*', label.lower())        
            ):

            bg_color = get_patch_color_with_gradient(image, bbox)
            gradient_type, start_color, end_color = bg_color
            latex_code = generate_latex_for_gradient(xmin, ymin, width, height, gradient_type, start_color, end_color)
            doc.append(NoEscape(latex_code))
        # doc.append(NoEscape(f'\\draw[red] ({xmin},{ymin}) rectangle ({xmax},{ymax});'))
        # label_x = xmin 
        # label_y = ymax 
        # processed_label = label.replace(' ', '').replace('_', '')
        # doc.append(NoEscape(f'\\node[anchor=north west, text=black] at ({label_x},{label_y}) {{{{{processed_label}}}}};'))

#         label_config = label_mapping.get(label.lower(), {"font_size": "\\Huge", "style": ""})
#         if isinstance(label_config, str):
#             label_config = {"font_size": "\\Huge", "style": ""}
            
#         font_size_command = label_config.get("font_size", "\\Huge")
#         style_command = label_config.get("style", "")

#         tikz_text_style = "paragraphtext" if label.lower().startswith("paragraph") or label.lower() == "answer" or label.lower() == "footnote"  or label.lower() == "Poem"  else "hinditext"
#         bbox_width_inches = width_with_padding / 72.0
#         bbox_height_inches = height_with_padding / 72.0


#         if label not in ["figure_1", "QR code", "table", "page number", "figure", "page_number", "mugshot", "code", "correlation", "bracket", "examinee info", "sealing line", "weather forecast", "barcode", "bill", "advertisement", "underscore", "blank", "other question number", "second-level question number", "third-level question number", "first-level question number"]:
#             if label.lower() == "dateline":
#                 def read_datelines(filename="datelines.txt"):
#                     """Read the dateline.txt file and return a list of date lines."""
#                     try:
#                         with open(filename, 'r') as file:
#                             datelines = [line.strip() for line in file.readlines()]
#                             if not datelines:
#                                 print("No data lines found in the file.")
#                             else:
#                                 print(f"Datelines read from file: {datelines}")
#                         return datelines
#                     except FileNotFoundError:
#                         print(f"File {filename} not found.")
#                         return []
#                     except Exception as e:
#                         print(f"An error occurred while reading the file: {e}")
#                         return []

#                 # Fetch datelines and choose one randomly
#                 datelines_list = read_datelines()
#                 if datelines_list:
#                     selected_dateline = random.choice(datelines_list)

#                     # Font size mapping for dateline
#                     font_size_command = font_size_mapping.get('dateline', '\\Huge')
#                     style_command = ""  # If there's a specific style, you can add it here.

#                     # Dynamic font size adjustment logic
#                     hindi_text_to_fit = estimate_text_to_fit(selected_dateline, bbox_height_inches, bbox_width_inches, box_id, json_file_path, x1, y1, font_size_command, bboxes)
                    
#                     # If the selected dateline does not fit, reduce the font size dynamically
#                     if not hindi_text_to_fit:
#                         for font_size in font_sizes[font_sizes.index(font_size_command) + 1:]:
#                             hindi_text_to_fit = estimate_text_to_fit(selected_dateline, bbox_height_inches, bbox_width_inches, box_id, json_file_path, x1, y1, font_size, bboxes)
#                             if hindi_text_to_fit:
#                                 font_size_command = font_size  # Update the font size
#                                 break

#                     # Final baseline skip and node placement
#                     font_size_pts = font_size_mapping.get(font_size_command, 10)  # Default to 10pt if undefined
#                     baseline_skip = font_size_pts * 1.1
#                     doc.append(NoEscape(
#                         f'\\node[paragraphtext, anchor=north west, text width={bbox_width_inches * 72}pt] at ({xmin},{ymax+3.5}) {{{font_size_command}{{{hindi_text_to_fit}}}}};'
#                     ))
#                 else:
#                     print("No valid dateline found to place in the node.")

#             if label.lower() in ["headline","author","credit","index"] and height > width:

#                 ymax = ymax + padding_points
#                 if x1 > (image_width / 2):
#                     rotation = -90
#                     anchor = "south west"
#                     text_pos = f"({xmin},{ymax})"
#                 else:
#                     rotation = 90
#                     anchor = "north west"
#                     text_pos = f"({xmin},{ymin})"

#                 label_config = label_mapping.get(label.lower(), {"font_size": "\\Huge", "style": ""})
#                 if isinstance(label_config, str):
#                     label_config = {"font_size": "\\Huge", "style": ""}
#                 font_size_command = label_config.get("font_size", "\\Huge")
#                 # print(font_size_command)
#                 style_command = label_config.get("style", "")   
                        
#                 # hindi_text_to_fit = estimate_text_to_fit(' '.join(hindi_texts), bbox_height_inches, bbox_width_inches,box_id,json_file_path, x1, y1, font_size_command,bboxes)
#                 # if not hindi_text_to_fit:
#                 #     for font_size in font_sizes[font_sizes.index(font_size_command) + 1:]:
#                 #         hindi_text_to_fit = estimate_text_to_fit(' '.join(hindi_texts), bbox_height_inches, bbox_width_inches,box_id,json_file_path, x1, y1, font_size_command,bboxes)
#                 #         if hindi_text_to_fit:
#                 #             font_size_command = font_size
#                 #             # print(font_size_command)
#                 #             break

#                 # font_size_pts = font_size_mapping.get(font_size_command, 10)  # Default to 10pt if not found

#                 # # Calculate the baselineskip (1 times the font size)
#                 # baseline_skip = font_size_pts *1.1

#                 # Modify the LaTeX node to include the baselineskip
#                 # doc.append(NoEscape(
#                 #     f'\\node[hinditext, anchor={anchor}, text width={height}pt, rotate={rotation}] at {text_pos} '
#                 #     f'{{\\setlength{{\\baselineskip}}{{{baseline_skip}pt}} {font_size_command} {style_command}{{{hindi_text_to_fit}}}}};'
#                 # ))
#             elif label.lower() in ["ordered list", "unordered list", "catalogue", "option"]:
#                 label_config = label_mapping.get(label.lower(), {"font_size": "\\Huge", "style": ""})
                
#                 if isinstance(label_config, str):
#                     label_config = {"font_size": "\\Huge", "style": ""}

#                 font_size_command = label_config.get("font_size", "\\Huge")
#                 style_command = label_config.get("style", "")
#                 estimated_text = estimate_text_to_fit(' '.join(hindi_texts), bbox_width_inches, bbox_height_inches, box_id, json_file_path, x1, y1, font_size_command,bboxes)
#                 print("in the ordered list")
#                 print(estimated_text)
#                 print("in the ordered list")
#                 estimated_lines = estimated_text.split('\\linebreak')
#                 if label.lower() == "ordered list":
#                     prefix_format = lambda idx: f"{idx + 1}. "  # Numbered list (1., 2., 3., ...)
#                 elif label.lower() == "unordered list":
#                     prefix_format = lambda idx: "• "  # Bullet points (•)
#                 elif label.lower() == "option":
#                     prefix_format = lambda idx: chr(65 + idx) + ". "  # Alphabetic options (A., B., C., ...)
#                 else:
#                     prefix_format = lambda idx: "" 
#                 enumerated_lines = [f"{prefix_format(idx)}{line.strip()}" for idx, line in enumerate(estimated_lines) if line.strip()]
#                 formatted_text = '\\linebreak'.join(enumerated_lines)
#                 doc.append(NoEscape(
#                     f'\\node[paragraphtext, anchor=north west, text width={bbox_width_inches * 72}pt] at ({xmin},{ymax+3.5}) {{{font_size_command}{{{formatted_text}}}}};'
#                 ))

#             elif (label.lower() not in ["index", "figure_1", "author_1", "dateline_1", "header", "headline", "subhead", "option", "figure", "credit", "dateline", "table_row1_col1", "table_row1_col2", "table_row1_col3"] 
#                 and not re.match(r'table_row[1-9][0-9]*_col[1-9][0-9]*', label.lower()) 
#                 or re.match(r'.*(?<!_1)_1$', label.lower())):
#                 if label.lower().startswith("paragraph") or label.lower() == "answer":
#                     if width_with_padding <= 35:
#                         continue  
#                     alignment = 'justify'
#                 else:
#                     alignment = 'left'

#                 label_config = label_mapping.get(label.lower(), {"font_size": "\\Huge", "style": ""})
#                 if isinstance(label_config, str):
#                     label_config = {"font_size": "\\Huge", "style": ""}
                
#                 font_size_command = label_config.get("font_size", "\\Huge")
#                 style_command = label_config.get("style", "")
#                 hindi_text_to_fit = estimate_text_to_fit(' '.join(hindi_texts), bbox_width_inches, bbox_height_inches, box_id, json_file_path, x1, y1, font_size_command,bboxes)
#                 # print(hindi_text_to_fit)
#                 if not hindi_text_to_fit:
#                     print(label_config)
#                     print("no hindi text")
#                     for font_size in font_sizes[font_sizes.index(font_size_command) + 1:]:
#                         print(font_size)
#                         hindi_text_to_fit = estimate_text_to_fit(' '.join(hindi_texts), bbox_width_inches, bbox_height_inches, box_id, json_file_path, x1, y1, font_size,bboxes)
#                         if hindi_text_to_fit:
#                             font_size_command = font_size
#                             print('got hindi text')
#                             # print(font_size_command)
#                             break
                
#                 font_size_pts = font_size_mapping.get(font_size_command, 10) 
#                 baseline_skip = font_size_pts *1.1

#                 if hindi_text_to_fit:
#                     # Prepare the LaTeX node with baseline skip for the entire paragraph
#                     doc.append(NoEscape(
#                         f'\\node[{tikz_text_style}, anchor=north west, text width={width_with_padding}pt, align={alignment}] '
#                         f'at ({xmin},{ymax +3.5})'
#                         f'{{\\setlength{{\\baselineskip}}{{{baseline_skip}pt}} % Set baseline skip for the whole paragraph '
#                         f'\\par\n'  # This ensures that the text is treated as a paragraph
#                         f'{font_size_command} {style_command}{{{hindi_text_to_fit}}}}};'
#                     ))


#         if label in ["header","headline", "subhead","credit"] and height < width:
#             # print("header was there")
#             label_config = label_mapping.get(label.lower(), {"font_size": "", "style": ""})
#             if isinstance(label_config, str):
#                 label_config = {"font_size": "", "style": ""}
#             font_size_command = label_config.get("font_size", "\\Huge")
#             style_command = label_config.get("style", "")
#             hindi_text_to_fit = estimate_text_to_fit(' '.join(hindi_texts), bbox_width_inches, bbox_height_inches,box_id,json_file_path, x1, y1, font_size_command,bboxes)
#             # print(hindi_text_to_fit)

#             if not hindi_text_to_fit:
#                 print("no hindi_text")
#                 for font_size in font_sizes[font_sizes.index(font_size_command) + 1:]:
#                     hindi_text_to_fit = estimate_text_to_fit(' '.join(hindi_texts), bbox_width_inches, bbox_height_inches,box_id,json_file_path, x1, y1, font_size,bboxes)
#                     print(font_size)
#                     if hindi_text_to_fit:
#                         print("got hindi text")
#                         # print(hindi_text_to_fit)
#                         font_size_command = font_size
#                         break

#             if hindi_text_to_fit:
#                 # dominant_colors = get_most_used_colors(image, bbox)
#                 # text_color = choose_text_color(start_color, dominant_colors)
#                 # text_color_normalized = rgb_to_normalized(text_color)
#                 # normalized_color_str = ','.join(map(str, text_color_normalized))
#                 # r, g, b = normalized_color_str.split(',')
#                 color_str = 'text=black'  
#                 font_size_pts = font_size_mapping.get(font_size_command, 10)
#                 baseline_skip = font_size_pts *1.1
#                 doc.append(NoEscape(
#                     f'\\node[{tikz_text_style}, anchor=north west, text width={width_with_padding}pt,{color_str}]'
#                     f'at ({xmin},{ymax + 3.5}) '
#                     f'{{\\setlength{{\\baselineskip}}{{{baseline_skip}pt}} {font_size_command} {style_command} {hindi_text_to_fit}}};'
#                 ))
                
    doc.append(NoEscape(r'\end{tikzpicture}'))
    doc.append(NoEscape(r'\end{center}'))
    return doc.dumps()


# import re

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
                    print(f"Skipping malformed line (regex match failed): {line}")
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



# label_mapping = {
#     "_background_": {"font_size": "\\large", "style": ""},
#     "QR code": {"font_size": "\\footnotesize", "style": ""},
#     "advertisement": {"font_size": "\\VeryHuge", "style": ""},
#     "algorithm": {"font_size": "\\huge", "style": ""},
#     "answer": {"font_size": "\\huge", "style": ""},
#     "author": {"font_size": "\\large", "style": ""},
#     "barcode": {"font_size": "\\large", "style": ""},
#     "bill": {"font_size": "\\large", "style": ""},
#     "blank": {"font_size": "\\large", "style": ""},
#     "bracket": {"font_size": "\\footnotesize", "style": ""},
#     "breakout": {"font_size": "\\VeryHuge", "style": ""},
#     "byline": {"font_size": "\\huge", "style": ""},
#     "caption": {"font_size": "\\huge", "style": ""},
#     "catalogue": {"font_size": "\\VeryHuge", "style": ""},
#     "chapter title": {"font_size": "\\VeryHuge", "style": ""},
#     "code": {"font_size": "\\large", "style": ""},
#     "correction": {"font_size": "\\VeryHuge", "style": ""},
#     "credit": {"font_size": "\\LARGE", "style": ""},
#     "dateline": {"font_size": "\\Large", "style": ""},
#     "drop cap": {"font_size": "\\veryHuge", "style": ""},
#     "editor's note": {"font_size": "\\Large", "style": ""},
#     "endnote": {"font_size": "\\large", "style": ""},
#     "examinee information": {"font_size": "\\huge", "style": ""},
#     "fifth-level title": {"font_size": "\\VeryHuge", "style": ""},
#     "figure": {"font_size": "\\large", "style": ""},
#     "first-level question number": {"font_size": "\\Large", "style": ""},
#     "first-level title": {"font_size": "\\LARGE", "style": ""},
#     "flag": {"font_size": "\\veryHuge", "style": ""},
#     "folio": {"font_size": "\\veryHuge", "style": ""},
#     "footer": {"font_size": "\\veryHuge", "style": ""},
#     "footnote": {"font_size": "\\Huge", "style": ""},
#     "formula": {"font_size": "\\LARGE", "style": ""},
#     "fourth-level section title": {"font_size": "\\huge", "style": ""},
#     "fourth-level title": {"font_size": "\\LARGE", "style": ""},
#     "header": {"font_size": "\\veryHuge", "style": ""},
#     "headline": {"font_size": "\\veryHuge", "style": ""},
#     "index": {"font_size": "\\veryHuge", "style": ""},
#     "inside": {"font_size": "\\veryHuge", "style": ""},
#     "institute": {"font_size": "\\normalsize", "style": ""},
#     "jump line": {"font_size": "\\scriptsize", "style": ""},
#     "kicker": {"font_size": "\\Large", "style": ""},
#     "lead": {"font_size": "\\LARGE", "style": ""},
#     "marginal note": {"font_size": "\\LARGE", "style": ""},
#     "matching": {"font_size": "\\LARGE", "style": ""},
#     "mugshot": {"font_size": "\\Large", "style": ""},
#     "option": {"font_size": "\\LARGE", "style": ""},
#     "ordered list": {"font_size": "\\huge", "style": ""},
#     "other question number": {"font_size": "\\Large", "style": ""},
#     "page number": {"font_size": "\\normalsize", "style": ""},
#     "paragraph": {"font_size": "\\huge", "style": ""},
#     "part": {"font_size": "\\Large", "style": ""},
#     "play": {"font_size": "\\large", "style": ""},
#     "poem": {"font_size": "\\LARGE", "style": ""},
#     "reference": {"font_size": "\\large", "style": ""},
#     "sealing line": {"font_size": "\\large", "style": ""},
#     "second-level question number": {"font_size": "\\veryHuge", "style": ""},
#     "second-level title": {"font_size": "\\veryHuge", "style": ""},
#     "section": {"font_size": "\\huge", "style": ""},
#     "section title": {"font_size": "\\veryHuge", "style": ""},
#     "sidebar": {"font_size": "\\large", "style": ""},
#     "sub section title": {"font_size": "\\veryHuge", "style": ""},
#     "subhead": {"font_size": "\\veryHuge", "style": ""},
#     "subsub section title": {"font_size": "\\veryHuge", "style": ""},
#     "supplementary note": {"font_size": "\\large", "style": ""},
#     "table": {"font_size": "\\large", "style": ""},
#     "table caption": {"font_size": "\\Large", "style": ""},
#     "table note": {"font_size": "\\Large", "style": ""},
#     "teasers": {"font_size": "\\Large", "style": ""},
#     "third-level question number": {"font_size": "\\huge", "style": ""},
#     "third-level title": {"font_size": "\\huge", "style": ""},
#     "title": {"font_size": "\\veryHuge", "style": ""},
#     "translator": {"font_size": "\\normalsize", "style": ""},
#     "underscore": {"font_size": "\\scriptsize", "style": ""},
#     "unorderedlist": {"font_size": "\\huge", "style": ""},
#     "weather forecast": {"font_size": "\\large", "style": ""}
# }


# hindi_text_file = r"/hind_text_file.txt"
base_path = ''
# json_file_path=r'/BBOX_val/output_annotations.json'

# Start time for execution tracking
start_time = time.time()

# Get bounding box and image file paths
bbox_files_and_paths = get_bboxes_and_image_path(base_path)
for bbox_file_path, image_path in bbox_files_and_paths:
    bboxes = read_bboxes_from_file(bbox_file_path)
    # uniform_font_size = set_uniform_font_size_for_labels(bboxes, font_size_mapping)
    
    # if uniform_font_size:
    #     label_mapping["paragraph"]["font_size"] = uniform_font_size
    extract_dimensions_and_text_from_file(image_path, bbox_file_path)

end_time = time.time()
execution_time = end_time - start_time
print(f"Execution Time: {execution_time} seconds")
