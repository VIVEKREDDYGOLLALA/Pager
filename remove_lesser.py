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

    # First add all packages
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

    # Map language to script
    script_mapping = {
        'assamese': 'Bengali', 'bengali': 'Bengali', 'bodo': 'Devanagari', 'dogri': 'Devanagari',
        'gujarati': 'Gujarati', 'hindi': 'Devanagari', 'kannada': 'Kannada', 'kashmiri': 'Arabic',
        'konkani': 'Devanagari', 'maithili': 'Devanagari', 'malayalam': 'Malayalam', 'manipuri': 'Meetei Mayek',
        'marathi': 'Devanagari', 'nepali': 'Devanagari', 'odia': 'Oriya', 'punjabi': 'Gurmukhi',
        'sanskrit': 'Devanagari', 'santali': 'Ol Chiki', 'sindhi': 'Arabic', 'tamil': 'Tamil',
        'telugu': 'Telugu', 'urdu': 'Arabic'
    }
    script = script_mapping.get(language, 'Devanagari')
    
    # Set the main and other language in the preamble
    doc.preamble.append(NoEscape(f'\\setmainlanguage{{{language}}}'))
    doc.preamble.append(NoEscape(f'\\setotherlanguage{{english}}'))
    
    # Define the script-specific font required by polyglossia
    # Get the lowercase script name to match polyglossia's naming convention
    script_lowercase = script.lower()
    
    # Define the script font with the same font as paragraphfont
    doc.preamble.append(NoEscape(f'\\newfontfamily\\{script_lowercase}font[Script={script},Path={os.path.dirname(paragraph_font_path)}/]{{{os.path.basename(paragraph_font_path).replace(".ttf", "")}}}'))
    
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