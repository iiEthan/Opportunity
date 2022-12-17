import asyncio
import asyncpg
import json
import typing

import discord
from discord.ext import commands, tasks



class RacialSlurCounting(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.blocked_guilds = []
        self.blocked_guilds_ids = []
        self.monitored_guilds = {}
        self.add_to_db = []
        self.update_nwordcount.start()
        self.anti_abuse_monitor.start()

    # == misc functions ==

    @commands.command()
    @commands.is_owner()
    async def createdatabase(self, ctx):
        async with self.bot.nword_db.acquire() as con:
            async with con.transaction():
                await con.execute(f'INSERT INTO postgres.nwords.nwords VALUES (0, {ctx.author.id}, {ctx.guild.id}, {ctx.channel.id}, 0, 0)')
        totalcount = 0
        timesran = 1
        startmsg = await ctx.send("Initializing n-word database creation: crawling through old messages and counting their n-words. This is a slow operation. Your results will be incomplete until this is done.")
        for channel in ctx.guild.channels:
            if channel.type == discord.ChannelType.text:
                if channel.permissions_for(ctx.guild.me).read_messages and channel.permissions_for(ctx.guild.me).read_message_history:
                    achannel = self.bot.get_channel(channel.id)
                    async for message in achannel.history(limit=None): # we want every single message.
                        await asyncio.sleep(0.01)
                        totalcount += 1

                        if "nigger" in message.content.lower() or "nigga" in message.content.lower():
                            soft_amount = message.content.lower().count("nigga")
                            hard_amount = message.content.lower().count("nigger")

                            async with self.bot.nword_db.acquire() as con:
                                async with con.transaction():
                                    await con.execute(
                                        f'INSERT INTO postgres.nwords.nwords VALUES (\'{message.id}\', \'{message.author.id}\', \'{message.guild.id}\', \'{message.channel.id}\', {soft_amount}, {hard_amount})')


        await ctx.send(f"N-word database creation complete, messages scanned in total: {totalcount}. You can now use `,,nwordcount` to get full results.")

    async def create_nword_leaderboard(self, ctx):
        embed = discord.Embed(title=f"N-word leaderboard for {ctx.guild}", description="*Note: Opportunity does not encourage the usage of the n-word in any way.*")

        async with self.bot.nword_db.acquire() as con:
            async with con.transaction():
                top_softs = await con.fetch(
                    f'SELECT author_id, COALESCE (SUM(softs),0) AS total FROM postgres.nwords.nwords WHERE guild_id = {ctx.guild.id} GROUP BY author_id ORDER BY total DESC LIMIT 10'
                )
                top_hards = await con.fetch(
                    f'SELECT author_id, COALESCE (SUM(hards),0) AS total FROM postgres.nwords.nwords WHERE guild_id = {ctx.guild.id} GROUP BY author_id ORDER BY total DESC LIMIT 10'
                )
        n = 0
        softns = []

        for i in top_softs:
            softns.append(f"<@{i[0]}>: {i[1]}")
            n += 1
            if n == 10:
                break

        if not len(softns) == 0:
            embed.add_field(name="Soft n-word leaderboard:", value="\n".join(softns))
        else:
            embed.add_field(name="Soft n-word leaderboard:", value="I haven't seen anyone say the soft n-word.")

        n = 0
        hardns = []

        for i in top_hards:
            hardns.append(f"<@{i[0]}>: {i[1]}")
            n += 1
            if n == 10:
                break

        if not len(hardns) == 0:
            embed.add_field(name="Hard n-word leaderboard:", value="\n".join(hardns))
        else:
            embed.add_field(name="Hard n-word leaderboard:", value="I haven't seen anyone say the hard n-word.")

        return embed

    async def get_nwords(self, ctx, object, object_type):
        async with self.bot.nword_db.acquire() as con:
            results = await con.fetch(f'SELECT * from postgres.nwords.nwords WHERE guild_id = {ctx.guild.id} LIMIT 1')

        if not len(results) == 0:
            if object_type == "member":
                async with self.bot.nword_db.acquire() as con:
                    results_s = await con.fetchrow(
                        f'SELECT COALESCE (SUM(softs),0) AS total FROM postgres.nwords.nwords WHERE author_id = {object.id} AND guild_id = {ctx.guild.id}')
                    results_h = await con.fetchrow(
                        f'SELECT COALESCE (SUM(hards),0) AS total FROM postgres.nwords.nwords WHERE author_id = {object.id} AND guild_id = {ctx.guild.id}')

            if object_type == "user":
                async with self.bot.nword_db.acquire() as con:
                    results_s = await con.fetchrow(
                        f'SELECT COALESCE (SUM(softs),0) AS total FROM postgres.nwords.nwords WHERE author_id = {object} AND guild_id = {ctx.guild.id}')
                    results_h = await con.fetchrow(
                        f'SELECT COALESCE (SUM(hards),0) AS total FROM postgres.nwords.nwords WHERE author_id = {object} AND guild_id = {ctx.guild.id}')

            elif object_type == "channel":
                async with self.bot.nword_db.acquire() as con:
                    results_s = await con.fetchrow(
                        f'SELECT COALESCE (SUM(softs),0) AS total FROM postgres.nwords.nwords WHERE channel_id = {ctx.channel.id}')
                    results_h = await con.fetchrow(
                        f'SELECT COALESCE (SUM(hards),0) AS total FROM postgres.nwords.nwords WHERE channel_id = {ctx.channel.id}')

            elif object_type == "guild":
                async with self.bot.nword_db.acquire() as con:
                    results_s = await con.fetchrow(
                        f'SELECT COALESCE (SUM(softs),0) AS total FROM postgres.nwords.nwords WHERE guild_id = {ctx.guild.id}')
                    results_h = await con.fetchrow(
                        f'SELECT COALESCE (SUM(hards),0) AS total FROM postgres.nwords.nwords WHERE guild_id = {ctx.guild.id}')

            elif object_type == "leaderboard":
                return "leaderboard"

        else:
            await self.createdatabase(ctx)
            return False
        return results_s["total"], results_h["total"]

    async def send_embed(self, ctx, object, object_type, softcount, hardcount):
        if object_type == "user":
            embed = discord.Embed(title=f"{object}'s n-words:", description="*Note: Opportunity does not encourage the usage of the n-word in any way.*")
        else:
            embed = discord.Embed(title=f"{str(object)}'s n-words:", description="*Note: Opportunity does not encourage the usage of the n-word in any way.*")
        embed.add_field(name="Soft n-words found:", value=softcount)
        embed.add_field(name="Hard n-words found:", value=hardcount)
        embed.set_footer(text="Usage: ,,nwordcount [@mention/leaderboard]")
        if object_type == "user":
            await ctx.send(f"Thanks for the request, comrade. I've looked through their messages for n-words.", embed=embed)
        elif object_type == "channel":
            await ctx.send(f"Thanks for the request, comrade. I've looked through <#{object.id}>'s messages for n-words.", embed=embed)
        else:
            await ctx.send(f"Thanks for the request, comrade. I've looked through the user's messages for n-words.", embed=embed)

    # == nwordcount ==

    @commands.command()
    async def nwordcount(self, ctx, object: typing.Union[discord.Member, discord.TextChannel, discord.Guild, str, None]): #discord.guild.Guild, str, None]):

        if str(ctx.guild.id) in self.blocked_guilds_ids:
            for guild in self.blocked_guilds:
                if guild.get(str(ctx.guild.id)):
                    reason = guild.get(str(ctx.guild.id))
                    break
                else:
                    reason = "No reason provided"
            
            embed = discord.Embed(title="Command blocked", description=reason)
            await ctx.send(embed=embed)
            return

        if isinstance(object, discord.Member): # note to self: isinstance works, obj is x doesn't.
            object_type = "member"

        elif isinstance(object, discord.Guild):
            object_type = "guild"

        elif isinstance(object, discord.TextChannel):
            object_type = "channel"

        elif isinstance(object, str):

            guild_aliases = [str(ctx.guild.id), ctx.guild.name, "server", "guild"]

            if object.lower() in [a.lower() for a in guild_aliases]: # case-insensitive
                object_type = "guild"
                object = ctx.guild

            elif object in "leaderboard":
                object_type = "leaderboard"

            else:
                try:
                    if "#" in str(object):
                        int("givemeafuckingvalueerror")
                    object = int(''.join(c for c in str(object) if c.isdigit())) # get the id, in case it's a mention
                    object_type = "user"

                except ValueError:
                    embed = discord.Embed(title=f"Invalid argument:", description=f"`{object}` is not a valid member, channel or a guild.\nUsage: ',,nwordcount [{ctx.author.mention} / {ctx.channel.mention} / {ctx.guild} / leaderboard]'")
                    await ctx.send(embed=embed)
                    return
        else:
            object_type = "member"
            object = ctx.author

        nwords = await self.get_nwords(ctx, object, object_type)
        if nwords is False:
            return
        if nwords == "leaderboard":
            leaderboard = await self.create_nword_leaderboard(ctx)
            await ctx.send(embed=leaderboard)
            return
        softcount = nwords[0]
        hardcount = nwords[1]

        await self.send_embed(ctx, object, object_type, softcount, hardcount)
        return

    # == listeners & loops ==

    @commands.Cog.listener()
    async def on_message(self, message):

        if message.guild.id in self.blocked_guilds_ids:
            return

        # I moved this up here so that it counts hard r first in order to be consistent with the init,
        # but this can be changed later
        if "nigger" in message.content.lower() or "nigga" in message.content.lower():
            soft_amount = message.content.lower().count("nigga")
            hard_amount = message.content.lower().count("nigger")

            async with self.bot.nword_db.acquire() as con:
                async with con.transaction():
                    await con.execute(f'INSERT INTO postgres.nwords.nwords VALUES (\'{message.id}\', \'{message.author.id}\', \'{message.guild.id}\', \'{message.channel.id}\', {soft_amount}, {hard_amount})')

            try:
                self.monitored_guilds[str(message.guild.id)] += 1
            except KeyError:
                self.monitored_guilds[str(message.guild.id)] = 1


    @tasks.loop(minutes=30)
    async def anti_abuse_monitor(self):
        for guild, number in self.monitored_guilds.items():
            if number > 1500:
                reason = "This guild has been blacklisted automatically due to detected abuse.\n\nTo appeal this " \
                         "action, please contact a developer on our support server: discord.gg/KxFWHW9"
                await self.blockguild(ctx=self.bot.get_guild(guild), guild=int(guild), reason=reason)
        self.monitored_guilds = {}

    @tasks.loop(hours=1)
    async def update_nwordcount(self):
        async with self.bot.nword_db.acquire() as con:
            soft_nwords = await con.fetchrow(f'SELECT COALESCE (SUM(softs),0) AS total FROM postgres.nwords.nwords')
            hard_nwords = await con.fetchrow(f'SELECT COALESCE (SUM(hards),0) AS total FROM postgres.nwords.nwords')
            self.bot.total_nwords = soft_nwords["total"] + hard_nwords["total"]


    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload):
        async with self.bot.nword_db.acquire() as con:
            async with con.transaction():
                await con.execute(f'DELETE FROM postgres.nwords.nwords WHERE message_id = {payload.message_id}')

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        async with self.bot.nword_db.acquire() as con:
            async with con.transaction():
                await con.execute(f'DELETE FROM postgres.nwords.nwords WHERE channel_id = {channel.id}')

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        async with self.bot.nword_db.acquire() as con:
            async with con.transaction():
                await con.execute(f'DELETE FROM postgres.nwords.nwords WHERE guild_id = {guild.id}')


def setup(bot):
    bot.add_cog(RacialSlurCounting(bot))
