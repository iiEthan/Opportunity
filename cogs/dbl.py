import dbl
import discord
from discord.ext import commands


class TopGG(commands.Cog):
    """Handles interactions with the top.gg API"""

    def __init__(self, bot):
        self.bot = bot
        self.token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjM4Njk1ODYxOTE2NzQyNDUxMiIsImJvdCI6dHJ1ZSwiaWF0IjoxNTk2OTIwNTY3fQ.7-d5w00ctLhf7omzGci-gygu_4AGB_0CYHspJQ6HPYw' # set this to your DBL token
        self.dblpy = dbl.DBLClient(self.bot, self.token, autopost=True) # Autopost will post your guild count every 30 minutes

    async def on_guild_post():
        print("Server count posted successfully")

def setup(bot):
    bot.add_cog(TopGG(bot))
