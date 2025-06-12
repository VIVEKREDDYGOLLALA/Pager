import os
import random
import shutil

doc_cats = ['ar', 'br', 'fm', 'nv', 'np', 'mg', 'mn', 'rp', 'nt', 'sy', 'tb', 'br']
src_dir = '/root/Pager/indicdlp/images/test'
label_dir = '/root/Pager/indicdlp/labels/test'

langs_list = ['mr', 'bn', 'pa', 'or', 'ta', 'te', 'kn', 'ml']

for lang in langs_list:

    dst_img_dir = f'/root/Pager/sample_{lang}'
    dst_label_dir = os.path.join(dst_img_dir, 'labels')

    test_images = os.listdir(src_dir)
    test_images.sort()

    final_list = []

    for doc_cat in doc_cats:
        lang_hi_images = [img for img in test_images if f'{doc_cat}_{lang}' in img]
        final_list.extend(random.sample(lang_hi_images, min(12, len(lang_hi_images))))

    os.makedirs(dst_img_dir, exist_ok=True)
    os.makedirs(dst_label_dir, exist_ok=True)

    for img_name in final_list:
        shutil.copy(os.path.join(src_dir, img_name), os.path.join(dst_img_dir, img_name))
        
        label_name = os.path.splitext(img_name)[0] + '.txt'
        label_src = os.path.join(label_dir, label_name)
        label_dst = os.path.join(dst_label_dir, label_name)
        if os.path.exists(label_src):
            shutil.copy(label_src, label_dst)

    print(f"Copied {len(final_list)} images and labels to {dst_img_dir}")
