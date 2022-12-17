import asyncio
import json
import time
import gc
import re
from datetime import datetime
import typing

import discord
import markovify
from discord.ext import commands, tasks


class MarkovChain(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.imitated_users = []
        self.bot.dbentry_list = []
        self.allowed_characters = "[^a-zA-Z0-9,. !?:/_|@*'\"¤%#&()=<>-]+"

    async def not_disabled(self, ctx):
        try:
            if ctx.command.name in self.bot.disabled_guilds[str(ctx.guild.id)]:
                return False
            return True
        except:
            return True

    async def safe_insert(self, author_id, message_id, channel_id, guild_id, message_content):

        async with self.bot.nword_db.acquire() as con:
            async with con.transaction():
                await con.execute(
                    "INSERT INTO postgres.nwords.messages VALUES ($1, $2, $3, $4, $5)", *(author_id, message_id,
                                                                                          channel_id, guild_id,
                                                                                          message_content)
                )

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.id not in self.bot.opted_in_users:
            return
        if message.author.bot:  # Ignores bots
            return

        bot_prefixes = (",,", "!", "/", "?")
        if message.content.startswith(bot_prefixes):
            return

        await self.safe_insert(author_id=message.author.id, message_id=message.id, channel_id=message.channel.id,
                               guild_id=message.guild.id, message_content=message.content[0:1000])

    @commands.command()
    @commands.cooldown(1.0, 10.0, commands.BucketType.user)
    async def optin(self, ctx):
        if ctx.author.id not in self.bot.opted_in_users:
            self.bot.opted_in_users.append(ctx.author.id)
            async with self.bot.nword_db.acquire() as con:
                async with con.transaction():
                    vals = (ctx.author.id, True)
                    await con.execute(
                        "INSERT INTO postgres.nwords.message_optins VALUES ($1, $2)", *vals
                    )
            await ctx.send("Successfully opted in! Opt out at any time using `,,optout`.")
        else:
            await ctx.send(content="You are already opted in! You can opt out using `,,optout`.", delete_after=5.0)

    @optin.error
    async def optin_error(self, ctx, error):
        await ctx.send(
            content=f"{ctx.author.mention}, you are on cooldown (10 s in between commands). Retry-after: {round(error.retry_after, 3)} s",
            delete_after=5.0)
        ctx.handled_in_local = True

    async def fetch_messages(self, author_id=None, channel_id=None, guild_id=None):

        qstr = ", "
        author = f"author_id = {author_id}," if author_id else ""
        channel = f"channel_id = {channel_id}," if channel_id else ""
        guild = f"guild_id = {guild_id}" if guild_id else ""
        queries = (author, channel, guild)

        if author_id:
            async with self.bot.nword_db.acquire() as con:
                msgs = await con.fetch(
                    "SELECT message_content FROM postgres.nwords.messages WHERE (author_id = $1 AND guild_id = $2)",
                    *(author_id, guild_id)
                )
        elif channel_id:
            async with self.bot.nword_db.acquire() as con:
                msgs = await con.fetch(
                    "SELECT message_content FROM postgres.nwords.messages WHERE (channel_id = $1 AND guild_id = $2)",
                    *(channel_id, guild_id)
                )
        elif guild_id and not channel_id:
            async with self.bot.nword_db.acquire() as con:
                msgs = await con.fetch(
                    "SELECT message_content FROM postgres.nwords.messages WHERE (guild_id = $1)",
                    guild_id
                )
        return [r["message_content"] for r in msgs]


    @commands.command()
    @commands.cooldown(1, 3600.0, commands.BucketType.user)
    async def optout(self, ctx):
        if ctx.author.id in self.bot.opted_in_users:

            msg = await ctx.send("Are you sure you want to opt out? Your messages will be deleted from the database "
                                 "permanently, which cannot be reversed. Write `CONFIRM` (cAsE-sEnsItive) to confirm.")

            def check(m):
                return m.content == "CONFIRM" and m.author.id == ctx.author.id

            await self.bot.wait_for('message', check=check)

            self.bot.opted_in_users.remove(ctx.author.id)
            async with self.bot.nword_db.acquire() as con:
                async with con.transaction():
                    vals = ctx.author.id
                    await con.execute(
                        "DELETE FROM postgres.nwords.message_optins WHERE user_id = $1", vals
                    )
            await msg.edit(
                content="Successfully opted out from `,,imitate`. You can opt in at any time using `,,optin`")
        else:
            await ctx.send(content="You have not opted in yet. You can opt in using `,,optin`", delete_after=5.0)

    @optout.error
    async def optout_error(self, ctx, error):
        await ctx.send(
            content=f"{ctx.author.mention}, you are on cooldown (3600 s in between commands). Retry-after: {round(error.retry_after, 3)} s",
            delete_after=5.0)
        ctx.handled_in_local = True

    @commands.command(pass_context=True)
    @commands.cooldown(1.0, 3.0, commands.BucketType.user)
    async def imitate(self, ctx, *, user: typing.Union[discord.Member, discord.TextChannel, discord.Guild, str, None]):

        if user is None:
            user = ctx.message.author
            objtype = "user"

        elif isinstance(user, discord.Member):
            objtype = "user"

        elif isinstance(user, discord.TextChannel):
            if not user.permissions_for(ctx.author).read_messages and not user.permissions_for(
                    ctx.author).read_message_history:
                await ctx.send(content="You can't see this channel, so you also can't imitate it.")
                return
            if not user.permissions_for(ctx.guild.me).read_messages and not user.permissions_for(
                    ctx.guild.me).read_message_history:
                await ctx.send(content="I can't see this channel, so I can't imitate it.")
                return
            objtype = "channel"

        elif isinstance(user, discord.Guild):
            objtype = "guild"

        elif isinstance(user, str):
            guild_aliases = [str(ctx.guild.id), ctx.guild.name, "server", "guild"]

            if user.lower() in [a.lower() for a in guild_aliases]:  # case-insensitive
                objtype = "guild"
                user = ctx.guild
            else:
                await asyncio.sleep(1)
                await ctx.send(content="I could not find that member. Use mentions or 'server' for server")
                return


        else:
            await ctx.send(content="I could not find that member. Use mentions or 'server' for server")
            return

        if user.id not in self.bot.opted_in_users and objtype == "user":

            markov_title = "Unable to form a message"
            if user == ctx.message.author:
                markov_message = "You have not opted in to use this command. Use `,,optin` to give me permission to listen to your messages. They will be stored for 30 days and used with this command only."
            else:
                markov_message = "This user has not opted in to use this command. They must use `,,optin` to give me permission to listen to their messages. They will be stored for 30 days and used with this command only."
            embed = discord.Embed(title=markov_title, description=markov_message,
                                  color=16747520)
            embed.set_footer(text=f"Requested by {str(ctx.author)}")
            embed.set_author(icon_url=user.avatar.url, name=user.name + "#" + user.discriminator)
            await ctx.send(embed=embed)
            return


        messages = []

        if objtype == "user":
            msgs = await self.fetch_messages(author_id=user.id, guild_id=ctx.guild.id)
            messages.append(msgs)
        elif objtype == "channel":
            msgs = await self.fetch_messages(channel_id=user.id, guild_id=ctx.guild.id)
            messages.append(msgs)
        elif objtype == "guild":
            msgs = await self.fetch_messages(guild_id=ctx.guild.id)
            messages.append(msgs)
        else:
            msgs = []

        try:
            text_model = markovify.NewlineText('\n'.join(msgs)).make_sentence(tries=100)  # Build the model
            if text_model is not None:
                markov_message = text_model[0:1020]
                # Limit 1500 characters to a message and try 50 times to decrease failure likelihood
                markov_title = " "
            else:
                markov_title = "Unable to form a sentence"
                markov_message = "This may be due to a low message count, you have not been messaging much recently, or the bot was unable to make a sentence that does not overlap too much."

        except KeyError:  # Sometimes an imitation can fail for a variety of reasons listed below
            markov_title = "Unable to form a sentence"
            markov_message = "This may be due to a low message count, you have not been messaging much recently, or the bot was unable to make a sentence that does not overlap too much."
        embed = discord.Embed(title=markov_title, description=markov_message, color=16747520)
        embed.set_footer(text=f"Requested by {str(ctx.author)}")

        if objtype == "user":
            embed.set_author(icon_url=user.avatar.url, name=str(user))

        elif objtype == "channel":
            embed.set_author(icon_url=ctx.guild.icon.url, name=str(user))

        elif objtype == "guild":
            embed.set_author(icon_url=ctx.guild.icon.url, name=ctx.guild.name)

        await ctx.send(embed=embed)

    @imitate.error
    async def imitate_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(
                content=f"{ctx.author.mention}, you are on cooldown (3 s in between commands). Retry-after: {round(error.retry_after, 3)} s",
                delete_after=5.0)
            ctx.handled_in_local = True
        if isinstance(error, AttributeError):
            await ctx.send(
                "I could not find that member. Member names are cAsE-sEnsitive. Use a mention, a user ID or a username")
            ctx.handled_in_local = True
        if isinstance(error, TypeError):
            await ctx.send(
                "Something happened between me and Discord, and I was unable to retrieve the object correctly. Please try again!")
            ctx.handled_in_local = True


def setup(bot):
    bot.add_cog(MarkovChain(bot))
