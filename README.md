# Pager: Document Text Generation Pipeline

## Overview

Pager is a comprehensive pipeline for generating synthetic text documents with customizable parameters. It extracts document templates from Shoonya, removes existing text through inpainting, creates text bounding boxes, populates these boxes with new text content, and finally renders the documents as PNG images.

The pipeline processes documents in a sequential manner, where each script builds upon the output of the previous one, resulting in high-quality synthetic text documents in multiple languages.

## Installation

### Clone the Repository

```bash
git clone https://github.com/VIVEKREDDYGOLLALA/Pager
cd Pager
```

### Requirements

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Pipeline Components

The pipeline consists of the following scripts executed in sequence:

1. **shoonya_extract.py**: Extracts document templates from Shoonya based on document type
2. **inpaint.py**: Removes existing text from images using inpainting techniques
3. **normal__fill_shoonya.py**: Creates bounding boxes for text lines with assumed font sizes
4. **extract_text_bbox.py**: Extracts bounding box information from JSON files
5. **clear_textlines.py**: Clears existing text line data from JSON files
6. **textline_fill_shoonya.py**: Populates text lines in the JSON files and generates TeX files
7. **tex_to_png.py**: Compiles TeX files into PNG images

## Usage

### Running the Complete Pipeline

The entire pipeline can be executed using the `main.py` script, which runs all the component scripts in the correct order with the specified parameters.

```bash
python main.py --doc_type [DOCUMENT_TYPE] --num_docs [NUMBER_OF_DOCUMENTS] --languages [SPACE_SEPARATED_LANGUAGES] --output_folder [OUTPUT_FOLDER] --cpus [NUMBER_OF_CPUS] --dpi [DPI_VALUE] --timeout [TIMEOUT_IN_SECONDS] --log_file [LOG_FILE_PATH]
```

#### Parameters:

- `--doc_type`: Type of document to extract from Shoonya (e.g. "novels", "magazines")
- `--num_docs`: Number of documents to process
- `--languages`: Space-separated list of languages to generate text in (e.g. "hindi telugu bengali")
- `--output_folder`: Folder to save the generated PNG images
- `--cpus`: Number of CPU cores to use for converting tex code to pngs
- `--dpi`: DPI resolution for output images
- `--timeout`: Timeout in seconds for TeX compilation
- `--log_file`: Path to the log file

### Example:

```bash
python main.py --doc_type magazines --num_docs 100 --languages "hindi telugu bengali" --output_folder output_images --cpus 32 --dpi 300 --timeout 60 --log_file ./logs/process.log
```

## Pipeline Workflow

### 1. Document Extraction

The pipeline begins by extracting document templates from Shoonya using `shoonya_extract.py`. This script fetches documents of the specified type and quantity, saving them with unique image IDs.

```bash
python shoonya_extract.py --doc_type magazines --num_docs 50
```

### 2. Text Removal via Inpainting

Next, `inpaint.py` processes the extracted images to remove any pre-existing text, creating clean templates for new text insertion.

```bash
python inpaint.py
```

### 3. Text Box Generation

The `normal__fill_shoonya.py` script analyzes the inpainted images and creates bounding boxes for text lines with appropriate font sizes.

```bash
python normal__fill_shoonya.py
```

### 4. Bounding Box Extraction

`extract_text_bbox.py` extracts the bounding box information from the generated JSON files for further processing.

```bash
python extract_text_bbox.py
```

### 5. Text Line Clearing

`clear_textlines.py` removes any existing text line data from the JSON files to prepare them for new content.

```bash
python clear_textlines.py
```

### 6. Text Line Population

`textline_fill_shoonya.py` populates the cleared text lines with new content in the specified languages and generates corresponding TeX files.

```bash
python textline_fill_shoonya.py --languages urdu kashmiri bengali
```

### 7. TeX to PNG Conversion

Finally, `tex_to_png.py` compiles the generated TeX files into PNG images and saves them in the specified output folder.

```bash
python tex_to_png.py Output_Tex_Files --output_folder ./output_images --cpus 4 --dpi 300 --timeout 60 --log ./logs/tex_compilation.log
```

## Output Structure

The pipeline generates the following outputs:

- **Images**: Stored in the specified output folder
- **JSON Files**: Stored in the `output_jsons` folder, organized by language
- **TeX Files**: Generated in the `Output_Tex_Files` directory

## Troubleshooting

If the pipeline execution stops due to an error in any script, check the error message and the corresponding script. The `main.py` script will not proceed to the next script if the current one fails.
