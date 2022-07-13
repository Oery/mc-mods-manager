import discord
from discord.ext import commands

class MainCog(commands.Cog):

    def __init__(self, client):
        self.client = client
        client.loop.create_task(self.prepare_method())

    async def prepare_method(self):
        await self.client.wait_until_ready()
        await self.client.change_presence(status=discord.Status.online, activity=discord.Activity(type=discord.ActivityType.watching, name="Modrinth à la recherche de mises à jour..."))
        print('Bot is online.')
        
def setup(client):
    client.add_cog(MainCog(client))