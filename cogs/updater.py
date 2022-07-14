from threading import Thread
from zipfile import ZipFile
import os
import discord
import json
import requests
import asyncio
from discord.ext import commands, tasks

class Updater(commands.Cog):

    def cog_unload(self):
        if self.fetch_updates_task.is_running():
            self.fetch_updates_task.stop()

    def __init__(self, client):
        self.client = client
        client.loop.create_task(self.prepare_method())

    def write_in(self, file, data):
        with open(f"{file}.json", "w") as f:
            json.dump(data, f)

    def load_from(self, file):
        with open(f"{file}.json", "r") as f:
            return json.load(f)

    async def get_updates(self):
        channel = self.client.get_channel(996599085521977414)

        mods = self.load_from('mods')

        for project_slug in mods:
            
            try:
                print('fetching updates for', project_slug)

                await asyncio.sleep(1)
                url = f'https://api.modrinth.com/v2/project/{project_slug}/version'
                project_url = f'https://api.modrinth.com/v2/project/{project_slug}'
                
                data = requests.get(url).json
                await asyncio.sleep(2)
                
                project_data = requests.get(project_url).json

                for latest_version in data():
                    
                    latest_versions = self.load_from('latest_versions')

                    if latest_version["version_number"] in latest_versions:
                        break

                    if latest_version["version_type"] == "release":
                        
                        if len(latest_version["game_versions"]) == 1:
                            mc_versions = latest_version["game_versions"][0]
                        else:
                            mc_versions = "".join(f"{x}  " for x in latest_version["game_versions"])

                        if len(latest_version["loaders"]) == 1:
                            loaders = latest_version["loaders"][0].capitalize()
                        else:
                            loaders = "".join(f"{x.capitalize()} " for x in latest_version["loaders"])

                        embed=discord.Embed(title=project_data()["title"], url=latest_version['files'][0]['url'], color=0x1bd96a)
                        embed.set_thumbnail(url=project_data()["icon_url"])
                        embed.add_field(name="Version", value=latest_version['name'], inline=True)
                        embed.add_field(name="Versions Minecraft", value=mc_versions, inline=True)
                        embed.add_field(name="Mod Loaders", value=loaders, inline=False)
                        embed.set_footer(text=latest_version["changelog"][:300] + "...")
                        await channel.send(embed=embed)

                        latest_versions.append(latest_version['version_number'])
                        self.write_in('latest_versions', latest_versions)

                        break

            except Exception:
                print('failed to fetch updates for', project_slug)


    async def prepare_method(self):
        await self.client.wait_until_ready()

        self.fetch_updates_task = self.fetch_updates.start()

    @commands.is_owner()
    @commands.command()
    async def add_mod(self, ctx, *args):

        if args == []:
            await ctx.reply("Veuillez spécifier un mod !", mention_author=False)
            return

        for mod in args:
            res = requests.get(f'https://api.modrinth.com/v2/project/{mod}')
            
            if res.status_code != 200:
                await ctx.reply(f"Le mod {mod} n'a pas été trouvé.", mention_author=False)
                continue
            
            mods = self.load_from('mods')
            title = res.json()["title"]

            if mod in mods:
                await ctx.reply(f"Le mod {title} est déjà dans la liste.", mention_author=False)
                continue

            mods.append(mod)
            self.write_in('mods', mods)

            await ctx.reply(f"Le mod {title} a été ajouté à la liste.", mention_author=False)


    @commands.is_owner()
    @commands.command()
    async def remove_mod(self, ctx, *args):

        if args == []:
            await ctx.reply("Veuillez spécifier un mod !", mention_author=False)
            return

        for mod in args:
            mods = self.load_from('mods')

            if mod not in mods:
                await ctx.reply(f"Le mod {mod} n'est pas dans la liste.", mention_author=False)
                continue

            mods.remove(mod)
            self.write_in('mods', mods)

            await ctx.reply(f"Le mod {mod} a été retiré de la liste.", mention_author=False)


    @commands.is_owner()
    @commands.command()
    async def updates(self, ctx):
        await ctx.reply("Fetching Updates !", mention_author=False)
        await self.get_updates(ctx)
    
    @commands.command()
    async def mod(self, ctx, mod, version="", loader=""):

        if version == "":
            version = False

        if loader == "":
            loader = False
        
        url = 'https://api.modrinth.com/v2/search'

        params = {
            'query': mod,
        }

        res = requests.get(url, params=params)

        slug = res.json()['hits'][0]['slug']
        title = res.json()['hits'][0]['title']
        icon_url = res.json()['hits'][0]['icon_url']

        url = f'https://api.modrinth.com/v2/project/{slug}/version'

        res = requests.get(url)

        for release in res.json():

            if version and version not in release['game_versions']:
                continue

            if loader and loader not in release['loaders']:
                continue

            break
        
        if len(release["game_versions"]) == 1:
            mc_versions = release["game_versions"][0]
        else:
            mc_versions = "".join(f"{x}  " for x in release["game_versions"])

        if len(release["loaders"]) == 1:
            loaders = release["loaders"][0].capitalize()
        else:
            loaders = "".join(f"{x.capitalize()} " for x in release["loaders"])

        embed=discord.Embed(title=title, url=release['files'][0]['url'], color=0x1bd96a)
        embed.set_thumbnail(url=icon_url)
        embed.add_field(name="Version", value=release['name'], inline=True)
        embed.add_field(name="Versions Minecraft", value=mc_versions, inline=True)
        embed.add_field(name="Mod Loaders", value=loaders, inline=False)
        embed.set_footer(text=release["changelog"][:300] + "...")
        await ctx.reply(embed=embed, mention_author=False)

    @commands.is_owner()
    @commands.command()
    async def listmod(self, ctx):
        mods = self.load_from('mods')
        msg = "```"

        for mod in mods:
            msg += f"{mod}   "
        msg += "```"

        await ctx.reply(msg, mention_author=False)


    @commands.is_owner()
    @commands.command()
    async def dlmodpack(self, ctx, version="1.19"):
        msg = await ctx.reply("Génération du Modpack en cours : Démarrage...", mention_author=False)
        mods = self.load_from('mods')

        index = 0
        for project_slug in mods:
            url = f'https://api.modrinth.com/v2/project/{project_slug}/version'

            data = requests.get(url).json

            index += 1
            for latest_version in data():

                if latest_version["version_type"] == "release" and version in latest_version["game_versions"]:
                    download = latest_version['files'][0]['url']
                    file_name = latest_version['files'][0]['filename']

                    file = requests.get(download)
                    open(f'mods/{file_name}', 'wb').write(file.content)

                    await msg.edit(f"Génération du Modpack en cours : Téléchargement des mods ({index}/{len(mods)})")

                    break
            
            
        ModPack = ZipFile(f'modpack-oery-{version}.zip', 'w')

        index = 0
        for mod in os.listdir('mods'):
            index += 1
            ModPack.write(f'mods/{mod}')
            os.remove(f'mods/{mod}')

            if index % 20 == 0:
                await msg.edit(f"Génération du Modpack en cours : Compression des mods ({index}/{len(mods)})")

        await ctx.reply("Terminé !", mention_author=True, file=discord.File(f'modpack-oery-{version}.zip'))
        ModPack.close()


    @tasks.loop(hours=1)
    async def fetch_updates(self):
        await self.get_updates()


    @fetch_updates.before_loop
    async def before_fetch_updates(self):
        await self.client.wait_until_ready()


def setup(self):
    self.add_cog(Updater(self))

