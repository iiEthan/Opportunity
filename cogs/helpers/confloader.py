import json
import discord
from discord.ext import commands

async def not_disabled(ctx):
    with open("disabled.json", "r") as jsonf:
        data = json.load(jsonf)
    try:
        if ctx.command.name in data[str(ctx.guild.id)]:
            return True
    except:
        return False
