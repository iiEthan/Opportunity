import discord
from discord.ext import commands

import asyncio
import json
from datetime import datetime


class Radio(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def not_disabled(self, ctx):
        try:
            if ctx.command.name in self.bot.disabled_guilds[str(ctx.guild.id)]:
                return False
            return True
        except:
            return True

    @staticmethod
    def find_radio_channel(supported_channels, channel_radio):

        if " " in channel_radio:
            channel_radio = channel_radio.split()
        else:
            channel_radio = [channel_radio]

        for channel, description in supported_channels.items():

            for word in channel_radio:
                if word in channel.lower():
                    return channel, description

        return False

    @commands.command(aliases=["radio"])
    async def _radio(self, ctx, channel_radio=None):

        # These should be added to a JSON file at some point in time
        supported_channels = {"Järviradio": {"link": "http://radio2.6net.fi:8000/jarviradio2",
                                             "description": ":flag_fi: An old-school radio channel for people with a terrible music taste."},

                              "Radio Ålesund": {"link": "http://stream.jaerradiogruppen.no:8008/",
                                                "description": ":flag_no: A small radio station playing generic pop, located in Ålesund, Norway!"},

                              "Radio Rock": {
                                  "link": "https://digitacdn.akamaized.net/hls/live/629243/radiorock/master.m3u8",
                                  "description": ":flag_fi: Nice music in general!"},

                              "Hit Mix": {
                                  "link": "https://digitacdn.akamaized.net/hls/live/629243/hitmix/master-128000.m3u8",
                                  "description": ":flag_fi: <a:catJAM:892023520220049449>"
                              },

                              "YleX": {
                                  "link": "http://yleuni-f.akamaihd.net/i/yleliveradiohd_2@113879/master.m3u8",
                                  "description": ":flag_fi: <a:dancedude:892024143862698054>"
                              },

                              "Bassoradio": {"link": "https://stream.bauermedia.fi/basso/bassoradio_64.aac",
                                             "description": ":flag_fi: Nice bass :)"},

                              "Retro FM": {"link": "http://79.111.14.76:9063/;",
                                           "description": ":flag_ru: This almost broke my headphones when I first found it."},

                              "EWTN Catholic Radio": {"link": "http://patmos.cdnstream.com:9677/stream",
                                                      "description": ":flag_us: A catholic radio station located in Irondale, AL!"},

                              "Bible Broadcasting Network": {
                                  "link": "https://streams.radiomast.io/844b0a81-f4b9-485e-adaa-aab8d3ea9f7f",
                                  "description": ":flag_us: :cross:"},

                              "Relevant Radio": {"link": "http://relevantradio-ice.streamguys.us/RRBarix2",
                                                 "description": ":flag_us: It's relevant!"}}

        if channel_radio is None:

            description_string = "**Command syntax:** `,,radio [channel name]`\n"
            for name, description in self.bot.radiochannels.items():
                description_string += f"{name}: {description['description']}\n"

            embed = discord.Embed(title="Supported radio channels", description=description_string, colour=16747520,
                                  timestamp=datetime.utcnow())
            embed.set_footer(text="You can request your own radio station to be added on the support server!")
            return await ctx.send(embed=embed)

        if channel_radio not in supported_channels.keys():

            if self.find_radio_channel(supported_channels, channel_radio) is False:
                return await ctx.send("Couldn't find that channel! See `,,radio` for a list of channels.")

            channel_radio, description = self.find_radio_channel(supported_channels, channel_radio)
            description = description["description"]

        else:

            description = supported_channels[channel_radio]["description"]

        try:
            author = ctx.author.name  # This will just check if we have it cached
        except AttributeError:  # And raise AttributeError as ctx.author will be None if it isn't cached
            return await ctx.send(
                "Failed to find command author in cache, please try again!")  # Ree discord give us members intent

        if not ctx.author.voice:
            return await ctx.send("You must be in a voice channel to use this command!")

        if ctx.voice_client is None:
            channel = await ctx.author.voice.channel.connect()

        elif ctx.guild.me.voice.channel != ctx.author.voice.channel:
            return await ctx.send(f"I'm already connected to `{ctx.guild.me.voice.channel.name}`")

        else:
            channel = ctx.voice_client

        channel_link = supported_channels[channel_radio]["link"]

        source = await discord.FFmpegOpusAudio.from_probe(channel_link)

        if channel.is_playing():
            channel.stop()

        channel.play(source)

        embed = discord.Embed(title=f"Now listening to {channel_radio}", description=description,
                              timestamp=datetime.utcnow())
        embed.set_footer(text="You can suggest more channels on the support server!")

        await ctx.send(embed=embed)

    @commands.command()
    async def disconnect(self, ctx):
        if ctx.voice_client is not None:
            await ctx.voice_client.disconnect()

    @_radio.error
    async def _radio_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            try:
                await ctx.send("I don't have permissions to join the channel!")
                ctx.handled_in_local = True
                return
            except commands.MissingPermissions:
                await ctx.author.send(
                    "I don't have permissions to send messages in the channel and/or join the voice channel!")
                ctx.handled_in_local = True
                return
        await ctx.send(f"An error occured and was automatically reported, please try again! {error}")

    @commands.command()
    @commands.is_owner()
    async def stream(self, ctx, url):

        if ctx.voice_client is None:
            channel = await ctx.author.voice.channel.connect()

        elif ctx.guild.me.voice.channel != ctx.author.voice.channel:
            return await ctx.send(f"I'm already connected to `{ctx.guild.me.voice.channel.name}`")

        else:
            channel = ctx.voice_client

        source = await discord.FFmpegOpusAudio.from_probe(url)

        channel.play(source)

        await ctx.message.add_reaction("✅")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):

        state = None
        if before.channel is None:
            state = after
        if after.channel is None:
            state = before

        if state is None:
            return
        if member == state.channel.guild.me:
            return

        if state.channel.guild.voice_client is not None:
            if state.channel == state.channel.guild.me.voice.channel:
                if len(state.channel.guild.me.voice.channel.members) == 1:  # Check if we're alone in the VC
                    await asyncio.sleep(5)
                    if len(
                            state.channel.guild.me.voice.channel.members) == 1:  # Disconnect if there's still no one else in the VC
                        await state.channel.guild.voice_client.disconnect()


def setup(bot):
    bot.add_cog(Radio(bot))
