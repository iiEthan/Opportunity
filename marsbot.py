import json
import os
import asyncio
import asyncpg
import discord
import discord.ext
from discord.ext import commands

intents = discord.Intents(messages=True, guilds=True, reactions=True, voice_states=True)
bot = commands.AutoShardedBot(command_prefix = ",,", case_insensitive=True, help_command=None)
bot.first_startup = True

@bot.event
async def on_ready():
    if bot.first_startup:
        print("Bot connected to Discord")
        await bot.change_presence(activity=discord.Game(",,help"))
        await load_cogs()
        bot.first_startup = False

@bot.check
async def not_disabled(ctx):
    cantdisable = ["help", "invite", "disable", "enable"]
    if ctx.command.name in cantdisable:
        return True
    try:
        if ctx.command.name in bot.disabled_guilds[str(ctx.guild.id)]:
            return False
        return True
    except:
        return True

@bot.command()
async def invite(ctx):
    embed = discord.Embed(title="Interested in inviting me to your server?", description="[Invite link](https://discord.com/api/oauth2/authorize?client_id=386958619167424512&permissions=18432&scope=bot)", color=0x00ff4500)
    embed.set_footer(text="Make sure that I have permissions set up properly. I need to be able to read messages, send messages and embed links to function.", icon_url="https://cdn.discordapp.com/attachments/699740616241709146/699878588501196810/rsz_mars_4.png")
    await ctx.send(embed=embed)

@bot.command(hidden=True)
@commands.is_owner()
async def load(ctx, extension):
    bot.load_extension(f"cogs.{extension}")
    await ctx.send(f"Successfully loaded `{extension}`")

@bot.command(hidden=True)
@commands.is_owner()
async def unload(ctx, extension):
    bot.unload_extension(f"cogs.{extension}")
    await ctx.send(f"Successfully unloaded `{extension}`")

@bot.command(hidden=True)
@commands.is_owner()
async def reload(ctx, extension):
    bot.unload_extension(f"cogs.{extension}")
    bot.load_extension(f"cogs.{extension}")
    await ctx.send(f"Successfully reloaded `{extension}`")

async def load_cogs():
    bot.nword_db = await asyncpg.create_pool(database="postgres", user="postgres")
    bot.load_extension(f"cogs.database_handler")
    bot.load_extension("jishaku")
    await asyncio.sleep(2)
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py") and "database_handler" not in filename:
            try:
                bot.load_extension(f"cogs.{filename[:-3]}")
            except Exception as e:
                print(e)

    # Let's load some additional config here

    with open("disabled.json", "r") as jsonf:
        data = json.load(jsonf)
        bot.disabled_guilds = data

    with open("nwordblocked.json", "r") as jsonf:  # Load blocked guilds
        bot.blocked_guilds = []
        bot.blocked_guilds_ids = []
        blockdata = json.load(jsonf)
        for guild in blockdata["guilds"]:
            bot.blocked_guilds.append(guild)
            bot.blocked_guilds_ids.append(list(guild.keys())[0])

    with open("radiochannels.json", "r") as jsonf:
        bot.radiochannels = json.load(jsonf)

    async with bot.nword_db.acquire() as con:
        a = await con.fetch("SELECT user_id FROM postgres.nwords.message_optins WHERE optin = TRUE")
        bot.opted_in_users = [r["user_id"] for r in a]
        print(bot.opted_in_users)


with open("token.json") as bot_token: # file contains per-guild log channels
    data = json.load(bot_token)
    token = data["token"]

bot.run(token)
