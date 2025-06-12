import json
import pandas as pd
import os

langs_list = ['gu']
lang_dict = {'gu': 'Gujarati'}

for lang_prefix in langs_list:
    folder_path = f'sample_{lang_prefix}_coco_jsons'
    output_file = f'shoonya_outputs_{lang_prefix}.csv'

    new_rows = []

    if not os.path.isdir(folder_path):
        print(f"Error: Folder '{folder_path}' not found.")
        continue

    for filename in os.listdir(folder_path):
        if not filename.endswith('.json'):
            continue

        file_path = os.path.join(folder_path, filename)

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if not data.get('images') or not isinstance(data['images'], list) or not data['images']:
                print(f"Skipping file, 'images' missing or empty: {filename}")
                continue

            image_info = data['images'][0]
            original_width = image_info.get('width', 0)
            original_height = image_info.get('height', 0)
            image_filename = image_info.get('file_name', '')

            if not image_filename:
                print(f"Skipping file, 'file_name' missing in images: {filename}")
                continue

            if original_width == 0 or original_height == 0:
                print(f"Skipping file due to zero width/height: {filename}")
                continue

            scale_x = 100 / original_width
            scale_y = 100 / original_height

            annotations = data.get("annotations", [])
            boxes_data = []

            for i, box in enumerate(annotations):
                if 'bbox' not in box or len(box['bbox']) != 4:
                    print(f"Skipping annotation #{i}, invalid bbox: {filename}")
                    continue
                if 'text' not in box or 'category_name' not in box:
                    print(f"Skipping annotation #{i}, missing text/category: {filename}")
                    continue

                x1 = box['bbox'][0] * scale_x
                y1 = box['bbox'][1] * scale_y
                x2 = (box['bbox'][0] + box['bbox'][2]) * scale_x
                y2 = (box['bbox'][1] + box['bbox'][3]) * scale_y

                boxes_data.append({
                    'x': x1,
                    'y': y1,
                    'width': x2 - x1,
                    'height': y2 - y1,
                    'shoonya_bbox': [x1, y1, x2, y2],
                    'text': box['text'],
                    'bbox': [box['bbox'][0], box['bbox'][1], box['bbox'][0]+box['bbox'][2], box['bbox'][1]+box['bbox'][3]],
                    'original_width': original_width,
                    'original_height': original_height,
                    'id': os.path.splitext(image_filename)[0],
                    'parentID': None,
                    'rotation': 0,
                    'labels': [box['category_name']]
                })

            file_ext = os.path.splitext(image_filename)[1].lstrip('.').upper()
            image_url = f"https://objectstore.e2enetworks.net/indic-ocr-oik/sample_{lang_prefix}/{image_filename}"
            metadata_json_str = json.dumps(data["images"], ensure_ascii=False)
            ocr_prediction_json_str = json.dumps(boxes_data, ensure_ascii=False)

            new_row = {
                'id': None,
                'metadata_json': metadata_json_str,
                'draft_data_json': None,
                'file_type': file_ext,
                'image_url': image_url,
                'page_number': 1,
                'language': lang_dict.get(lang_prefix, lang_prefix),
                'ocr_type': 'DT',
                'ocr_domain': 'NV',
                'ocr_transcribed_json': None,
                'ocr_prediction_json': ocr_prediction_json_str,
                'image_details_json': None,
                'parent_data': None,
                'instance_id': None,
                'lp_prediction_json': ocr_prediction_json_str
            }

            new_rows.append(new_row)

        except json.JSONDecodeError:
            print(f"Error decoding JSON: {file_path}")
        except Exception as e:
            print(f"Unexpected error in file {file_path}: {e}")

    if new_rows:
        df_new = pd.DataFrame(new_rows)
        df_new.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"✅ Saved '{output_file}' with {len(df_new)} rows.")
    else:
        print(f"⚠️ No data processed for: {lang_prefix}")


# import json
# import pandas as pd
# import os

# title_dict = {'nv' : 'Novels', 'rp' : 'Research_Papers', 'sy' : 'Syllabus', 'tb' : 'Textbooks', 'ar' : 'Acts_Rules',
#                 'br' : 'Brochure_Posters_Leaflets', 'np' : 'Newspapers', 'fm' : 'Form', 'mg' : 'Magazines', 'mn' : 'Manual',
#                 'nt' : 'Notices', 'qp' : 'Question_Papers'}

# lang_dict = {'as': 'Assamese', 'bn': 'Bengali', 'bd': 'Bodo', 'do': 'Dogri', 'en': 'English', 'gu': 'Gujarati', 'hi': 'Hindi',
#             'kn': 'Kannada', 'ks': 'Kashmiri', 'kk': 'Konkani', 'mt': 'Maithili', 'ml': 'Malayalam', 'mp': 'Manipuri',
#             'mr': 'Marathi', 'ne': 'Nepali', 'or': 'Odia', 'pa': 'Punjabi', 'sa': 'Sanskrit', 'sn': 'Santhali', 'sd': 'Sindhi',
#             'ta': 'Tamil', 'te': 'Telugu', 'ur': 'Urdu'}


# # langs_list = ['mr', 'bn', 'pa', 'or', 'ta', 'te', 'kn', 'ml']
# langs_list = ['gu']  

# for lang_prefix in langs_list:
#     folder_path = f'sample_{lang_prefix}_coco_jsons' # Make sure this folder exists and has your JSON files
#     output_file = f'shoonya_outputs_{lang_prefix}.csv'

#     new_rows = []

#     if not os.path.isdir(folder_path):
#         print(f"Error: Folder '{folder_path}' not found. Please create it and add your JSON files.")
#     else:
#         for filename in os.listdir(folder_path):
#             if not filename.endswith('.json'):
#                 # print(f"Skipping non-JSON file: {filename}") # Optional: uncomment to see skipped files
#                 continue

#             file_path = os.path.join(folder_path, filename)
#             try:
#                 with open(file_path, 'r', encoding='utf-8') as f: # Ensure source JSONs are read as UTF-8
#                     fn_parts = filename.split('.')[0].split('_')
#                     if len(fn_parts) < 3:
#                         print(f"Skipping file with unexpected name format: {filename}")
#                         continue
                    
#                     pgno_str = fn_parts[2]
#                     lang_key = fn_parts[1]
#                     ocr_domain_key = fn_parts[0]

#                     try:
#                         pgno = int(pgno_str)
#                     except ValueError:
#                         print(f"Skipping file, could not parse page number: {filename}")
#                         continue
                    
#                     lang = lang_dict.get(lang_key)
#                     if lang is None:
#                         print(f"Skipping file, unknown language key '{lang_key}': {filename}")
#                         continue
                    
#                     ocr_domain = ocr_domain_key.upper() 
                    
#                     data = json.load(f)
                    
#                     if not data.get('images') or not isinstance(data['images'], list) or not data['images']:
#                         print(f"Skipping file, 'images' field is missing, not a list, or empty: {filename}")
#                         continue
#                     if 'width' not in data['images'][0] or 'height' not in data['images'][0]:
#                         print(f"Skipping file, 'width' or 'height' missing in image data: {filename}")
#                         continue
                        
#                     original_width = data['images'][0]['width']
#                     original_height = data['images'][0]['height']

#                     if original_width == 0 or original_height == 0:
#                         print(f"Skipping file due to zero width/height: {filename}")
#                         continue

#                     scale_x = 100 / original_width
#                     scale_y = 100 / original_height

#                     annotations = data.get("annotations", [])
#                     boxes_data = []
#                     for box_annotation_index, box in enumerate(annotations): # Added index for more specific error reporting
#                         box_data = {}
                        
#                         if 'bbox' not in box or len(box['bbox']) != 4:
#                             print(f"Skipping annotation #{box_annotation_index} due to missing/invalid 'bbox' in file: {filename}")
#                             continue
#                         if 'text' not in box:
#                             print(f"Skipping annotation #{box_annotation_index} due to missing 'text' in file: {filename}")
#                             continue
#                         if 'category_name' not in box:
#                             print(f"Skipping annotation #{box_annotation_index} due to missing 'category_name' in file: {filename}")
#                             continue


#                         box1 = [box['bbox'][0], box['bbox'][1], box['bbox'][0] + box['bbox'][2], box['bbox'][1] + box['bbox'][3]]
#                         x1 = box1[0] * scale_x
#                         y1 = box1[1] * scale_y
#                         x2 = box1[2] * scale_x
#                         y2 = box1[3] * scale_y
                        
#                         box_data['x'] = x1
#                         box_data['y'] = y1
#                         box_data['width'] = x2 - x1
#                         box_data['height'] = y2 - y1

#                         box_data['shoonya_bbox'] = [x1, y1, x2, y2]
#                         box_data['text'] = box['text'] # This is where your Indic text is
#                         box_data['bbox'] = box1
#                         box_data['original_width'] = original_width
#                         box_data['original_height'] = original_height
#                         box_data['id'] = fn_parts[0] 
#                         box_data['parentID'] =  None
#                         box_data['rotation'] = 0
#                         box_data['labels'] = [box['category_name']]

#                         boxes_data.append(box_data)

#                     image_url = f"https://objectstore.e2enetworks.net/indic-ocr-oik/sample_{lang_prefix}/{filename.split('.')[0]}.png"
                    
#                     # --- CHANGES ARE HERE ---
#                     # Use ensure_ascii=False to keep Indic characters as they are
#                     metadata_json_str = json.dumps(data["images"], ensure_ascii=False)
#                     ocr_prediction_json_str = json.dumps(boxes_data, ensure_ascii=False)
#                     lp_prediction_json_str = json.dumps(boxes_data, ensure_ascii=False)

#                     new_row = {
#                                     'id': None, 
#                                     'metadata_json' : metadata_json_str,
#                                     'draft_data_json' : None,
#                                     'file_type' : 'PNG', 'image_url' : image_url,
#                                     'page_number' : pgno, 'language' : lang, 'ocr_type' : 'DT', 'ocr_domain' : ocr_domain,
#                                     'ocr_transcribed_json' : None, 
#                                     'ocr_prediction_json' : ocr_prediction_json_str,
#                                     'image_details_json' : None,
#                                     'parent_data' : None, 'instance_id' : None, 
#                                     'lp_prediction_json' : lp_prediction_json_str
#                                 }
#                     new_rows.append(new_row)
#             except json.JSONDecodeError:
#                 print(f"Error decoding JSON from file: {file_path}") # Show full path
#             except KeyError as e:
#                 print(f"Missing key {e} in JSON structure of file: {file_path}") # Show full path
#             except Exception as e:
#                 print(f"An unexpected error occurred while processing file {file_path}: {e}") # Show full path


#         if new_rows:
#             df_new = pd.DataFrame(new_rows)
#             df_new.to_csv(output_file, index = False, encoding='utf-8-sig')
#             print(f"Successfully created '{output_file}' with {len(df_new)} rows. Indic characters should be preserved.")
#         else:
#             print("No data was processed to create the CSV file.")