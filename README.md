# Synthetic Document Processing Pipeline

A comprehensive pipeline for processing documents with text extraction, overlap management, text filling, and image generation.

## 📋 Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Project Structure](#project-structure)
- [Input Format Requirements](#input-format-requirements)
- [Installation](#installation)
- [Usage](#usage)
  - [Method 1: Using main.py (Recommended)](#method-1-using-mainpy-recommended)
  - [Method 2: Running Scripts Individually](#method-2-running-scripts-individually)
- [Script Details](#script-details)
- [Configuration](#configuration)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

## 🎯 Overview

This pipeline processes documents through several stages:

1. **Data Extraction** - Extract documents from source folders
2. **Image Inpainting** - Remove existing text from images
3. **Overlap Management** - Resolve overlapping bounding boxes using percentage-based logic
4. **Text Filling** - Fill cleaned images with new text content
5. **Text Processing** - Process text-specific content
6. **Image Generation** - Convert TEX files to PNG images

## 📋 Prerequisites

- Python 3.7+
- Required packages (install via requirements.txt)
- Font files for text rendering
- Input text files in specified languages

## 📁 Project Structure

```
/root/Pager/
├── main.py                        # Main execution script
├── shoonya_extract.py             # Step 1: Data extraction
├── inpaint.py                     # Step 2: Image inpainting
├── overlaap_manage_shoonya.py     # Step 3: Overlap management
├── normal__fill_shoonya.py        # Step 4: Normal text filling
├── text_fill.py                   # Step 5: Text-specific processing
├── tex_to_png.py                  # Step 6: TEX to PNG conversion
├── fonts/                         # Font files directory
│   └── bengali/Header/
│       └── Atma-Bold.ttf
├── 1M_seed/                       # Input text files
│   ├── input_1/
│   │   ├── hindi.txt
│   │   ├── urdu.txt
│   │   ├── kashmiri.txt
│   │   └── assamese.txt
│   └── input_2/
│       └── [additional text files]
├── BBOX/                          # Bounding box files (created by pipeline)
├── images/                        # Processed images (created by pipeline)
└── Output_Tex_Files/              # TEX files (created by pipeline)
```

## 🔧 Input Format Requirements

### 1. Text Files Format
Text files should be placed in the following structure:
```
1M_seed/
├── input_1/
│   ├── hindi.txt         # Hindi text content
│   ├── urdu.txt          # Urdu text content
│   ├── kashmiri.txt      # Kashmiri text content
│   └── assamese.txt      # Assamese text content
└── input_2/
    └── [additional language files]
```

**Text File Content Format:**
```
Simple plain text content in the respective language.
Each line can contain sentences or paragraphs.
No special formatting required.
```

### 2. Document Structure
Input documents should be organized as:
```
source_documents/
├── magazines/
│   ├── doc_001/
│   ├── doc_002/
│   └── ...
└── newspapers/
    ├── doc_001/
    ├── doc_002/
    └── ...
```

### 3. BBOX Files Format
BBOX files are automatically generated with this format:
```
[image_width, image_height]
[label, [x, y, width, height], annotation_id, image_id]
[label, [x, y, width, height], annotation_id, image_id]
...
```

Example:
```
[1200, 800]
[text, [100, 50, 200, 30], text_region_1, 001]
[header, [50, 20, 300, 25], header_1, 001]
```

## 🚀 Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd Pager
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Prepare input files:**
```bash
# Create text input directory
mkdir -p 1M_seed/input_1

# Add your text files
echo "नमस्ते यह हिंदी टेक्स्ट है।" > 1M_seed/input_1/hindi.txt
echo "یہ اردو متن ہے۔" > 1M_seed/input_1/urdu.txt
echo "This is Kashmiri text." > 1M_seed/input_1/kashmiri.txt
echo "এটি অসমীয়া পাঠ্য।" > 1M_seed/input_1/assamese.txt
```

4. **Ensure font files are available:**
```bash
# Font files should be placed in:
fonts/bengali/Header/Atma-Bold.ttf
```

## 📖 Usage

### Method 1: Using main.py (Recommended)

**Basic Usage:**
```bash
python main.py --bbox-dir "BBOX" --image-dir "images" --cpus 8
```

**Full Configuration:**
```bash
python main.py \
  --cpus 8 \
  --doc_types magazines newspapers \
  --num_docs 100 \
  --languages urdu kashmiri hindi \
  --bbox-dir "BBOX" \
  --image-dir "images" \
  --hindi-text-file "1M_seed/input_1/assamese.txt" \
  --chunk-size 1 \
  --font-path "fonts/bengali/Header/Atma-Bold.ttf" \
  --input-text-folder "1M_seed" \
  --file-count 50 \
  --output_folder "Output_PNG" \
  --dpi 300 \
  --timeout 60
```

**Skip Specific Scripts:**
```bash
python main.py \
  --bbox-dir "BBOX" \
  --image-dir "images" \
  --skip-scripts inpaint.py extract_text_bbox.py
```

**Dry Run (See commands without executing):**
```bash
python main.py --bbox-dir "BBOX" --image-dir "images" --dry-run
```

### Method 2: Running Scripts Individually

#### Step 1: Data Extraction
```bash
python shoonya_extract.py \
  --doc_types magazines newspapers \
  --num_docs 50 \
  --num_cores 8 \
  --image_patterns all
```

#### Step 2: Image Inpainting
```bash
python inpaint.py --cpus 8
```

#### Step 3: Overlap Management
```bash
python overlaap_manage_shoonya.py
```

#### Step 4: Normal Text Filling
```bash
python normal__fill_shoonya.py \
  --cpus 8 \
  --bbox-dir "BBOX" \
  --image-dir "images" \
  --hindi-text-file "1M_seed/input_1/assamese.txt" \
  --chunk-size 1 \
  --font-path "fonts/bengali/Header/Atma-Bold.ttf"
```

#### Step 5: Text Processing
```bash
python text_fill.py \
  --languages urdu kashmiri hindi \
  --input-text-folder "1M_seed" \
  --file-count 100
```

#### Step 6: TEX to PNG Conversion
```bash
python tex_to_png.py \
  "Output_Tex_Files" \
  --output_folder "Output_PNG" \
  --cpus 8 \
  --dpi 300 \
  --timeout 60 \
  --log "skipped_files.txt"
```

## 🔧 Script Details

### 1. shoonya_extract.py
**Purpose:** Extract documents and images from source folders
**Key Parameters:**
- `--doc_types`: Document types to process (magazines, newspapers)
- `--num_docs`: Number of documents per type
- `--image_patterns`: Image patterns to extract

### 2. inpaint.py
**Purpose:** Remove existing text from images using inpainting
**Key Parameters:**
- `--cpus`: Number of CPU cores to use

### 3. overlaap_manage_shoonya.py
**Purpose:** Resolve overlapping bounding boxes using percentage-based logic
**Features:**
- Calculates intersection percentages
- Assigns intersections to boxes with highest percentage
- Creates non-overlapping segments
- Preserves annotation IDs

### 4. normal__fill_shoonya.py
**Purpose:** Fill cleaned images with text content
**Key Parameters:**
- `--bbox-dir`: Directory with bounding box files
- `--image-dir`: Directory with processed images
- `--hindi-text-file`: Path to text content file
- `--font-path`: Font file for text rendering

### 5. text_fill.py
**Purpose:** Process text-specific content for multiple languages
**Key Parameters:**
- `--languages`: Languages to process
- `--input-text-folder`: Folder containing language-specific text files
- `--text-file`: Specific text file (optional)

### 6. tex_to_png.py
**Purpose:** Convert TEX files to PNG images
**Key Parameters:**
- `input_folder`: Folder with TEX files
- `--output_folder`: Output directory for PNG files
- `--dpi`: Image resolution

## ⚙️ Configuration

### Text Input Configuration
The `--input-text-folder` parameter expects this structure:
```
1M_seed/               # Your input text folder
├── input_1/
│   ├── hindi.txt      # Text for Hindi processing
│   ├── urdu.txt       # Text for Urdu processing
│   ├── kashmiri.txt   # Text for Kashmiri processing
│   └── assamese.txt   # Text for Assamese processing
└── input_2/           # Additional text variations
    └── [language].txt
```

### Language Processing
When you specify `--languages urdu kashmiri hindi`, the system will:
1. Look for `1M_seed/input_1/urdu.txt`
2. Look for `1M_seed/input_1/kashmiri.txt`
3. Look for `1M_seed/input_1/hindi.txt`

### CPU Configuration
- Default: Uses all available CPU cores
- Recommendation: Use 50-75% of available cores
- Example: For 16-core system, use `--cpus 12`

## 📝 Examples

### Example 1: Basic Processing
```bash
# Process 50 documents with Hindi text
python main.py \
  --bbox-dir "BBOX" \
  --image-dir "images" \
  --num_docs 50 \
  --languages hindi \
  --cpus 4
```

### Example 2: Multi-language Processing
```bash
# Process multiple languages with custom text folder
python main.py \
  --bbox-dir "BBOX" \
  --image-dir "images" \
  --languages urdu kashmiri hindi assamese \
  --input-text-folder "my_texts" \
  --file-count 200 \
  --cpus 8
```

### Example 3: Custom Font and High DPI
```bash
# Use custom font and high resolution output
python main.py \
  --bbox-dir "BBOX" \
  --image-dir "images" \
  --font-path "fonts/custom/MyFont.ttf" \
  --dpi 600 \
  --cpus 12
```

### Example 4: Skip Inpainting for Pre-processed Images
```bash
# Skip inpainting if images are already processed
python main.py \
  --bbox-dir "BBOX" \
  --image-dir "images" \
  --skip-scripts inpaint.py \
  --cpus 8
```

## 🔍 Output Structure

After processing, you'll have:
```
BBOX/                          # Processed bounding boxes
├── document_1/
│   └── page_1.txt
├── document_2/
│   └── page_1.txt
└── ...

images/                        # Processed images
├── document_1/
│   └── page_1.png
├── document_2/
│   └── page_1.png
└── ...

Output_Tex_Files/              # Generated TEX files
├── file_1.tex
├── file_2.tex
└── ...

Output_PNG/                    # Final PNG outputs
├── file_1.png
├── file_2.png
└── ...
```

## 🐛 Troubleshooting

### Common Issues

**1. Font Not Found Error:**
```bash
# Solution: Ensure font file exists
ls fonts/bengali/Header/Atma-Bold.ttf
```

**2. Text File Not Found:**
```bash
# Solution: Create required text files
mkdir -p 1M_seed/input_1
echo "Sample text" > 1M_seed/input_1/hindi.txt
```

**3. Permission Errors:**
```bash
# Solution: Set proper permissions
chmod -R 755 /root/Pager
```

**4. Memory Issues:**
```bash
# Solution: Reduce CPU count and chunk size
python main.py --cpus 2 --chunk-size 1 --bbox-dir "BBOX" --image-dir "images"
```

### Debugging

**Enable Verbose Output:**
```bash
# Add dry-run to see commands
python main.py --dry-run --bbox-dir "BBOX" --image-dir "images"
```

**Check Individual Script Status:**
```bash
# Test individual scripts
python shoonya_extract.py --help
python inpaint.py --help
```

### Log Files

Check these log files for errors:
- `skipped_files.txt` - TEX conversion errors
- Console output - Real-time processing status

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Verify input file formats
3. Ensure all dependencies are installed
4. Check file permissions and paths

## 🔄 Pipeline Flow

```
Input Documents → Extract → Inpaint → Overlap Management → Text Fill → TEX Processing → PNG Generation
```

Each step builds on the previous, creating a complete document processing pipeline.
