import requests
import json
import os

# Mapping workspace names to IDs
workspaces_name_to_id_map = {
    'Assamese': 66,
    'Bengali': 67,
    'Gujarati': 68,
    'Hindi': 69,
    'Kannada': 70,
    'Malayalam': 71,
    'Marathi': 72,
    'Odia': 73,
    'Punjabi': 74,
    'Tamil': 75,
    'Telugu': 76,
    'English': 77,
    'Bodo': 116,
    'Dogri': 117,
    'Konkani': 119,
    'Maithili': 120,
    'Nepali': 122,
    'Sanskrit': 123,
    'Sindhi': 125,
}

# Authentication token
auth_token = 'JWT eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzU2MDIwMjYyLCJqdGkiOiIzYWZiZmZmMmNhMDA0NDIzOGRjZGQwNjVhMjRiMGJkMyIsInVzZXJfaWQiOjF9.mIhC7UwaFC3f5E5fa56edwUVnrZQcYE_HyoIU-Yq4gk'

# Iterate through each language
for language in workspaces_name_to_id_map.keys():
    print(f"Processing language: {language}")

    # Create directories for the language
    os.makedirs(f'jsons/{language}', exist_ok=True)
    os.makedirs(f'./{language}', exist_ok=True)

    # Fetch project details for the current language
    try:
        response = requests.get(
            f"https://backend.shoonya.ai4bharat.org/workspaces/{workspaces_name_to_id_map[language]}/projects/",
            headers={'Authorization': auth_token}
        )
        response.raise_for_status()  # Raise an exception for bad status codes
        projects = response.json()
    except requests.RequestException as e:
        print(f"Failed to fetch projects for {language}: {str(e)}")
        continue

    # Filter out archived projects and keep only those with 'LP' in the title (Novels)
    filtered_projects = [project for project in projects if not project.get('is_archived', False) and 'LP' in project['title']]

    # Save the project metadata to a JSON file
    with open(f'./{language}/{language}_response.json', 'w') as json_file:
        json.dump(filtered_projects, json_file, indent=4)

    # Extract project IDs and titles
    p_ids = [project['id'] for project in filtered_projects]
    p_zip = {project['id']: '_'.join(project['title'].split('_')[3:-1]) for project in filtered_projects}
    print(f"Project ID to Title Mapping for {language}: {p_zip}")

    # Initialize list to store all JSON data for the current language
    all_data = []

    # Iterate through each project and download JSON data
    for p_id in p_ids:
        try:
            response = requests.get(
                f"https://backend.shoonya.ai4bharat.org/projects/{p_id}/download?export_type=JSON&include_input_data_metadata_json=\"true\"",
                headers={'Authorization': auth_token}
            )
            response.raise_for_status()  # Raise an exception for bad status codes

            # Parse the JSON data
            project_data = response.json()

            # Save the JSON data to an individual file
            with open(f'jsons/{language}/{language}_{p_zip[p_id]}_{p_id}.json', 'w') as json_file:
                json.dump(project_data, json_file, indent=4)

            print(f"Downloaded Project {p_id} for {language}")

            # Add data to the all_data list
            all_data.extend(project_data)
        except requests.RequestException as e:
            print(f"Failed to download data for Project {p_id} in {language}: {str(e)}")
            continue

    # Save the concatenated JSON data for the language
    with open(f'./{language}/{language}_main.json', 'w') as main_file:
        json.dump(all_data, main_file, indent=4)

    print(f"All project data for {language} saved to ./{language}/{language}_main.json")