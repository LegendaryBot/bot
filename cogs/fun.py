import requests
from discord.ext import commands


class Fun:
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