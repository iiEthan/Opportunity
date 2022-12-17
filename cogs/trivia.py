import discord
import aiohttp
import json 
import asyncio 
import random
import html

from discord.ext import commands
from datetime import datetime


class TriviaCommands(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def not_disabled(self, ctx):
        try:
            if ctx.command.name in self.bot.disabled_guilds[str(ctx.guild.id)]:
                return False
            return True
        except:
            return True

    @commands.command()
    @commands.cooldown(1.0, 3.0, commands.BucketType.user)
    async def trivia(self, ctx):

        async with aiohttp.ClientSession() as session:
            async with session.get('https://opentdb.com/api.php?amount=1') as r:

                if r.status != 200:
                    raise ValueError('Server returned a non-ok code: ' + r.status)

                response = await r.json()
                # This will help in making the code less of a clusterfuck
                question = html.unescape(response["results"][0]['question'])
                difficulty = html.unescape(response['results'][0]['difficulty'])
                category = html.unescape(response['results'][0]['category'])
                correct_answer = html.unescape(response['results'][0]['correct_answer'])
                incorrect_answers = response['results'][0]['incorrect_answers'] # This is a list so we'll unescape it later

                embed = discord.Embed(
                    title = question,
                    description = f'**You have 15 seconds to answer!**\nCategory: {category}\nDifficulty: {difficulty}',
                    colour = 0x63C5DA,
                    timestamp = datetime.utcnow()
                )

                all_answers = incorrect_answers.copy()
                all_answers.append(correct_answer) # Incorrect answers + the correct one
                random.shuffle(all_answers) # Randomly shuffle the answers
                correct_answer_index = all_answers.index(correct_answer) # Keeps track which is the correct answer
                

                letters = {0: 'A', 1: 'B', 2: 'C', 3: 'D', 4: 'F' } # I don't think there'll be more than 4 options but we'll see if there is
                n = 0

                for answer in all_answers:
                    embed.add_field(name=letters[n], value=html.unescape(answer), inline=False)
                    n += 1
                
                embed.set_footer(text="Respond with the letter assigned to the answer!")
                
                embed_message = await ctx.send(embed=embed)

                def check(m):
                    return m.author == ctx.author and m.channel == ctx.channel

                try:
                    message = await self.bot.wait_for('message', timeout=15.0, check=check)
                except asyncio.TimeoutError:
                    embed.description = f'Category: {category},\nDifficulty: {difficulty}\n❌ **You didn\'t respond fast enough!**'
                    return await embed_message.edit(content=None, embed=embed)
                else:
                    if message.content.upper().startswith(letters[correct_answer_index]) or message.content.lower().startswith(str(correct_answer.lower())):
                        await ctx.send(f"{ctx.author.mention} correct! Nice job <:oppie:742406582939287634>")
                    else:
                        await ctx.send(f"Nope! The correct answer was {letters[correct_answer_index]}, {correct_answer}.")

    @trivia.error
    async def on_trivia_error(self, ctx, error):
        if isinstance(error, ValueError):
            await ctx.send("Didn't receive a response code 200, please try again later.")
            ctx.handled_in_local = True 

        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(content=f"{ctx.author.mention}, you are on cooldown (3 s in between commands). Retry-after: {round(error.retry_after, 3)} s", delete_after=5.0)
            ctx.handled_in_local = True
        
def setup(bot):
    bot.add_cog(TriviaCommands(bot))
