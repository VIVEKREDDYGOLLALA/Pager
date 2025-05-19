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
from collections import Counter, defaultdict
import os
import re
import json
import math
from PIL import Image
from label_mapping import label_mapping_1, label_mapping_2, label_mapping_3, label_mapping_4, label_mapping_5, label_mapping_default

# Define the base path as the directory containing this script
BASE_PATH = os.path.dirname(os.path.abspath(__file__))

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

# LANGUAGES = [
#     # 'assamese',
#     # 'bengali',
#     # 'bodo',
#     # 'dogri',
#     # 'gujarati',
#     # 'hindi',
#     # 'kannada',
#     'kashmiri',
#     # 'konkani',
#     # 'maithili',
#     # 'malayalam',
#     # 'manipuri',
#     # 'marathi',
#     # 'nepali',
#     # 'odia',
#     # 'punjabi',
#     # 'sanskrit',
#     # 'santali',
#     # 'sindhi',
#     # 'tamil',
#     # 'telugu',
#     'urdu',
# ]

# basic font mappings for each language
FONT_MAPPING = {
    'assamese': 'NotoSerif', 'bengali': 'NotoSerifBengali', 'bodo': 'NotoSerif', 'dogri': 'NotoSerif',
    'gujarati': 'NotoSerifGujarati', 'hindi': 'NotoSerifDevanagari', 'kannada': 'NotoSerifKannada',
    'kashmiri': 'NotoSerif', 'konkani': 'NotoSerif', 'maithili': 'NotoSerifDevanagari',
    'malayalam': 'NotoSerifMalayalam', 'manipuri': 'NotoSansMeeteiMayek', 'marathi': 'NotoSerifDevanagari',
    'nepali': 'NotoSerifDevanagari', 'odia': 'NotoSerifOriya', 'punjabi': 'NotoSerifGurmukhi',
    'sanskrit': 'NotoSerifDevanagari', 'santali': 'NotoSerif', 'sindhi': 'NotoSerif', 'tamil': 'NotoSerifTamil',
    'telugu': 'NotoSerifTelugu', 'urdu': 'Amiri'
}

#function to estimate how much text can fit in a given bounding box
import os
import json
import random
from PIL import Image, ImageDraw, ImageFont

def estimate_text_to_fit(text, bbox_width_inches, bbox_height_inches, box_id, language, x1, y1, font_size, bboxes, dpi, font_path):
    output_folder_path = os.path.join(BASE_PATH, 'output_jsons')
    os.makedirs(output_folder_path, exist_ok=True)

    json_file_path = os.path.join(output_folder_path, f"{language}.json")

    point_size = font_size_mapping.get(font_size, 12)
    try:
        font = ImageFont.truetype(font_path, int(point_size))
    except Exception as e:
        print(f"Error loading font {font_path} for {language}: {e}")
        return ''

    img = Image.new('RGB', (int(bbox_width_inches * dpi), int(bbox_height_inches * dpi)), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    words = text.split()

    random_start = random.randint(0, max(0, len(words) - 1))
    words = words[random_start:] + words[:random_start]

    truncated_text_lines = []
    truncated_text_with_linebreaks = []
    current_line = ''
    current_line_width = 0

    line_height = point_size * 1.5
    max_lines = 1  # One line per textline box

    for word in words:
        word_bbox = draw.textbbox((0, 0), word, font=font)
        word_width = word_bbox[2] - word_bbox[0]
        space_bbox = draw.textbbox((0, 0), ' ', font=font)
        space_width = space_bbox[2] - space_bbox[0]
        new_line_width = current_line_width + space_width + word_width if current_line else word_width

        if word_width > bbox_width_inches * dpi:
            truncated_text_lines.clear()
            truncated_text_with_linebreaks.clear()
            break

        if new_line_width <= bbox_width_inches * dpi:
            current_line = (current_line + ' ' + word) if current_line else word
            current_line_width = new_line_width
        else:
            break  # We only want one line

    if current_line:
        truncated_text_lines.append(current_line)
        truncated_text_with_linebreaks.append(current_line + r'\linebreak')
    else:
        # Fallback to single-character text
        single_text_path = os.path.join(BASE_PATH, f"Characters/{language}.txt")
        try:
            with open(single_text_path, "r", encoding="utf-8") as f:
                chars = f.read().split()
        except FileNotFoundError:
            print(f"Error: {single_text_path} not found for {language}. Using placeholder text.")
            chars = ["..."]

        for ch in chars:
            word_bbox = draw.textbbox((0, 0), ch, font=font)
            word_width = word_bbox[2] - word_bbox[0]
            if word_width <= bbox_width_inches * dpi:
                truncated_text_lines.append(ch)
                truncated_text_with_linebreaks.append(ch + r'\linebreak')
                break

    current_box = next((bbox for bbox in bboxes if bbox[5] == box_id), None)
    if current_box and truncated_text_lines:
        image_id = current_box[6]
        label = current_box[4]

        # Load existing data
        if os.path.exists(json_file_path):
            with open(json_file_path, 'r', encoding='utf-8') as json_file:
                try:
                    existing_data = json.load(json_file)
                except json.JSONDecodeError:
                    existing_data = {"annotations": []}
        else:
            existing_data = {"annotations": []}

        # Find or create annotation for this bounding box
        annotation = next((a for a in existing_data["annotations"] if a["id"] == box_id), None)
        if not annotation:
            annotation = {
                "id": box_id,
                "image_id": image_id,
                "label": label,
                "text": "",
                "textlines": []
            }
            existing_data["annotations"].append(annotation)

        # Determine correct line index based on number of textlines already present
        line_idx = len(annotation["textlines"]) + 1

        line_text = truncated_text_lines[0]
        annotation["text"] += f" {line_text}"
        annotation["textlines"].append({
            "line_idx": line_idx,
            "bbox": [x1, y1, bbox_width_inches * dpi, line_height],
            "text": line_text
        })

        try:
            with open(json_file_path, 'w', encoding='utf-8') as json_file:
                json.dump(existing_data, json_file, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error creating JSON file for {language}: {e}")

    return '\n'.join(truncated_text_with_linebreaks[:1])

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

def extract_dimensions_and_text_from_file(image_path, file_path, text_file, label_mapping, language):
    # Convert paths to absolute
    image_path = os.path.abspath(image_path)
    file_path = os.path.abspath(file_path)
    text_file = os.path.abspath(text_file)

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

    texts = []
    with open(text_file, 'r', encoding='utf-8') as file:
        texts = file.read().splitlines()

    latex_code = generate_latex(image_path, image_dimensions, bboxes, texts, label_mapping, dpi, language)

    main_output_folder = os.path.join(BASE_PATH, 'Output_Tex_Files')
    os.makedirs(main_output_folder, exist_ok=True)

    # Create language-specific subfolder
    output_folder = os.path.join(main_output_folder, f'Tex_files_{language}')
    os.makedirs(output_folder, exist_ok=True)

    image_file_name = os.path.splitext(os.path.basename(image_path))[0]
    latex_output_file = os.path.join(output_folder, f"{image_file_name}.tex")
    with open(latex_output_file, "w", encoding='utf-8') as output_file:
        output_file.write(latex_code)

def get_bboxes_and_image_path(base_path):
    bbox_dir = os.path.join(BASE_PATH, 'BBOX')
    image_dir = os.path.join(BASE_PATH, 'images_val')
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

def generate_latex(image_path, image_dimensions, bboxes, texts, label_mapping, dpi, language):
    # Convert image path to absolute
    image_path = os.path.abspath(image_path)
    # Define font directories with absolute paths
    header_fonts_dir = os.path.join(BASE_PATH, f"fonts/{language}/Header")
    paragraph_fonts_dir = os.path.join(BASE_PATH, f"fonts/{language}/Paragraph")

    # Get random fonts
    try:
        header_font_path = get_random_font(header_fonts_dir)
        paragraph_font_path = get_random_font(paragraph_fonts_dir)
        header_font = os.path.basename(header_font_path).replace('.ttf', '')
        paragraph_font = os.path.basename(paragraph_font_path).replace('.ttf', '')
    except FileNotFoundError as e:
        print(f"Font error for {language}: {e}")
        header_font = FONT_MAPPING.get(language, 'NotoSerif')
        paragraph_font = FONT_MAPPING.get(language, 'NotoSerif')
        header_font_path = os.path.join(BASE_PATH, f"fonts/{language}/Header/{header_font}-Bold.ttf")
        paragraph_font_path = os.path.join(BASE_PATH, f"fonts/{language}/Paragraph/{paragraph_font}-Regular.ttf")

    # Initialize LaTeX document
    doc = Document(documentclass='article', document_options=['11pt'])

    #  added all packages
    doc.packages.append(Package('fontenc', options='T1'))
    doc.packages.append(Package('inputenc', options='utf8'))
    doc.packages.append(Package('lmodern'))
    doc.packages.append(Package('textcomp'))
    doc.packages.append(Package('lastpage'))
    doc.packages.append(Package('tikz'))
    
    # Add fontspec and polyglossia before any language settings
    doc.packages.append(Package('fontspec'))
    doc.packages.append(Package('polyglossia'))
    
    # Set geometry
    doc.packages.append(Package('geometry', options=f'paperwidth={image_dimensions[1]}pt,paperheight={image_dimensions[0]}pt,margin=0pt'))

    # Special mapping for polyglossia language names
    # Some languages have different names in polyglossia than commonly used
    language_mapping_polyglossia = {
        'assamese': 'bengali',  # Assamese uses Bengali script
        'bodo': 'hindi',       # Bodo typically uses Devanagari script
        'dogri': 'hindi',      # Dogri typically uses Devanagari script
        'gujarati': 'gujarati',
        'hindi': 'hindi',
        'kannada': 'kannada',
        'kashmiri': 'urdu',    # Kashmiri commonly uses Arabic/Urdu script
        'konkani': 'hindi',    # Konkani typically uses Devanagari script
        'maithili': 'hindi',   # Maithili typically uses Devanagari script
        'malayalam': 'malayalam',
        'manipuri': 'bengali', # Manipuri traditionally uses Bengali script, though Meetei Mayek is now used
        'marathi': 'marathi',
        'nepali': 'nepali',
        'odia': 'oriya',      # Odia is called Oriya in many contexts including polyglossia
        'punjabi': 'punjabi',
        'sanskrit': 'sanskrit',
        'santali': 'hindi',   # Santali traditionally used various scripts including Devanagari
        'sindhi': 'sindhi',
        'tamil': 'tamil',
        'telugu': 'telugu',
        'urdu': 'urdu',
        'bengali': 'bengali'
    }
    
    # map language to script
    script_mapping = {
        'assamese': 'Bengali', 'bengali': 'Bengali', 'bodo': 'Devanagari', 'dogri': 'Devanagari',
        'gujarati': 'Gujarati', 'hindi': 'Devanagari', 'kannada': 'Kannada', 'kashmiri': 'Arabic',
        'konkani': 'Devanagari', 'maithili': 'Devanagari', 'malayalam': 'Malayalam', 'manipuri': 'Bengali',
        'marathi': 'Devanagari', 'nepali': 'Devanagari', 'odia': 'Oriya', 'punjabi': 'Gurmukhi',
        'sanskrit': 'Devanagari', 'santali': 'Devanagari', 'sindhi': 'Arabic', 'tamil': 'Tamil',
        'telugu': 'Telugu', 'urdu': 'Arabic'
    }
    
    # get the script for current language
    script = script_mapping.get(language, 'Devanagari')
    
    # get the polyglossia language name
    polyglossia_language = language_mapping_polyglossia.get(language, language)
    
    # Set the main and other language in the preamble
    doc.preamble.append(NoEscape(f'\\setmainlanguage{{{polyglossia_language}}}'))
    doc.preamble.append(NoEscape(f'\\setotherlanguage{{english}}'))
    
    # defined the script-specific font required by polyglossia
    # get the lowercase script name to match polyglossia's naming convention
    # remove spaces and ensure lowercase for consistency
    script_lowercase = script.lower().replace(' ', '')
    
    # fixed specific script names for polyglossia
    script_name_fixes = {
        'oriya': 'oriya',
        'arabic': 'arabic',
        'bengali': 'bengali',
        'devanagari': 'devanagari',
        'gujarati': 'gujarati',
        'gurmukhi': 'gurmukhi',
        'kannada': 'kannada',
        'malayalam': 'malayalam',
        'tamil': 'tamil',
        'telugu': 'telugu'
    }
    
    script_polyglossia = script_name_fixes.get(script_lowercase, script_lowercase)
    
    # Define the script font with the same font as paragraphfont
    doc.preamble.append(NoEscape(f'\\newfontfamily\\{script_polyglossia}font[Script={script},Path={os.path.dirname(paragraph_font_path)}/]{{{os.path.basename(paragraph_font_path).replace(".ttf", "")}}}'))
    
    # Now define your custom fonts
    doc.preamble.append(NoEscape(f'\\newfontfamily\\headerfont[Script={script},Path={os.path.dirname(header_font_path)}/]{{{os.path.basename(header_font_path).replace(".ttf", "")}}}'))
    doc.preamble.append(NoEscape(f'\\newfontfamily\\paragraphfont[Script={script},Path={os.path.dirname(paragraph_font_path)}/]{{{os.path.basename(paragraph_font_path).replace(".ttf", "")}}}'))

    # Define custom font sizes in the preamble
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

    # Document content starts here
    doc.append(NoEscape(r'\begin{center}'))
    doc.append(NoEscape(r'\begin{tikzpicture}[x=1pt, y=1pt]'))
    
    # Rest of the function remains the same...
    
    # Rest of your code remains the same...
    image_height, image_width = image_dimensions
    # Use absolute path for image
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
        padding_points = 0

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
            "headline", "header", "sub-headline", "section-title", "sub-section-title", "dateline",
            "caption", "table caption", "table note", "editor's note", "kicker", "jump line",
            "subsub-section-title", "chapter-title", "first-level title", "second-level title",
            "third-level title", "fourth-level title", "fifth-level title", "title", "byline",
            "kicker", "subsub-headline", "folio"
        ]

        tikz_text_style = "headertext" if label.lower() in [hl.lower() for hl in headline_labels] else "paragraphtext"
        bbox_width_inches = width_with_padding / dpi
        bbox_height_inches = height_with_padding / dpi

        if label not in ["header", "footer", "figure_1", "formula", "formula_1", "QR code", "table", "page-number", "figure", "page_number", "mugshot", "code", "correlation", "bracket", "examinee info", "sealing line", "weather forecast", "barcode", "bill", "advertisement", "underscore", "blank", "other question number", "second-level-question number", "third-level question number", "first-level-question"]:
            if label.lower() == "dateline":
                dateline_path = os.path.join(BASE_PATH, f"Datelines/{language}.txt")
                try:
                    with open(dateline_path, 'r', encoding='utf-8') as file:
                        dateline_lines = [line.strip() for line in file.readlines() if line.strip()]
                except FileNotFoundError:
                    print(f"Dateline file {dateline_path} not found for {language}.")
                    dateline_lines = []

                if dateline_lines:
                    random_line = random.choice(dateline_lines)
                    font_size_command = font_size_mapping.get('dateline', '\\LARGE')
                    style_command = ""

                    hindi_text_to_fit = estimate_text_to_fit(
                        random_line, bbox_width_inches, bbox_height_inches, box_id,
                        language, x1, y1, font_size_command, bboxes, dpi, paragraph_font_path
                    )

                    if not hindi_text_to_fit:
                        for font_size in font_sizes[font_sizes.index(font_size_command) + 1:]:
                            hindi_text_to_fit = estimate_text_to_fit(
                                random_line, bbox_width_inches, bbox_height_inches, box_id,
                                language, x1, y1, font_size, bboxes, dpi, paragraph_font_path
                            )
                            if hindi_text_to_fit:
                                font_size_command = font_size
                                break

                    if hindi_text_to_fit:
                        font_size_pts = font_size_mapping.get(font_size_command, 10)
                        baseline_skip = font_size_pts * 1.1
                        doc.append(NoEscape(
                            f'\\node[{tikz_text_style}, anchor=north west, text width={width-5}pt]'
                            f'at ({xmin}, {ymax + 0}) '
                            f'{{\\setlength{{\\baselineskip}}{{{baseline_skip}pt}} {font_size_command} {style_command} {hindi_text_to_fit}}};'
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
                index = font_size_keys.index(label_config.get("font_size", "\\Large"))
                font_size_command = font_size_keys[index] if index < len(font_size_keys) else font_size_keys[-1]
                style_command = label_config.get("style", "")

                estimated_text = estimate_text_to_fit(
                    ' '.join(texts), bbox_width_inches, bbox_height_inches, box_id,
                    language, x1, y1, font_size_command, bboxes, dpi, paragraph_font_path
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

                enumerated_lines = [f"{prefix_format(idx)}{line.strip()}" for idx, line in enumerate(estimated_lines) if line.strip()]
                formatted_text = '\\linebreak'.join(enumerated_lines)
                doc.append(NoEscape(
                    f'\\node[paragraphtext, anchor=north west, text width={width-5}pt] at ({xmin},{ymax+3.5}) {{{font_size_command}{{{formatted_text}}}}};'
                ))
            elif (label.lower() not in ["index", "formula", "figure_1", "formula_1", "header", "headline", "sub-headline", "options", "figure", "credit", "dateline", "table_row1_col1", "table_row1_col2", "table_row1_col3"]
                  and not re.match(r'table_row[1-9][0-9]*_col[1-9][0-9]*', label.lower())
                  or re.match(r'.*(?<!_1)_1$', label.lower())):
                if label.lower().startswith("paragraph") or label.lower() in ["answer", "table caption", "caption"]:
                    if width_with_padding <= 35:
                        continue
                    alignment = 'justify'
                else:
                    alignment = 'left'

                label_config = label_mapping.get(label.lower(), {"font_size": "\\Large", "style": ""})
                if isinstance(label_config, str):
                    label_config = {"font_size": "\\Large", "style": ""}

                font_size_keys = list(font_size_mapping.keys())
                index = font_size_keys.index(label_config.get("font_size", "\\Large"))
                font_size_command = font_size_keys[index] if index < len(font_size_keys) else font_size_keys[-1]
                style_command = label_config.get("style", "")

                hindi_text_to_fit = estimate_text_to_fit(
                    ' '.join(texts), bbox_width_inches, bbox_height_inches, box_id,
                    language, x1, y1, font_size_command, bboxes, dpi, paragraph_font_path
                )

                if not hindi_text_to_fit:
                    for font_size in font_sizes[font_sizes.index(font_size_command) + 1:]:
                        hindi_text_to_fit = estimate_text_to_fit(
                            ' '.join(texts), bbox_width_inches, bbox_height_inches, box_id,
                            language, x1, y1, font_size, bboxes, dpi, paragraph_font_path
                        )
                        if hindi_text_to_fit:
                            font_size_command = font_size
                            break

                font_size_pts = font_size_mapping.get(font_size_command, 10)
                baseline_skip = font_size_pts * 1.1

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
                index = font_size_keys.index(label_config.get("font_size", "\\Large"))
                font_size_command = font_size_keys[index] if index < len(font_size_keys) else font_size_keys[-1]
                style_command = label_config.get("style", "")

                hindi_text_to_fit = estimate_text_to_fit(
                    ' '.join(texts), bbox_width_inches, bbox_height_inches, box_id,
                    language, x1, y1, font_size_command, bboxes, dpi, header_font_path
                )

                if not hindi_text_to_fit:
                    for font_size in font_sizes[font_sizes.index(font_size_command) + 1:]:
                        hindi_text_to_fit = estimate_text_to_fit(
                            ' '.join(texts), bbox_width_inches, bbox_height_inches, box_id,
                            language, x1, y1, font_size, bboxes, dpi, header_font_path
                        )
                        if hindi_text_to_fit:
                            font_size_command = font_size
                            break

                if not hindi_text_to_fit:
                    font_size_command = "\\large"
                    hindi_text_to_fit = estimate_text_to_fit(
                        ' '.join(texts), bbox_width_inches, bbox_height_inches, box_id,
                        language, x1, y1, font_size_command, bboxes, dpi, header_font_path
                    )
                    if not hindi_text_to_fit:
                        hindi_text_to_fit = " "

                font_size_pts = font_size_mapping.get(font_size_command, 10)
                baseline_skip = font_size_pts * 1.1
                color_str = 'text=black'

                doc.append(NoEscape(
                    f'\\node[{tikz_text_style}, anchor=north west, text width={width-5}pt, align=left, {color_str}] '
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

# Remove this global variable:
# # List of 22 official languages of India
# LANGUAGES = [
#     # 'assamese',
#     # 'bengali',
#     # 'bodo',
#     # 'dogri',
#     # 'gujarati',
#     # 'hindi',
#     # 'kannada',
#     'kashmiri',
#     # 'konkani',
#     # 'maithili',
#     # 'malayalam',
#     # 'manipuri',
#     # 'marathi',
#     # 'nepali',
#     # 'odia',
#     # 'punjabi',
#     # 'sanskrit',
#     # 'santali',
#     # 'sindhi',
#     # 'tamil',
#     # 'telugu',
#     'urdu',
# ]

def parse_arguments():
    """Parse command line arguments for language selection."""
    parser = argparse.ArgumentParser(
        description='Generate LaTeX documents with support for multiple languages, including Arabic script languages.'
    )
    
    # Add arguments for languages with default values matching your previous hardcoded selection
    parser.add_argument(
        '--languages', 
        nargs='+', 
        default=['urdu', 'kashmiri'],
        help='List of languages to process. Default: urdu kashmiri'
    )
    
    # Add BASE_PATH as an optional argument
    parser.add_argument(
        '--base-path',
        type=str,
        help='Base path for input/output files. Defaults to BASE_PATH global variable.'
    )
    
    return parser.parse_args()

def main():
    # Parse command line arguments
    args = parse_arguments()
    
    # Use languages from command-line arguments instead of global LANGUAGES list
    languages = args.languages
    
    # Use provided base path or fall back to global BASE_PATH
    base_path = args.base_path if args.base_path else BASE_PATH
    
    print(f"Processing the following languages: {', '.join(languages)}")
    
    # Start timing execution
    start_time = time.time()

    # Get bounding box files and image paths
    bbox_files_and_paths = get_bboxes_and_image_path(base_path)
    
    # Use the languages from args instead of the global LANGUAGES list
    for language in languages:
        print(f"Processing language: {language}")
        text_file = os.path.join(base_path, f"output_texts/{language}.txt")
        if not os.path.exists(text_file):
            print(f"Text file {text_file} not found for {language}. Skipping.")
            continue

        for bbox_file_path, image_path in bbox_files_and_paths:
            bboxes, label_mapping = process_image_and_bboxes(bbox_file_path, image_path)
            font_size_by_label = set_font_size_per_category(bboxes, font_size_mapping)

            for label, font_size in font_size_by_label.items():
                if label in label_mapping:
                    label_mapping[label]["font_size"] = font_size

            extract_dimensions_and_text_from_file(image_path, bbox_file_path, text_file, label_mapping, language)

    # Calculate and print execution time
    end_time = time.time()
    execution_time = end_time - start_time
    print(f"Total Execution Time: {execution_time} seconds")

if __name__ == "__main__":
    main()
