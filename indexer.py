import contextlib
import requests
import json
import os
import time

with open("index.json", "r") as f:
    index = json.load(f)

with open("mods_full.json", "r") as f:
    slugs = json.load(f)

for slug in slugs:

    with contextlib.suppress(Exception):
        # if slug == 'fabric-api':
        #     continue

        if slug not in index:
            index[slug] = {}

        url = f'https://api.modrinth.com/v2/project/{slug}/version'

        time.sleep(0.1)
        res = requests.get(url, timeout=10).json()

        supported_versions = []

        for version in res:

            download = False

            url = version['files'][0]['url']
            filename = version['files'][0]['filename']
            file_url = version['files'][0]['url']
            version_name = version['name']
            version_id = version['id']

            index[slug][version_id] = {
                'version_name': version['name'],
                'game_versions': version['game_versions'],
                'loaders': version['loaders'],
                'filename': filename,
                'url': file_url,
            }

            for game_version in version['game_versions']:
                
                # if any(x in game_version for x in ['pre', 'w', 'rc']):
                #     continue
                
                # if game_version not in supported_versions:
                #     download = True

                supported_versions.append(game_version)

            print(f'Indexed {filename}')

            if not download:
                continue
            
            time.sleep(0.1)
            file = requests.get(url)

            if not os.path.exists(f'mods/{slug}'):
                os.makedirs(f'mods/{slug}')

            if not os.path.exists(f'mods/{slug}/{version_name}'):
                os.makedirs(f'mods/{slug}/{version_name}')

            open(f'mods/{slug}/{version_name}/{filename}', 'wb').write(file.content)


with open("index.json", "w") as f:
    json.dump(index, f)