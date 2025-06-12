import requests

workspace_mapping = {
    "OCR_Benchmark_SARVAM_WORKSPACE": 175
}

workspace_id = workspace_mapping.get("OCR_Benchmark_SARVAM_WORKSPACE", 175)




dataset_ids = {
    'bn': 744,
    'ta': 745,
    'te': 746,
    'mr': 747,
    'ml': 748,
    'kn': 749,
    'or': 750,
    'pa': 751,
    'gu': 753
}

dataset_short_to_long = {
    'bn': 'Bengali',
    'ta': 'Tamil',
    'te': 'Telugu',
    'mr': 'Marathi',
    'ml': 'Malayalam',
    'kn': 'Kannada',
    'or': 'Odia',
    'pa': 'Punjabi',
    'gu': 'Gujarati'
}


# lang_list = ['bn', 'ta', 'te', 'mr', 'ml', 'kn', 'or', 'pa']
lang_list = ['gu']

base_url = "https://backend.shoonya.ai4bharat.org/projects/"

headers = {
    "Authorization": 'JWT eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzU2MDIwMjYyLCJqdGkiOiIzYWZiZmZmMmNhMDA0NDIzOGRjZGQwNjVhMjRiMGJkMyIsInVzZXJfaWQiOjF9.mIhC7UwaFC3f5E5fa56edwUVnrZQcYE_HyoIU-Yq4gk',
    "Content-Type": "application/json"
}

# projects_do_not_touch = {"Marathi": ["MG", "NT"], "Tamil": ["MG", "NT", "SY"], "Telugu": ["MG", "AR"], "English": ["MG", "AR"], "Gujarati": ["MG"]}


for lang in lang_list:

    # language = workspace_name.split('_')[0]
    dataset_id = dataset_ids[lang]
    print(lang, dataset_id)

    project_title = f"OCR_Benchmark_SARVAM_{dataset_short_to_long[lang]}"
    print(project_title)
    payload = {
        "title": project_title,
        "description": f"OCR Benchmark for {dataset_short_to_long[lang]} (SARVAM)",
        "created_by": 1,
        "is_archived": 'false',
        "is_published": 'true',
        "users": [1],
        "workspace_id": str(workspace_id),
        "organization_id": 1,
        "tgt_language": dataset_short_to_long[lang],
        # "filter_string": filter_string,
        "sampling_mode": "f",
        "sampling_parameters_json": {},
        "project_type": "OCRTranscriptionEditing",
        "dataset_id": [str(dataset_id)],
        "label_config": "string",
        "variable_parameters": {},
        "project_mode": "Annotation",
        "required_annotators_per_task": 1,
        "project_stage": 3,
        "acoustic_enabled_stage": None
    }
    response = requests.post(base_url, json=payload, headers=headers)
    print(payload)


    if response.status_code == 200:
        print(f"Project '{project_title}' created successfully!")
    else:
        print(f"Failed to create project '{project_title}'. Status code: {response.status_code}")
