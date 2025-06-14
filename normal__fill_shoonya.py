import os
import re
import math
import time
import random
import argparse
import multiprocessing as mp
from functools import partial
from PIL import Image, ImageFont, ImageDraw
from label_mapping import label_mapping_1, label_mapping_2, label_mapping_3, label_mapping_4, label_mapping_5, label_mapping_default

# Font size mapping (keeping only what's needed for textline calculation)
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

def calculate_textlines_fast(hindi_text, bbox_width_inches, bbox_height_inches, box_id, x1, y1, font_size, dpi):
    """
    Fast textline calculation - returns textline bounding boxes without file I/O
    """
    font_path = r"fonts/bengali/Header/Atma-Bold.ttf"
    
    # Get font size
    point_size = font_size_mapping.get(font_size, 12)
    if point_size <= 0:
        point_size = 18
    
    try:
        font = ImageFont.truetype(font_path, int(point_size))
    except:
        # Fallback if font file not found
        font = ImageFont.load_default()
    
    # Create temporary image for text measurement
    img = Image.new('RGB', (int(bbox_width_inches * dpi), int(bbox_height_inches * dpi)), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    words = hindi_text.split()
    if not words:
        return []
    
    # Randomize word order
    if len(words) > 1:
        random_start = random.randint(0, len(words) - 1)
        words = words[random_start:] + words[:random_start]
    
    textlines = []
    current_line = ''
    current_line_width = 0
    line_height = point_size * 1.5
    max_lines = int(bbox_height_inches * dpi / line_height)
    
    if max_lines > 3:
        adjusted_line_height = point_size * 1.5
        max_lines = int(bbox_height_inches * dpi / adjusted_line_height)
    else:
        adjusted_line_height = line_height
    
    line_idx = 0
    
    for word in words:
        try:
            word_bbox = draw.textbbox((0, 0), word, font=font)
            word_width = word_bbox[2] - word_bbox[0]
            space_bbox = draw.textbbox((0, 0), ' ', font=font)
            space_width = space_bbox[2] - space_bbox[0]
        except:
            # Fallback if textbbox fails
            word_width = len(word) * point_size * 0.6
            space_width = point_size * 0.3
        
        new_line_width = current_line_width + space_width + word_width if current_line else word_width
        
        # Skip words that are too wide
        if word_width > bbox_width_inches * dpi:
            break
        
        if new_line_width <= bbox_width_inches * dpi:
            if current_line:
                current_line += ' ' + word
                current_line_width = new_line_width
            else:
                current_line = word
                current_line_width = word_width
        else:
            # Save current line
            if current_line and line_idx < max_lines:
                textlines.append([x1, y1 + line_idx * adjusted_line_height, bbox_width_inches * dpi, adjusted_line_height])
                line_idx += 1
            
            # Start new line
            current_line = word
            current_line_width = word_width
            
            if line_idx >= max_lines:
                break
    
    # Add the last line
    if current_line and line_idx < max_lines:
        textlines.append([x1, y1 + line_idx * adjusted_line_height, bbox_width_inches * dpi, adjusted_line_height])
    
    return textlines

def get_label_mapping_for_image(image_path):
    """Get appropriate label mapping based on image height"""
    with Image.open(image_path) as img:
        image_width, image_height = img.size
    
    if image_height > 3500:
        return label_mapping_1
    elif 2500 <= image_height <= 3000:
        return label_mapping_2
    elif 2000 <= image_height < 2500:
        return label_mapping_3
    elif 1500 <= image_height < 2000:
        return label_mapping_4
    elif 500 <= image_height < 1500:
        return label_mapping_5
    else:
        return label_mapping_default

def read_bbox_file_with_dimensions(file_path):
    """Read bbox file and extract image dimensions and bounding boxes"""
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    
    # First line contains image dimensions
    image_dimensions = eval(lines[0].strip())
    if not isinstance(image_dimensions, list) or len(image_dimensions) != 2:
        raise ValueError(f"Invalid image dimensions: {image_dimensions}")
    
    # Process remaining lines as bounding boxes
    bboxes = []
    for line in lines[1:]:
        if line.strip():
            match = re.match(r'^\[([^\[\],]+?),\s*\[\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*\],\s*([^\[\],]+?),\s*(\S+)\]$', line.strip())
            
            if not match:
                continue
            
            try:
                label = match.group(1).strip().strip('"')
                dimensions = [float(match.group(i)) for i in [2, 3, 4, 5]]
                annotation_id = match.group(6).strip()
                image_id = match.group(7).strip()
                
                if len(dimensions) == 4:
                    x1, y1, width, height = dimensions
                    bboxes.append([x1, y1, width, height, label, annotation_id, image_id])
            except Exception as e:
                print(f"Error processing line '{line.strip()}': {e}")
    
    return image_dimensions, bboxes

def calculate_dpi(image_path, image_dimensions):
    """Calculate DPI from image pixel dimensions and physical dimensions"""
    with Image.open(image_path) as img:
        pixel_width, pixel_height = img.size
    
    diagonal_pixels = math.sqrt(pixel_width**2 + pixel_height**2)
    diagonal_inches = math.sqrt(image_dimensions[0]**2 + image_dimensions[1]**2)
    
    return diagonal_pixels / diagonal_inches

def process_single_file_fast(file_data, hindi_text):
    """
    Process a single bbox file and update it with textline data
    Modified to work with multiprocessing
    """
    bbox_file_path, image_path = file_data
    
    print(f"Processing: {os.path.basename(bbox_file_path)} (PID: {os.getpid()})")
    
    try:
        # Read bbox file
        image_dimensions, bboxes = read_bbox_file_with_dimensions(bbox_file_path)
        
        # Calculate DPI
        dpi = calculate_dpi(image_path, image_dimensions)
        
        # Get label mapping
        label_mapping = get_label_mapping_for_image(image_path)
        
        # Collect all textline bboxes
        all_textline_bboxes = []
        
        # Labels to skip (same as original)
        skip_labels = [
            "header", "footer", "figure_1", "unknown", "formula", "formula_1", "QR code", 
            "table", "page-number", "figure", "page_number", "mugshot", "code", "correlation", 
            "bracket", "examinee info", "sealing line", "weather forecast", "barcode", "bill", 
            "advertisement", "underscore", "blank", "other question number", 
            "second-level-question number", "third-level question number", "first-level-question"
        ]
        
        for bbox in bboxes:
            x1, y1, width, height, label, box_id, image_id = bbox
            
            if label in skip_labels:
                continue
            
            # Get label configuration
            label_config = label_mapping.get(label.lower(), {"font_size": "\\Large", "style": ""})
            if isinstance(label_config, str):
                label_config = {"font_size": "\\Large", "style": ""}
            
            font_size_command = label_config.get("font_size", "\\Large")
            
            # Adjust font size (reduce by one level as in original)
            font_size_keys = list(font_size_mapping.keys())
            try:
                index = font_size_keys.index(font_size_command) + 1
                font_size_command = font_size_keys[index] if index < len(font_size_keys) else font_size_keys[-1]
            except ValueError:
                font_size_command = "\\Large"
            
            # Calculate textlines
            bbox_width_inches = width / dpi
            bbox_height_inches = height / dpi
            
            textlines = calculate_textlines_fast(
                hindi_text, bbox_width_inches, bbox_height_inches, 
                box_id, x1, y1, font_size_command, dpi
            )
            
            # Convert textlines to bbox format for txt file
            for textline in textlines:
                all_textline_bboxes.append([label, textline, box_id, image_id])
        
        # Update the bbox file with textlines
        update_bbox_file_with_textlines(bbox_file_path, all_textline_bboxes, image_dimensions)
        
        return f"Successfully processed {os.path.basename(bbox_file_path)}"
        
    except Exception as e:
        error_msg = f"Error processing {bbox_file_path}: {e}"
        print(error_msg)
        return error_msg

def update_bbox_file_with_textlines(bbox_file_path, textline_bboxes, image_dimensions):
    """Update bbox file with new textline bounding boxes"""
    # Prepare content
    content = f"{image_dimensions}\n"
    
    for bbox in textline_bboxes:
        label, textline_coords, box_id, image_id = bbox
        x, y, w, h = textline_coords
        content += f'[{label}, [{x}, {y}, {w}, {h}], {box_id}, {image_id}]\n'
    
    # Write back to file
    with open(bbox_file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Updated {bbox_file_path} with {len(textline_bboxes)} textlines")

def get_bbox_and_image_pairs(bbox_dir, image_dir):
    """Get all bbox and image file pairs from specified directories"""
    if not os.path.exists(bbox_dir):
        print(f"Error: BBOX directory not found: {bbox_dir}")
        return []
    
    if not os.path.exists(image_dir):
        print(f"Error: Images directory not found: {image_dir}")
        return []
    
    pairs = []
    bbox_files_processed = 0
    missing_images = 0
    
    # Walk through the bbox directory (including subdirectories)
    for root, _, files in os.walk(bbox_dir):
        for bbox_file in files:
            if bbox_file.endswith('.txt'):
                bbox_file_path = os.path.join(root, bbox_file)
                bbox_files_processed += 1
                
                # Extract corresponding image name
                # Handle cases like "filename_12345.txt" -> "filename.png"
                file_name_with_id = os.path.basename(bbox_file).replace('.txt', '')
                
                # Try different strategies to find the corresponding image
                possible_image_names = []
                
                # Strategy 1: Remove the last _[number] part
                if '_' in file_name_with_id:
                    file_name = "_".join(file_name_with_id.split('_')[:-1])
                    possible_image_names.append(file_name + '.png')
                    possible_image_names.append(file_name + '.jpg')
                    possible_image_names.append(file_name + '.jpeg')
                
                # Strategy 2: Use the exact filename (without extension)
                possible_image_names.append(file_name_with_id + '.png')
                possible_image_names.append(file_name_with_id + '.jpg')
                possible_image_names.append(file_name_with_id + '.jpeg')
                
                # Strategy 3: Case-insensitive search in image directory
                image_found = False
                for possible_name in possible_image_names:
                    image_path = os.path.join(image_dir, possible_name)
                    if os.path.exists(image_path):
                        pairs.append((bbox_file_path, image_path))
                        image_found = True
                        break
                
                # If not found with direct path, try case-insensitive search
                if not image_found:
                    try:
                        all_images = os.listdir(image_dir)
                        for possible_name in possible_image_names:
                            for img_file in all_images:
                                if img_file.lower() == possible_name.lower():
                                    image_path = os.path.join(image_dir, img_file)
                                    pairs.append((bbox_file_path, image_path))
                                    image_found = True
                                    break
                            if image_found:
                                break
                    except Exception as e:
                        print(f"Error reading image directory: {e}")
                
                if not image_found:
                    missing_images += 1
                    print(f"Warning: No corresponding image found for {bbox_file}")
    
    print(f"Summary:")
    print(f"  - Total bbox files found: {bbox_files_processed}")
    print(f"  - Valid bbox-image pairs: {len(pairs)}")
    print(f"  - Missing image files: {missing_images}")
    
    return pairs

def load_hindi_text(hindi_text_file):
    """Load Hindi text from file"""
    try:
        with open(hindi_text_file, 'r', encoding='utf-8') as f:
            hindi_texts = f.read().splitlines()
        return ' '.join(hindi_texts)
    except FileNotFoundError:
        print(f"Warning: Hindi text file not found: {hindi_text_file}")
        return "Sample text for testing"

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Process bbox files with textline generation using multiprocessing',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog="""
Examples:
  python script.py --bbox-dir ./BBOX --image-dir ./images_val
  python script.py --bbox-dir /path/to/bbox --image-dir /path/to/images --cpus 8
  python script.py --bbox-dir ./BBOX --image-dir ./images --hindi-text-file ./text.txt --cpus 4
        """
    )
    
    parser.add_argument(
        '--cpus', 
        type=int, 
        default=mp.cpu_count(),
        help='Number of CPU cores to use for processing'
    )
    
    parser.add_argument(
        '--bbox-dir',
        type=str,
        required=True,
        help='Directory containing BBOX text files (searches recursively)'
    ) 
    parser.add_argument(
        '--image-dir',
        type=str,
        required=True,
        help='Directory containing corresponding image files'
    )
    
    parser.add_argument(
        '--hindi-text-file',
        type=str,
        default=r"1M_seed/input_1/assamese.txt",
        help='Path to the Hindi/Assamese text file'
    )
    
    parser.add_argument(
        '--chunk-size',
        type=int,
        default=1,
        help='Number of files to process per worker at a time'
    )
    
    parser.add_argument(
        '--font-path',
        type=str,
        default=r"fonts/bengali/Header/Atma-Bold.ttf",
        help='Path to the font file to use for text rendering'
    )
    
    return parser.parse_args()

def validate_arguments(args):
    """Validate command line arguments"""
    errors = []
    
    # Check if directories exist
    if not os.path.exists(args.bbox_dir):
        errors.append(f"BBOX directory does not exist: {args.bbox_dir}")
    
    if not os.path.exists(args.image_dir):
        errors.append(f"Images directory does not exist: {args.image_dir}")
    
    # Check if directories are actually directories
    if os.path.exists(args.bbox_dir) and not os.path.isdir(args.bbox_dir):
        errors.append(f"BBOX path is not a directory: {args.bbox_dir}")
    
    if os.path.exists(args.image_dir) and not os.path.isdir(args.image_dir):
        errors.append(f"Images path is not a directory: {args.image_dir}")
    
    # Validate CPU count
    max_cpus = mp.cpu_count()
    if args.cpus > max_cpus:
        print(f"Warning: Requested {args.cpus} CPUs, but only {max_cpus} available. Using {max_cpus} CPUs.")
        args.cpus = max_cpus
    elif args.cpus < 1:
        print("Warning: CPU count must be at least 1. Using 1 CPU.")
        args.cpus = 1
    
    # Check font file
    if not os.path.exists(args.font_path):
        print(f"Warning: Font file not found: {args.font_path}. Will use default font.")
    
    # Check Hindi text file
    if not os.path.exists(args.hindi_text_file):
        print(f"Warning: Hindi text file not found: {args.hindi_text_file}. Will use sample text.")
    
    return errors

def main():
    """Main function to process all files with multiprocessing"""
    args = parse_arguments()
    
    # Validate arguments
    validation_errors = validate_arguments(args)
    if validation_errors:
        print("Error: Invalid arguments:")
        for error in validation_errors:
            print(f"  - {error}")
        return 1
    
    print(f"Configuration:")
    print(f"  - BBOX directory: {args.bbox_dir}")
    print(f"  - Images directory: {args.image_dir}")
    print(f"  - Hindi text file: {args.hindi_text_file}")
    print(f"  - Font path: {args.font_path}")
    print(f"  - CPU cores: {args.cpus}")
    print(f"  - Chunk size: {args.chunk_size}")
    
    start_time = time.time()
    
    # Load Hindi text once
    hindi_text = load_hindi_text(args.hindi_text_file)
    
    # Get all bbox and image pairs
    bbox_image_pairs = get_bbox_and_image_pairs(args.bbox_dir, args.image_dir)
    
    if not bbox_image_pairs:
        print("No valid bbox-image pairs found!")
        return 1
    
    print(f"\nStarting processing of {len(bbox_image_pairs)} file pairs...")
    
    # Process files using multiprocessing
    if args.cpus == 1:
        # Single-threaded processing
        print("Running in single-threaded mode")
        results = []
        for i, file_pair in enumerate(bbox_image_pairs, 1):
            print(f"Processing {i}/{len(bbox_image_pairs)}: {os.path.basename(file_pair[0])}")
            result = process_single_file_fast(file_pair, hindi_text)
            results.append(result)
    else:
        # Multi-threaded processing
        print(f"Running in multi-threaded mode with {args.cpus} processes")
        
        # Create a partial function with hindi_text already bound
        process_func = partial(process_single_file_fast, hindi_text=hindi_text)
        
        with mp.Pool(processes=args.cpus) as pool:
            # Use imap for better progress tracking
            results = list(pool.imap(
                process_func, 
                bbox_image_pairs, 
                chunksize=args.chunk_size
            ))
    
    # Print results summary
    successful = sum(1 for r in results if "Successfully processed" in r)
    failed = len(results) - successful
    
    print(f"\n{'='*60}")
    print(f"Processing complete!")
    print(f"Successfully processed: {successful} files")
    print(f"Failed: {failed} files")
    
    end_time = time.time()
    execution_time = end_time - start_time
    print(f"Total execution time: {execution_time:.2f} seconds")
    print(f"Average time per file: {execution_time/len(bbox_image_pairs):.2f} seconds")
    
    if failed > 0:
        print("\nFailed files:")
        for result in results:
            if "Error processing" in result:
                print(f"  - {result}")
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)