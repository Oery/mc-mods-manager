import eel
import os
import re
import zipfile
import json
import requests


path = r'C:\Users\Oery\AppData\Roaming\.minecraft\19\mods\\'


def cache_result(filename, slug):
    with open('cache.json', 'r') as f:
        cache = json.load(f)

    cache[filename] = slug

    with open('cache.json', 'w') as f:
        json.dump(cache, f, indent=4)


def check_contact(data):

    homepage = data.get('contact', {}).get('homepage', "")

    if not homepage:
        return None, None

    if homepage.startswith('https://modrinth.com/mod/'):
        slug = homepage.split('/')[-1]

        url = f'https://api.modrinth.com/v2/project/{slug}'
        res = requests.get(url)

        if res.status_code != 404:
            cache_result(mod, slug)
            return slug, 'Modrinth'

    elif homepage.startswith('https://www.curseforge.com/minecraft/mc-mods/'):
        slug = homepage.split('/')[-1]
        return slug, 'Curseforge'

    return None, None

    
def check_slug(data):

    if not data.get('id', None):
        return

    url = 'https://api.modrinth.com/v2/project/' + data['id']
    res = requests.get(url)

    if res.status_code != 404:
        cache_result(mod, data['id'])
        return data['id']


def load_jar(mod):
    with zipfile.ZipFile(mod, 'r') as jar:
        info = jar.getinfo('fabric.mod.json')

        with jar.open(info) as f:
            data = json.load(f, strict=False)

        if icon_file := next((file_info for file_info in jar.infolist() if file_info.filename.endswith("/icon.png") or file_info.filename.endswith(f"{data['id']}.png")), None):
            with jar.open(icon_file) as f:
                icon_bytes = f.read()

            with open(f"./icons/{data['id']}.png", 'wb') as g:
                g.write(icon_bytes)

    return data


def check_status(mod_info):

    if not mod_info.get('status'):
        mod_info['status'] = 'unknown'
        return mod_info

    filename = mod_info['status']

    url = f'https://api.modrinth.com/v2/project/{mod_info["slug"]}/version'
    res = requests.get(url)

    if res.status_code != 200:
        mod_info['status'] = 'error'
        return mod_info

    data = res.json()

    if not mod_info.get('loaders') or not mod_info.get('game_versions'):

        for version in data:
            if version['files'][0]['filename'] == filename:
                mod_info['loaders'] = version['loaders']
                mod_info['game_versions'] = version['game_versions']
                break

            else:
                mod_info['loaders'] = None
                mod_info['game_versions'] = None

    if not mod_info['loaders'] or mod_info['game_versions']:
        mod_info['loaders'] = ['fabric']
        mod_info['game_versions'] = ['1.19']

    for version in data:

        if filename == version['files'][0]['filename']:
            mod_info['status'] = 'good'
            return mod_info

        if all(x in version['game_versions'] for x in mod_info['game_versions']) and all(x in version['loaders'] for x in mod_info['loaders']):
            mod_info['status'] = 'update'
            return mod_info

    mod_info['status'] = 'update'
    return mod_info


    
def search_name(data):

    if not data.get('name', None):
        return

    name = re.sub(r'([A-Z])', r' \1', data['name']).replace(" ", "%20")
    url = f'https://api.modrinth.com/v2/search?query={name}'
    res = requests.get(url)

    if res.status_code != 200:
        return

    results = res.json()

    if len(results['hits']) == 0:
        return

    return results['hits']


def search_slug(data):
    url = 'https://api.modrinth.com/v2/search?query=' + data['id']
    res = requests.get(url)

    if res.status_code != 200:
        return

    results = res.json()

    if len(results['hits']) == 0:
        return

    return results['hits']


def check_version(slug):
    url = f'https://api.modrinth.com/v2/project/{slug}/version'
    res = requests.get(url)

    if res.status_code != 200:
        return

    version_data = res.json()

    for version in version_data:
        if version['files'][0]['filename'] == mod:
            cache_result(mod, slug)
            return True


class Main:


    def __init__(self, path):

        with open('cache.json', 'r') as f:
            self.cache = json.load(f)

        self.path = path
        self.eel = eel
        self.eel.init('web')


    def start_ui(self):
        self.eel.start(
            'app.html',
            port=8477,
            block = False,
            mode = 'chrome',
            cmdline_args = ['--disable-extensions']
        )

        eel.sleep(5)


    def get_mods(self):

        files = os.listdir(self.path)
        mods = filter(lambda file: file.endswith(".jar"), files)

        return list(mods)


    def get_mod_info(self, mod, slug=None):

        if mod in self.cache:
            slug = self.cache[mod]

        if not slug:
            mod_info = self.parse_mod(mod)
            slug = mod_info['slug']

        print(slug)

        url = f'https://api.modrinth.com/v2/project/{slug}'
        res = requests.get(url)

        if res.status_code != 200:
            return

        data = res.json()
              
        mod_info = {
            'name': data['title'],
            'slug': slug,
            'icon_path': data['icon_url'],
            'status': mod
        }
        
        status = check_status(mod_info)

        eel.addMod(status)
        


    def parse_mod(self, mod):

        data = load_jar(self.path + mod)
        slug, origin = check_contact(data)

        mod_info = {
            'name': data.get('name', 'id'),
            'slug': data['id'],
            'icon_path': f'./icons/{data["id"]}.png',
            'loaders': ['fabric', 'quilt']
        }

        if origin == 'Modrinth':
            mod_info['slug'] = slug
            return mod_info

        # elif origin == 'Curseforge':
        #     pass

        if hits := search_slug(data):
            for hit in hits:
                if check_version(hit['slug']):
                    mod_info['slug'] =  hit['slug']
                    return mod_info

        if hits := search_name(data):
            for hit in hits:
                if check_version(hit['slug']):
                    mod_info['slug'] = hit['slug']
                    return mod_info

        return mod_info


if __name__ == '__main__':
    app = Main(path)
    mods = app.get_mods()
    found, notfound = 0, 0


    app.start_ui()


    for mod in mods:
        status = app.get_mod_info(mod)

    print(found, notfound)

    while True:
        eel.sleep(1)