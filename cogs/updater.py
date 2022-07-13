from turtle import update
from webbrowser import get
import discord
import json
import requests
from discord.ext import commands
from discord.ext.commands.core import Command

class Updater(commands.Cog):

    def __init__(self, client):
        self.client = client
        client.loop.create_task(self.prepare_method())

    def write_in(self, file, data):
        with open(f"{file}.json", "w") as f:
            json.dump(data, f)

    def load_from(self, file):
        with open(f"{file}.json", "r") as f:
            return json.load(f)

    async def get_updates(self, ctx):

        mods = self.load_from('mods')
        update = False

        for project_slug in mods:
            url = f'https://api.modrinth.com/v2/project/{project_slug}/version'

            data = requests.get(url).json

            for latest_version in data():
                
                latest_versions = self.load_from('latest_versions')

                if latest_version in latest_versions:
                    break

                if latest_version["version_type"] == "release":
                    title = latest_version["name"]
                    changelog = latest_version["changelog"]
                    download = latest_version['files'][0]['url']
                    game_version = latest_version["game_versions"]
                    loaders = latest_version["loaders"]

                    update = True
                    await ctx.send(f"{title} a reçu une mise à jour !")
                    # await ctx.send(changelog)
                    # await ctx.send(download)
                    # await ctx.send(loaders, game_version)

                    latest_versions.append(latest_version)
                    self.write_in('latest_versions', latest_versions)

                    break
        
        if not update:
            await ctx.send("Aucun mod n'a reçu de mise à jour !")

    async def prepare_method(self):
        await self.client.wait_until_ready()

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
    

    @commands.is_owner()
    @commands.command()
    async def listmod(self, ctx):
        mods = self.load_from('mods')
        msg = "```"

        for mod in mods:
            msg += f"{mod}   "
        msg += "```"

        await ctx.reply(msg, mention_author=False)

        
def setup(self):
    self.add_cog(Updater(self))