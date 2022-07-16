import discord
import os
from dotenv import load_dotenv
from discord.ext import commands
from discord_components import *

load_dotenv('.env')
TOKEN = os.getenv('TOKEN')

intents = discord.Intents.default()
intents.members = True

client = commands.Bot(command_prefix = '&', owner_id = 301495911299940354, intents=intents)
DiscordComponents(client)
client.remove_command('help')

@client.command(pass_context=True)
@commands.is_owner()
async def mdmload(ctx, extension):
    client.load_extension(f'cogs.{extension}')
    await ctx.send(f"Loaded {extension}.py successfully")

@client.command(pass_context=True)
@commands.is_owner()
async def mdmunload(ctx, extension):
    client.unload_extension(f'cogs.{extension}')
    await ctx.send(f"Unloaded {extension}.py successfully")

@client.command(pass_context=True)
@commands.is_owner()
async def mdmreload(ctx, extension):
    client.unload_extension(f'cogs.{extension}')
    client.load_extension(f'cogs.{extension}')
    await ctx.send(f"Reloaded {extension}.py successfully")

for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        client.load_extension(f'cogs.{filename[:-3]}')

client.run(TOKEN)