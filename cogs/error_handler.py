import discord
import traceback
import textwrap
from discord.ext import commands

#
# This was largely copied from https://gist.github.com/EvieePy/7822af90858ef65012ea500bcecf1612
# because i'm lazy as hell
#


class CommandErrorHandler(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):

        # This prevents any commands with local handlers being handled here in on_command_error.
        if hasattr(ctx.command, 'on_error'):
            return
        
        if hasattr(ctx, 'handled_in_local'):
            return

        ignored = commands.CommandNotFound

        # Allows us to check for original exceptions raised and sent to CommandInvokeError.
        # If nothing is found. We keep the exception passed to on_command_error.
        error = getattr(error, 'original', error)

        # Anything in ignored will return and prevent anything happening.
        if isinstance(error, ignored):
            return
        if isinstance(error, commands.CommandOnCooldown):
            return

        formatted_error = traceback.format_exception(type(error), error, error.__traceback__)
        joiner = ""
        error_string = joiner.join(formatted_error)
        n = 1890  # split every n characters
        list_of_strings = [error_string[i:i+n] for i in range(0, len(error_string), n)]

        p = commands.Paginator(prefix='```py', suffix='```', max_size=1900)

        for text_page in list_of_strings:
            p.add_line(text_page)

        pagenumber = 1
        channel = self.bot.get_channel(711643281343250503)

        for error_page in p.pages:

            em = None

            if pagenumber == len(p.pages):
                embed = discord.Embed(title=f"An error occurred (page {pagenumber}/{len(p.pages)}):")
                embed.add_field(name="Full context:", value=f"Guild: {ctx.guild} ({ctx.guild.id})\nauthor: {ctx.author} ({ctx.author.id})\nchannel: {ctx.channel} ({ctx.channel.id})\nmessage: {ctx.message.content}")
                embed.set_footer(text=ctx.message.id)
                em = embed

            await channel.send(error_page, embed=em)
            pagenumber += 1


def setup(bot):
    bot.add_cog(CommandErrorHandler(bot))
