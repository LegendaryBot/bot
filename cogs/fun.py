import requests
from discord.ext import commands
from discord.ext.commands import Cog


class Fun(Cog):
    """
    World of Warcraft related commands
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def gif(self, ctx, *search):
        """
        Search for a GIF
        """
        gif = " ".join(search)
        request = requests.post("https://rightgif.com/search/web", {"text": gif})
        json_entry = request.json()
        await ctx.send(json_entry['url'])


def setup(bot):
    bot.add_cog(Fun(bot))