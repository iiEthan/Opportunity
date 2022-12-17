import asyncio
import asyncpg
import json
import typing
from datetime import datetime

import discord
from discord.ext import commands, tasks

class DevCommands(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.group()
    @commands.is_owner()
    async def dev(self, ctx):

        clist = []
        if ctx.invoked_subcommand is None:
            for command in ctx.command.cog.walk_commands():
                if isinstance(command, commands.Group):
                    for com in command.commands:
                        clist.append(com.name)

            return await ctx.send(f"Developer commands available: `{clist}`")

    @dev.command()
    @commands.is_owner()
    async def message(self, ctx, user: discord.User, *, what):

        embed = discord.Embed(title=" ", description=what, timestamp=datetime.utcnow(), color=16747520)
        embed.set_author(icon_url=ctx.author.avatar_url, name=str(ctx.author) + " [Opportunity developer]")
        embed.add_field(name="Messages sent in response are not read.", value=f"If you have more questions, join the [support server](https://discord.gg/KxFWHW9) and send a DM to {str(ctx.author)}", )
        embed.set_footer(text="Responses to this message will not be received.")

        await user.send(embed=embed)
        channel = self.bot.get_channel(699954979901014016)
        await channel.send(content=f"{str(ctx.author)} sent a message to {user}", embed=embed)

    @dev.command()
    @commands.is_owner()
    async def purgeguild(self, ctx, guild):
        async with self.bot.nword_db.acquire() as con:
            async with con.transaction():
                await con.execute(f'DELETE FROM postgres.nwords.nwords WHERE guild_id = {int(guild)}')

        guild = self.bot.get_guild(int(guild))

        await ctx.send(f"Purged guild `{guild.name}` (`{guild.id}`) from database. ")


    async def get_nwords(self, type, id):
        async with self.bot.nword_db.acquire() as con:
            soft_rs = await con.fetch(
                f'SELECT COALESCE (SUM(softs),0) AS total FROM postgres.nwords.nwords WHERE {type} = {int(id)}')
            hard_rs = await con.fetch(
                f'SELECT COALESCE (SUM(hards),0) AS total FROM postgres.nwords.nwords WHERE {type} = {int(id)}')
            return soft_rs, hard_rs

    @dev.command()
    @commands.is_owner()
    async def nwordcount(self, ctx, type, id):

        valid_types = ["author_id", "guild_id", "channel_id"]
        if type not in valid_types:
            return await ctx.send(f"Invalid type. Supported types are `{valid_types}`")

        soft_rs, hard_rs = await self.get_nwords(type, id)

        await ctx.send(f"{type} {id} has {soft_rs[0]['total'] + hard_rs[0]['total']} n-words in total, out of which {soft_rs[0]['total']} are soft-ns and {hard_rs[0]['total']} are hards.")
        return

    @dev.command()
    @commands.is_owner()
    async def nword_blockguild(self, ctx, guild, *, reason):
        with open("nwordblocked.json", "r+") as file:
            lis = []
            dis = json.load(file)
            try:
                try:
                    for i in dis["guilds"]:
                        lis.append(i)
                    lis.append({guild: reason})
                except AttributeError:
                    lis.append({guild: reason})
            except KeyError:
                lis.append({guild: reason})
        dis.update({"guilds": lis})
        with open("nwordblocked.json", "w+") as file:
            json.dump(dis, file)
        self.bot.blocked_guilds = lis
        self.bot.blocked_guilds_ids.append(str(ctx.guild.id))
        return

    @dev.command()
    @commands.is_owner()
    async def nword_unblockguild(self, ctx, guild):
        with open("nwordblocked.json", "r+") as file:
            lis = []
            dis = json.load(file)
            reason = "This guild has been blacklisted automatically due to detected abuse.\n\nTo appeal this " \
                     "action, please contact a developer on our support server: discord.gg/KxFWHW9"

            for i in dis["guilds"]:
                lis.append(i)
            lis.remove({guild: reason})

        dis.update({"guilds": lis})
        with open("nwordblocked.json", "w+") as file:
            json.dump(dis, file)
        self.bot.blocked_guilds = lis
        self.bot.blocked_guilds_ids.append(str(guild))
        return

    @dev.command()
    @commands.is_owner()
    async def guildinfo(self, ctx, guild = None):
        if guild is None:
            return await ctx.send("Please provide an id")
        try:
            int(guild)
        except:
            return await ctx.send("Please provide a proper id")
        soft_rs, hard_rs = await self.get_nwords(type="guild_id", id=guild)
        guild = self.bot.get_guild(int(guild))

        embed = discord.Embed(title=f"Guild:",
                              description=f"**Name**: {guild.name}\n"
                                          f"**ID**: {guild.id}\n"
                                          f"**Owner ID**: {str(guild.owner_id)}\n"
                                          f"**Created at**: {guild.created_at}\n"
                                          f"**Member count**: {guild.member_count}\n"
                                          f"**N-words**: {soft_rs[0]['total'] + hard_rs[0]['total']}",
                              timestamp=datetime.utcnow(),
                              colour=16747520)
        embed.set_thumbnail(url=guild.icon_url)
        embed.set_footer(text="", icon_url=guild.icon_url)

        return await ctx.send(embed=embed)

    @dev.command()
    @commands.is_owner()
    async def addchannel(self, ctx, name, link, description):
        self.bot.radiochannels[name] = {link: description}
        with open("radiochannels.json", "w+") as file:
            json.dump(self.bot.radiochannels, file)
        await ctx.send("Channel added")

    @dev.command()
    @commands.is_owner()
    async def clear_old_messages(self, ctx, sf: int):


        async with self.bot.nword_db.acquire() as con:
            async with con.transaction():
                msgs = await con.execute(
                    "DELETE from postgres.nwords.messages WHERE (message_id <= $1)",
                    sf
                )

        await ctx.send(f"Successfully cleared out `{msgs}` old messages.")


def setup(bot):
    bot.add_cog(DevCommands(bot))
