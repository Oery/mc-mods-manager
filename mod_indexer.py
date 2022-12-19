import requests
from bs4 import BeautifulSoup
import re
import json

index = 0
slug_list = []

with open("mods_full.json", "r") as f:
    slug_list = json.load(f)

while True:

    res = requests.get(f'https://modrinth.com/mods?o={index}&m=100')

    soup = BeautifulSoup(res.content, features="html.parser")

    elements = soup.select("#search-results > article > div > div > a")

    for element in elements:
        element = str(element)
        slug = re.findall('(?<=<a data-v-753afd63="" href="\/mod\/)(.*)(?="><img alt=")', string=element)

        if not slug:
            continue

        slug = slug[0]

        print(slug)
        
        if slug not in slug_list:
            slug_list.append(slug)

    index += 100

    with open("mods_full.json", "w") as f:
        json.dump(slug_list, f, indent=4)