import os

folder = '/root/Pager/sample_hi'
output_txt = '/root/Pager/sample_hi_image_urls.txt'
base_url = 'https://objectstore.e2enetworks.net/indic-ocr-oik/sample_hi/'

files = os.listdir(folder)
image_files = [f for f in files if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

with open(output_txt, 'w') as f:
    for fname in image_files:
        f.write(base_url + fname + '\n')

print(f"Saved {len(image_files)} image URLs to {output_txt}")
