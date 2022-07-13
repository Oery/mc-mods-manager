import discord
from discord.ext import commands
from discord.ext.commands.core import Command

class Bienvenue(commands.Cog):

    def __init__(self, client):
        self.client = client
        client.loop.create_task(self.prepare_method())

    async def prepare_method(self):
        await self.client.wait_until_ready()

    @commands.Cog.listener()
    async def on_member_join(self, member):
        bienvenue = self.client.get_channel(916304519455981589)
        await bienvenue.send(f"{member.mention} a rejoint le serveur !")
        
def setup(client):
    client.add_cog(Bienvenue(client))
