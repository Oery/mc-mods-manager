import os
import json
import requests

path = r"C:\Users\Oery\AppData\Roaming\.minecraft\\19\mods\\"

with open('index.json', 'r') as i:
    index = json.load(i)

for file in os.listdir(path):

    if '.jar' not in file:
        continue

    found = False
    for mod in index:

        latest = None

        for version in index[mod]:

            if file == index[mod][version]["filename"]:
                found = True

                for version in index[mod]:
                    if latest is None and 'fabric' in index[mod][version]["loaders"] and "1.19.2" in index[mod][version]["game_versions"]:
                        latest = version
                        break

                if not latest:
                    break

                if file != index[mod][latest]["filename"]:

                    new_file = requests.get(index[mod][latest]["url"])
                    name = index[mod][latest]["filename"]

                    open(path + name, 'wb').write(new_file.content)
                    os.remove(r"C:\Users\Oery\AppData\Roaming\.minecraft\19\mods\\" + file)
                    print('Replaced', file, 'with', index[mod][latest]["filename"])

                break

    if not found:
        print(f'{file} didnt get detected')
