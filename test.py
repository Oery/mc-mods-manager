import requests
import json

with open('mods.json', "r") as f:
    mods = json.load(f)

for project_slug in mods:
    url = f'https://api.modrinth.com/v2/project/{project_slug}/version'

    data = requests.get(url).json

    for latest_version in data():

        if latest_version["version_type"] == "release":
            download = latest_version['files'][0]['url']
            file_name = latest_version['files'][0]['filename']

            file = requests.get(download)
            open(f'mods/{file_name}', 'wb').write(file.content)

            break
