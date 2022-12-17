import json
from datetime import datetime
import asyncio
import asyncpg

import discord
import psutil
from discord.ext import commands, tasks





class HelpCommands(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.bot.total_nwords = bot.total_nwords

    async def not_disabled(self, ctx):
        try:
            if ctx.command.name in self.bot.disabled_guilds[str(ctx.guild.id)]:
                return False
            return True
        except:
            return True

    @commands.group()
    async def help(self, ctx): #command-specific in the future too?
        if ctx.invoked_subcommand is None:
            embed=discord.Embed(title="Command usage", description="**All commands use the same `,,` prefix.**", color=0xff8040)
            embed.set_author(name="Command list for Opportunity", icon_url="https://cdn.discordapp.com/attachments/699740616241709146/699878588501196810/rsz_mars_4.png")
            embed.add_field(name="help", value="Opens this list.", inline=False)
            embed.add_field(name="nwordcount <@member / #channel / server / leaderboard>", value="Counts a user's n-words on the server. Goes through all messages the bot can see.", inline=False)
            embed.add_field(name="imitate", value="Scans through a users message history to try to imitate them! Note: you must opt in using ,,optin. Opportunity will now store your messages for 2 weeks and use them to imitate you.", inline=False)
            embed.add_field(name="reddit <subreddit> <mediaonly> <search>", value="Searches for a submission on Reddit. 3-second cooldown. Example usage: ',,reddit pics mediaonly lake' or 'reddit pics lake'", inline=False)
            embed.add_field(name="trivia", value="Asks a trivia question with a 15-second response time!", inline=False)
            embed.add_field(name="radio", value="Streams a radio channel to your voice channel. Experimental, will likely support more channels in the future. Use ,,disconnect to disconnect the bot from VC.")
            embed.add_field(name="invite", value="Gives a link for inviting me to your server!", inline=False)
            embed.add_field(name="nasa", value="NASA-related commands: ,,nasa image | coming soon. See ',,help nasa' for detailed instructions.")
            embed.add_field(name="statistics", value="Sends a few fun statistics about Opportunity.", inline=False)
            embed.add_field(name="disable [command]", value="Disables a command for the guild. Requires permission: manage guild.", inline=False)
            embed.add_field(name="enable [command]", value="Enables a command for the guild. Requires permission: manage guild.", inline=False)
            embed.add_field(name="Bot not responding? Other issues?", value="Make sure that you've set permissions up correctly. I need at least the following permissions to function properly: read messages, read message history, send messages, embed links", inline=False)
            embed.set_footer(text="Don't forget to include the prefix. Example usage: ,,help")
            await ctx.send(embed=embed)

    @help.command(aliases=["nasa"])
    async def _nasa(self, ctx):
        embed = discord.Embed(title="Usage for ,,nasa:", description="`,,nasa image | [coming soon]`\n\n`,,nasa image [search query]`, example usage: `,,nasa image neil armstrong`", color=0xff8040)
        embed.set_footer(text="Don't forget to include the prefix. Example usage: ,,nasa image Opportunity")
        await ctx.send(embed=embed)

    @commands.command(aliases=["stats"])
    async def statistics(self, ctx):
        embed = discord.Embed(title="Statistics", description=f"[Consider voting for Opportunity on top.gg <3](https://top.gg/bot/386958619167424512)", timestamp=datetime.utcnow(), color=0xff8040)
        embed.add_field(name="Number of servers", value=str(len(self.bot.guilds)))
        embed.add_field(name="Average system load:", value=psutil.getloadavg())
        embed.add_field(name="Total number of n-words counted:", value=f'{self.bot.total_nwords}')
        embed.add_field(name="Shard count:", value=f"{self.bot.shard_count}")
        embed.set_footer(text="Opportunity and its developers do not support the usage of the n-word in any way. This feature is included only for entertainment purposes.")
        await ctx.send(embed=embed)


    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def disable(self, ctx, command):
        list = []
        cantdisable = ["help", "invite", "disable", "enable"]
        if command not in cantdisable:
            for comm in self.bot.walk_commands():
                if command in comm.name:
                    with open("disabled.json", "r+") as file:
                        dis = json.load(file)
                        try:
                            if command in dis[str(ctx.guild.id)]:
                                await ctx.send("Already disabled.")
                                return
                        except KeyError:
                            pass
                        try:
                            try:
                                for i in dis[str(ctx.guild.id)]:
                                    list.append(i)
                                list.append(command)
                            except AttributeError:
                                list.append(dis[str(ctx.guild.id)])
                                list.append(command)
                        except KeyError:
                            list.append(command)
                    dis.update({str(ctx.guild.id): list})
                    with open("disabled.json", "w+") as file:
                        json.dump(dis, file)
                    self.bot.disabled_guilds[str(ctx.guild.id)].append(command)
                    await ctx.send(f"Successfully disabled `{command}` in this guild")
                    return
        else:
            await ctx.send("You can't disable that command.")

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def enable(self, ctx, command):
        sep = ", "
        for comm in self.bot.walk_commands():
            if command in comm.name:
                with open("disabled.json", "r+") as file:
                    dis = json.load(file)
                if str(ctx.guild.id) in dis.keys():
                    if command in dis[str(ctx.guild.id)]:
                        dis[str(ctx.guild.id)].remove(command)
                        with open("disabled.json", "w+") as file:
                            json.dump(dis, file)
                        self.bot.disabled_guilds[str(ctx.guild.id)].remove(command)
                        await ctx.send(f"Successfully enabled `{command}` in this guild")
                        return
                    else:
                        await ctx.send(f"This command isn't disabled. Currently disabled commands: {sep.join(dis[str(ctx.guild.id)])}")
                        return
                else:
                    await ctx.send("This command isn't disabled.")
                    return
        await ctx.send("Invalid command. You can see a list of my commands with `,,help`")

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        icon_url = "https://cdn.discordapp.com/emojis/742406582939287634.png"
        await self.guild_join_embed(guild, action="Joined", icon_url=icon_url)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        icon_url = "https://cdn.discordapp.com/emojis/792836930587852830.png"
        await self.guild_join_embed(guild, action="Left", icon_url=icon_url)

    async def guild_join_embed(self, guild, action, icon_url):

        embed = discord.Embed(title=f"{action} a guild",
                              description=f"**Name**: {guild.name}\n"
                                          f"**ID**: {guild.id}\n"
                                          f"**Owner ID**: {str(guild.owner_id)}\n"
                                          f"**Created at**: {guild.created_at}\n"
                                          f"**Member count**: {guild.member_count}",
                              timestamp=datetime.utcnow(),
                              colour=16747520)
        embed.set_thumbnail(url=guild.icon.url)
        embed.set_footer(text="", icon_url=icon_url)

        join_log_channel = self.bot.get_channel(699954979901014016)
        await join_log_channel.send(embed=embed)


def setup(bot):
    bot.add_cog(HelpCommands(bot))
