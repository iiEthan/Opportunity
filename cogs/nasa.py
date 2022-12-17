import discord
from discord.ext import commands

import requests
import json
import random
from datetime import datetime


class NasaCommands(commands.Cog):

    def __init__(self, bot):
        
        self.bot = bot

    async def not_disabled(self, ctx):
        try:
            if ctx.command.name in self.bot.disabled_guilds[str(ctx.guild.id)]:
                return False
            return True
        except:
            return True

    @commands.group()
    async def nasa(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send(content="No argument specified: see `,,help nasa` for detailed instructions.", delete_after=15.0)
    
    @nasa.command(aliases=["img", "picture", "pic"])
    @commands.cooldown(1.0, 4.0, commands.BucketType.user)
    async def image(self, ctx, *, query = None):

        default = False
        if query is None:
            default_queries = ["astronaut", "earth", "mars", "space", "opportunity", "curiosity", "iss"]
            query = random.choice(default_queries)
            default = True

        search_endpoint = "https://images-api.nasa.gov/search?q="
        r = requests.get(url=search_endpoint + query)

        if r.ok: # if the request got code 200
            data = r.json() # jsonify
            if data["collection"]["metadata"]["total_hits"] == 0: # if the amount of results is zero
                data = None
                title = "No image found"
                description = "No results were found with this search query."

        else: # should be rare but can happen
            data = None
            title = "The NASA API returned a non-ok code: " + r.status_code
            description = "If this problem persists, feel free to join the support server."
        
        if data is not None:

            item = random.choice(data["collection"]["items"]) # the request returns a huge list of results, this chooses one of them
            image_url = item["links"][0]["href"] 
            description = item["data"][0]["description"][:200] + "...\nImage taken on: " + item["data"][0]["date_created"][:10] # description + newline + creation date
            title = item["data"][0]["title"]
        
        embed = discord.Embed(title=title, description=description, timestamp=datetime.utcnow(), color=0xff8040)
        if data is not None: # if we found a result, set image url to it
            embed.set_image(url=image_url)

        if default is True:
            embed.set_footer(text="Tip: you can give a search query, ',,nasa image saturn' for example.")
        else:
            embed.set_footer(text="Images supplied from NASA's Images API")

        await ctx.send(embed=embed)
    
    @image.error
    async def image_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(content=f"{ctx.author.mention}, you are on cooldown (4 s in between commands). Retry-after: {round(error.retry_after, 3)} s", delete_after=5.0)
            ctx.handled_in_local = True
        

def setup(bot):
    bot.add_cog(NasaCommands(bot))