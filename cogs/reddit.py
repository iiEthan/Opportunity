import json
import time
from textwrap import wrap

import asyncpraw
import discord
from discord.ext import commands, tasks


class Reddit(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.bot.reddit_posts = []
        self.remove_seen_posts.start()
        self.bot.nword_used = 0

    async def not_disabled(self, ctx):
        try:
            if ctx.command.name in self.bot.disabled_guilds[str(ctx.guild.id)]:
                return False
            return True
        except:
            return True

    @commands.command()
    async def rockyplanet(self, ctx, arg=None):
        if arg == None:
            async for submission in reddit.subreddit("rockyplanet").random_rising(limit=1):
                emb = discord.Embed(title=submission.title, color=0x00ff4500)
                emb.add_field(name="upvotes: {}, op: {}".format(submission.score, submission.author),
                              value="https://reddit.com{}".format(submission.permalink))
                emb.set_image(url=submission.url)
                await ctx.channel.send(embed=emb)
        else:
            async for submission in reddit.subreddit("rockyplanet").arg(limit=1):
                emb = discord.Embed(title=submission.title, color=0x00ff4500)
                emb.add_field(name="upvotes: {}, op: {}".format(submission.score, submission.author),
                              value="https://reddit.com{}".format(submission.permalink))
                emb.set_image(url=submission.url)
                await ctx.channel.send(embed=emb)

    @rockyplanet.error
    async def rockyplanet_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            await ctx.channel.send(error)

    def check_if_seen(self, ctx, submission):
        for post in self.bot.reddit_posts:
            if submission.id in post[0]:
                if post[2] == ctx.guild.id:
                    return False
                return True
        return True

    @commands.command()
    @commands.cooldown(1.0, 3.0, commands.BucketType.user)
    async def reddit(self, ctx, subreddit="rockyplanet", *, search=None):
        self.bot.nword_used += 1
        sub = await reddit.subreddit(subreddit)
        await sub.load()
        nsfwcheck = sub.over18
        p = commands.Paginator(prefix='', suffix='', max_size=1024)
        if search is not None:
            d = search.split()
            if len(d) != 0:
                if d[0].lower() == "mediaonly":
                    searchb = search[10:]
                    medo = True
                else:
                    medo = False
                    searchb = search
        else:
            medo = False
            searchb = search
        if search is None or len(d) <= 1 and medo is True:
            async for submission in sub.random_rising(limit=None):
                if self.check_if_seen(ctx, submission):
                    text = wrap(submission.selftext, width=1000)
                    texta = [p.add_line(i) for i in text]
                    if len(str(submission.title)) >= 150:
                        embed = discord.Embed(title=f"{submission.title[:150]}...",
                                              description=f"[Author: u/{submission.author}, submission score: {submission.score}](https://reddit.com{submission.permalink})",
                                              color=0x00ff4500)
                    else:
                        embed = discord.Embed(title=submission.title[:150],
                                              description=f"[Author: u/{submission.author}, submission score: {submission.score}](https://reddit.com{submission.permalink})",
                                              color=0x00ff4500)
                    if len(submission.selftext) >= 1:
                        embed.add_field(name="Body:", value=p.pages[0], inline=False)
                    if not submission.is_self:
                        embed.set_image(url=submission.url)
                    embed.set_footer(
                        text="Use the mediaonly argument if media isn't loading. Example usage: ,,reddit [subreddit] <mediaonly> <what to search for>")
                    self.bot.reddit_posts.append((submission.id, time.time(), ctx.guild.id))
                    if nsfwcheck == True:
                        if ctx.channel.is_nsfw():
                            if medo:
                                await ctx.send(submission.url)
                            else:
                                message = await ctx.send(embed=embed)
                        else:
                            await ctx.send(
                                "You can only search for posts on NSFW subreddits on an NSFW-marked channel.")
                    else:
                        if submission.over_18:
                            if ctx.channel.is_nsfw():
                                if medo:
                                    await ctx.send(submission.url)
                                else:
                                    await self.sendembed(ctx, submission, text, embed, p)
                            else:
                                continue
                        else:
                            if medo:
                                await ctx.send(submission.url)
                            else:
                                await self.sendembed(ctx, submission, text, embed, p)
                    break

        else:
            async for submission in sub.search(searchb, syntax="cloudsearch"):
                if self.check_if_seen(ctx, submission):
                    text = wrap(submission.selftext, width=1000)
                    texta = [p.add_line(i) for i in text]
                    if len(str(submission.title)) >= 150:
                        embed = discord.Embed(title=f"{submission.title[:150]}...",
                                              description=f"[Author: u/{submission.author}, submission score: {submission.score}](https://reddit.com{submission.permalink})",
                                              color=0x00ff4500)
                    else:
                        embed = discord.Embed(title=submission.title[:150],
                                              description=f"[Author: u/{submission.author}, submission score: {submission.score}](https://reddit.com{submission.permalink})",
                                              color=0x00ff4500)
                    if len(submission.selftext) >= 1:
                        embed.add_field(name="Body:", value=p.pages[0], inline=False)
                    if not submission.is_self:
                        embed.set_image(url=submission.url)
                    embed.set_footer(
                        text="Use the mediaonly argument if media isn't loading. Example usage: ,,reddit [subreddit] <mediaonly> <what to search for>")
                    self.bot.reddit_posts.append((submission.id, time.time(), ctx.guild.id))
                    if nsfwcheck == True:
                        if ctx.channel.is_nsfw():
                            if medo:
                                await ctx.send(submission.url)
                            else:
                                message = await ctx.send(embed=embed)
                        else:
                            await ctx.send(
                                "You can only search for posts on NSFW subreddits on an NSFW-marked channel.")
                    else:
                        if submission.over_18:
                            if ctx.channel.is_nsfw():
                                if medo:
                                    await ctx.send(submission.url)
                                else:
                                    await self.sendembed(ctx, submission, text, embed, p)
                            else:
                                continue
                        else:
                            if medo:
                                await ctx.send(submission.url)
                            else:
                                await self.sendembed(ctx, submission, text, embed, p)
                    break

    async def sendembed(self, ctx, submission, text, embed, p):

        message = await ctx.send(embed=embed)
        if submission.is_self:
            if len(text) > 1:
                one = await message.add_reaction("⬅️")
                two = await message.add_reaction("➡️")
                print(p.pages)
                print(ctx.message.author)
                self.bot.onpage = 0
                reactions = ["➡️", "⬅️"]

                def check(reaction, user):
                    if user == self.bot.user:
                        return False
                    if str(reaction.emoji) == "➡️":
                        if self.bot.onpage <= len(text):
                            self.bot.onpage += 1
                        return user == ctx.message.author and reaction.message.id == message.id and str(
                            reaction.emoji) == "➡️"
                    if str(reaction.emoji) == "⬅️":
                        if self.bot.onpage >= 1:
                            self.bot.onpage -= 1
                        return user == ctx.message.author and reaction.message.id == message.id and str(
                            reaction.emoji) == "⬅️"

                while True:
                    try:
                        reaction, user = await self.bot.wait_for('reaction_add', timeout=180.0, check=check)
                        try:
                            await reaction.remove(ctx.message.author)
                        except:
                            pass
                    except Exception:  # asyncio.TimeoutError doesn't work. weird.
                        await message.remove_reaction("⬅️", self.bot.user)
                        await message.remove_reaction("➡️", self.bot.user)
                        break
                    else:
                        try:
                            if len(str(submission.title)) >= 150:
                                embed = discord.Embed(title=f"{submission.title[:150]}...",
                                                      description=f"[Author: u/{submission.author}, submission score: {submission.score}](https://reddit.com{submission.permalink})",
                                                      color=0x00ff4500)
                            else:
                                embed = discord.Embed(title=submission.title[:150],
                                                      description=f"[Author: u/{submission.author}, submission score: {submission.score}](https://reddit.com{submission.permalink})",
                                                      color=0x00ff4500)
                            if len(submission.selftext) >= 1:
                                embed.add_field(name="Body:", value=p.pages[self.bot.onpage], inline=False)
                            if not submission.is_self:
                                embed.set_image(url=submission.url)
                            embed.set_footer(text=f"Page {self.bot.onpage + 1}/{len(text)}")
                            await message.edit(embed=embed)
                        except IndexError:
                            self.bot.onpage -= 1

    @reddit.error
    async def reddit_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            if "Redirect" in str(error.__cause__):
                embed = discord.Embed(title="An error occured while getting a submission from reddit:",
                                      description="Redirect to /subreddits/search\n(this usually means that the subreddit doesn't exist)")
                embed.set_footer(text="If this happens but the error is wrong, please submit a devrequest.")
                await ctx.send(embed=embed)
                ctx.handled_in_local = True
            if "403" in str(error.__cause__):
                embed = discord.Embed(title="An error occured while getting a submission from reddit:",
                                      description="received 403 Forbidden HTTP response\n(this usually means that the subreddit is banned, private, premium-, or employee-only.)")
                embed.set_footer(text="If this happens but the error is wrong, please submit a devrequest.")
                await ctx.send(embed=embed)
                ctx.handled_in_local = True
            if "404" in str(error.__cause__):
                embed = discord.Embed(title="An error occured while getting a submission from reddit:",
                                      description="received 404 NotFound HTTP response\n(this usually means that the subreddit doesn't exist)")
                embed.set_footer(text="If this happens but the error is wrong, please submit a devrequest.")
                await ctx.send(embed=embed)
                ctx.handled_in_local = True
            if "500" in str(error.__cause__):
                embed = discord.Embed(title="An error occured while getting a submission from reddit:",
                                      description="received 500 InternalServerError HTTP response\n(an error happened on reddit's end)")
                embed.set_footer(text="An error log was automatically sent to the support server")
                await ctx.send(embed=embed)
            if isinstance(error, commands.CommandOnCooldown):
                await ctx.send(
                    content=f"{ctx.author.mention}, you are on cooldown (3 s in between commands). Retry-after: {round(error.retry_after, 3)} s",
                    delete_after=5.0)
                ctx.handled_in_local = True
            else:
                await ctx.send(
                    "An error occured while getting a submission from Reddit. Example usage: `,,reddit memes mediaonly dank`")
                ctx.handled_in_local = True

    @tasks.loop(minutes=30)
    async def remove_seen_posts(self):
        for post in self.bot.reddit_posts:
            if round(time.time()) - post[1] > 36000:
                self.bot.reddit_posts.remove(post)


reddit = asyncpraw.Reddit(client_id='SUz6Oh1ksE1Phw',
                          client_secret='u9wE9Yf3mDtkMmfIbzvSiuP4vZw',
                          user_agent='marsbot discord bot',
                          username='marzbotsts',
                          password="8ErT#b5xqjnLqFa")


def setup(bot):
    bot.add_cog(Reddit(bot))
