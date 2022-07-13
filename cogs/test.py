import discord
from discord.ext import commands
from discord.ext.commands.core import Command

class Test(commands.Cog):

    def __init__(self, client):
        self.client = client
        client.loop.create_task(self.prepare_method())

    async def prepare_method(self):
        await self.client.wait_until_ready()

    @commands.command()
    async def test(self, ctx):
        await ctx.reply("Done !", mention_author=False)
        
def setup(client):
    client.add_cog(Test(client))