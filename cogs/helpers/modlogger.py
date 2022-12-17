import discord
from discord.ext import commands, tasks

from cogs.helpers import confloader as cl

# avoiding circular dependency

async def logmute(self, ctx, mute_minutes, member, reason):
    logchan = self.bot.get_channel(cl.getlogctx(self, ctx))
    embed = discord.Embed(title="Member muted")
    embed.add_field(name="Moderator", value=ctx.author.mention)
    embed.add_field(name="User", value=f"<@{member[0].id}>")
    embed.add_field(name="Reason", value=reason)
    embed.add_field(name="Duration", value=mute_minutes)
    await logchan.send(embed=embed)

async def logunmute(self, ctx, member, reason):
    logchan = self.bot.get_channel(cl.getlogctx(self, ctx))
    embed = discord.Embed(title="Member unmuted")
    embed.add_field(name="User", value=f"<@{member[0].id}>")
    embed.add_field(name="Reason", value=reason)
    await logchan.send(embed=embed)

async def logumute(self, ctx, mute_minutes, member, reason):
    logchan = self.bot.get_channel(cl.getlogctx(self, ctx))
    embed = discord.Embed(title="Member unmuted")
    embed.add_field(name="Moderator", value=reason)
    embed.add_field(name="User", value=f"<@{member[0].id}>")
    await logchan.send(embed=embed)

async def auto_unmute(ctx, mute_minutes, member):
    await ctx.send("huomenta")
    muted_role = discord.utils.find(lambda m: m.name == "Muted", ctx.guild.roles)
    if muted_role in member.guild.roles:
        await member.remove_roles(muted_role)
        await ml.logunmute(ctx, mute_minutes, member)

async def logwarn(self, ctx, member, reason):
    logchan = self.bot.get_channel(cl.getlogctx(self, ctx))
    embed = discord.Embed(title="Member warned")
    embed.add_field(name="Moderator", value=ctx.author)
    embed.add_field(name="User", value=f"<@{member[0].id}>")
    embed.add_field(name="Reason", value=reason)
    await logchan.send(embed=embed)

async def logban(self, ctx, member, reason):
    logchan = self.bot.get_channel(cl.getlogctx(self, ctx))
    embed = discord.Embed(title="Member banned", color=0xff0000)
    embed.set_thumbnail(url=member[0].avatar_url)
    embed.add_field(name="Moderator", value=ctx.author)
    embed.add_field(name="User", value=f"<@{member[0].id}>")
    embed.add_field(name="Reason", value=reason)
    embed.set_footer(text=f"User ID: {member[0].id}")
    await logchan.send(embed=embed)

async def logmban(self, ctx, memberid, reason):
    logchan = self.bot.get_channel(cl.getlogctx(self, ctx))
    embed = discord.Embed(title="Member banned", color=0xff0000)
    embed.add_field(name="Moderator", value=ctx.author)
    embed.add_field(name="User", value=f"<@{memberid}>")
    embed.add_field(name="Reason", value=reason)
    embed.set_footer(text=f"User ID: {memberid}")
    await logchan.send(embed=embed)
