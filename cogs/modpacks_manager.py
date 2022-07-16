from zipfile import ZipFile
import json
import requests
import os
import shutil

import discord
from discord.ext import commands

class ModPackManager(commands.Cog):

    def __init__(self, client):
        self.client = client
        client.loop.create_task(self.prepare_method())


    def write_in(self, file, data):
        with open(f"{file}.json", "w") as f:
            json.dump(data, f, indent=4)


    def load_from(self, file):
        with open(f"{file}.json", "r") as f:
            return json.load(f)


    async def prepare_method(self):
        await self.client.wait_until_ready()
        
        self.modpacks = self.load_from('modpacks')

    async def get_modpack(self, ctx, modpack):

        for user_id in self.modpacks:

            if modpack in list(self.modpacks[user_id].keys()):
                exist = True
                break
            
            if not exist:
                await ctx.reply('Ce ModPack n\'existe pas', mention_author=False)
                return None

        if str(ctx.author.id) != user_id:
            await ctx.reply('Ce ModPack ne vous appartient pas', mention_author=False)
            return None
                
        return self.modpacks[user_id][modpack]


    def is_compatible(self, mod, modloader, version):
        index = self.load_from('index')

        if mod not in index:
            index = self.index(mod)

        return any(version in index[mod][mod_version]['game_versions'] and modloader in index[mod][mod_version]['loaders'] for mod_version in index[mod])


    def index(self, slug):
        with open("index.json", "r") as f:
            index = json.load(f)
            index[slug] = {}

            url = f'https://api.modrinth.com/v2/project/{slug}/version'

            res = requests.get(url, timeout=10).json()
            supported_versions = []

            for version in res:
                download = False
                url = version['files'][0]['url']
                filename = version['files'][0]['filename']
                version_name = version['name']
                index[slug][version_name] = {
                    'game_versions': version['game_versions'],
                    'loaders': version['loaders'],
                    'filename': filename,
                    'url': url
                }

                for game_version in version['game_versions']:

                    if any(x in game_version for x in ['pre', 'w', 'rc']):
                        continue

                    if game_version not in supported_versions:
                        download = True

                    supported_versions.append(game_version)

                if not download:
                    continue

                file = requests.get(url)

                if not os.path.exists(f'mods/{slug}'):
                    os.makedirs(f'mods/{slug}')

                if not os.path.exists(f'mods/{slug}/{version_name}'):
                    os.makedirs(f'mods/{slug}/{version_name}')

                if filename not in os.listdir(f'mods/{slug}/{version_name}'):
                    open(f'mods/{slug}/{version_name}/{filename}', 'wb').write(file.content)

                self.write_in('index', index)
                
            return index
        

    @commands.command(aliases=['mp'])
    async def modpack(self, ctx, *args):

        if len(args) == 0:
            return await ctx.reply('Arguments possibles : create, download, info, me, mods, delete', mention_author=False)
        
        if len(args) == 1 and args[0] not in ['me', 'create']:
            return await ctx.reply('Vous devez préciser un nom de ModPack.', mention_author=False)

        if args[0] == 'create':
            
            if len(args) != 4:
                return await ctx.reply('Exemple : &modpack create NomDuModPack fabric 1.19', mention_author=False)

            if args[2].lower() not in ['fabric', 'forge', 'quilt']:
                return await ctx.reply('Modloader Invalide : Fabric, Forge, Quilt', mention_author=False)

            for user_id in self.modpacks:
                if args[1] in list(self.modpacks[user_id].keys()):
                    return await ctx.reply('Ce nom est déjà pris par un autre ModPack.', mention_author=False) 

            if str(ctx.author.id) not in self.modpacks:
                self.modpacks[str(ctx.author.id)] = {}

            self.modpacks[str(ctx.author.id)][args[1]] = {
                'version': args[3],
                'modloader': args[2].lower(),
                'mods': [],
            }

            self.write_in('modpacks', self.modpacks)

            loader = args[2].capitalize()
            version = args[3]

            return await ctx.reply(f'ModPack crée !\nNom : {args[1]}\nCréateur : {ctx.author}\nLoader : {loader}\nVersion : {version}\nPour obtenir la liste des mods. Utilisez la commande &modpack mods.', mention_author=False)

        elif args[0] == 'info':
            
            exist = False

            for user_id in self.modpacks:
                if args[1] in list(self.modpacks[user_id].keys()):
                    exist = True
                    break
            
            if not exist:
                return await ctx.reply('Ce ModPack n\'existe pas', mention_author=False)

            modpack = self.modpacks[user_id][args[1]]
            
            if ctx.guild.get_member(int(user_id)) != None:
                user_id = ctx.guild.get_member(int(user_id))

            loader = modpack['modloader'].capitalize()
            version = modpack['version']
            
            return await ctx.reply(f'Nom : {args[1]}\nCréateur : {user_id}\nLoader : {loader}\nVersion : {version}\nPour obtenir la liste des mods. Utilisez la commande &modpack mods.', mention_author=False)
    
        elif args[0] == 'delete':
            
            exist = False

            for user_id in self.modpacks:
                    if args[1] in list(self.modpacks[user_id].keys()):
                        exist = True
                        break
            
            if not exist:
                return await ctx.reply('Ce ModPack n\'existe pas', mention_author=False)

            if str(ctx.author.id) != user_id:
                return await ctx.reply('Ce ModPack ne vous appartient pas', mention_author=False)

            del self.modpacks[user_id][args[1]]

            self.write_in('modpacks', self.modpacks)

            return await ctx.reply('ModPack supprimé', mention_author=False)

        elif args[0] == 'me':
            
            if str(ctx.author.id) not in self.modpacks:
                return await ctx.reply('Vous n\'avez pas encore crée de ModPack.\nCréez en un avec la commande &modpack create', mention_author=False)

            message = 'Liste de vos ModPacks :'
            for modpack in self.modpacks[str(ctx.author.id)]:
                message += f'\n{modpack}'

            return await ctx.reply(message, mention_author=False)

        elif args[0] == 'download':
            modpack = await self.get_modpack(ctx, args[1])

            index = self.load_from('index')

            if not os.path.exists(f'mods/modpacks/{args[1]}'):
                os.makedirs(f'mods/modpacks/{args[1]}')

            for slug in modpack['mods']:

                if not slug in index:
                    index = self.index(slug)
                else:
                    exist = False

                    for mod_version in index[slug]:
                        if modpack['version'] in index[slug][mod_version]['game_versions'] and modpack['modloader'] in index[slug][mod_version]['loaders']:
                            exist = True

                    if exist == False:
                         index = self.index(slug)

                for mod_version in index[slug]:
                    
                    if modpack['version'] in index[slug][mod_version]['game_versions'] and modpack['modloader'] in index[slug][mod_version]['loaders']:
                        filename = index[slug][mod_version]['filename']

                        if not os.path.exists(f'mods/{slug}/{mod_version}'):
                            os.makedirs(f'mods/{slug}/{mod_version}')

                        if not index[slug][mod_version]['filename'] in os.listdir(f'mods/{slug}/{mod_version}'):
                            file = requests.get(index[slug][mod_version]['url'])
                            open(f'mods/{slug}/{mod_version}/{filename}', 'wb').write(file.content)

                        shutil.copyfile(f'mods/{slug}/{mod_version}/{filename}', f'mods/modpacks/{args[1]}/{filename}')
                        break
            
            version = modpack['version']
            modloader = modpack['modloader']

            ModPack = ZipFile(f'mods/modpacks/{args[1]}-{modloader}-{version}.zip', 'w')                                        
            
            for mod in os.listdir(f'mods/modpacks/{args[1]}/'):
                ModPack.write(f'mods/modpacks/{args[1]}/{mod}', arcname=mod)
                os.remove(f'mods/modpacks/{args[1]}/{mod}')
            ModPack.close()

            try:
                await ctx.reply("Terminé !", mention_author=True, file=discord.File(f'mods/modpacks/{args[1]}-{modloader}-{version}.zip'))
                
            except:
                await ctx.reply("Le fichier est trop large.", mention_author=True)

            return

        elif args[0] == 'update':
            return await ctx.reply('Cette fonctionnalité n\'est pas encore disponible.', mention_author=False)

        elif args[0] == 'mods':
            
            for user_id in self.modpacks:
                if args[1] in list(self.modpacks[user_id].keys()):
                    exist = True
                    break
            
            if not exist:
                return await ctx.reply('Ce ModPack n\'existe pas', mention_author=False)

            modpack = self.modpacks[user_id][args[1]]
            message = ''

            for slug in modpack['mods']:
                mod = requests.get(f'https://api.modrinth.com/v2/project/{slug}').json()
                title = mod['title'] + ', '

                if len(message) + len(title) < 2000:
                    message += title

                else:
                    await ctx.send(message)
                    message = title

                if slug == modpack['mods'][-1]:
                    await ctx.send(message)

        elif args[0] == 'add':
            modpack = await self.get_modpack(ctx, args[1])
            mods = self.load_from('mods')
            index = self.load_from('index')

            if modpack is None:
                return

            if len(args) <= 2:
                return await ctx.reply('Veuillez spécifier les mods à ajouter.', mention_author=False)
            
            for slug in args:

                if slug in [args[0], args[1]]:
                    continue
                
                if slug in modpack['mods']:
                    await ctx.reply(f"Le mod {title} est déjà dans le ModPack.", mention_author=False)
                    continue

                res = requests.get(f'https://api.modrinth.com/v2/project/{slug}')
            
                if res.status_code != 200:
                    await ctx.reply(f"Le mod {slug} n'a pas été trouvé.", mention_author=False)
                    continue

                title = res.json()["title"]

                if slug not in mods:
                    mods.append(slug)
                    self.write_in('mods', mods)

                if slug not in index:
                    self.index(slug)

                if not self.is_compatible(slug, modpack['modloader'], modpack['version']):
                    await ctx.reply(f"Le mod {title} n'est pas compatible mais a été ajouté au ModPack au cas où une version compatible verrait le jour.", mention_author=False)

                else:
                    await ctx.reply(f"Le mod {title} a été ajouté au ModPack.", mention_author=False)

                self.modpacks[str(ctx.author.id)][args[1]]['mods'].append(slug)
                
            self.write_in('modpacks', self.modpacks)

        elif args[0] == 'remove':
            modpack = await self.get_modpack(ctx, args[1])

            if modpack is None:
                return

            if len(args) <= 2:
                return await ctx.reply('Veuillez spécifier les mods à retirer.', mention_author=False)
                
            for slug in args:
                
                if slug in [args[0], args[1]]:
                    continue
                
                if slug not in modpack['mods']:
                    modpack['mods'].remove(slug)
                    await ctx.reply(f"Le mod n'est pas dans le ModPack.", mention_author=False)
                    continue
                
                modpack['mods'].remove(slug)
                await ctx.reply(f"Le mod {slug} a été retiré du ModPack.", mention_author=False)

            self.write_in('modpacks', self.modpacks)

def setup(client):
    client.add_cog(ModPackManager(client))