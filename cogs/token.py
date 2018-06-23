from discord import Embed, Colour
from discord.ext import commands
import requests


class Token:

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def token(self, ctx):
        token_request = requests.get("https://data.wowtoken.info/snapshot.json")
        token_json = token_request.json()
        if "NA" in token_json:
            region_json = token_json['NA']['formatted']
            embed = Embed(title="Price for 1 WoW Token in the NA region",
                          color=Colour.from_rgb(255, 215, 0).value)
            embed.set_footer(text="Information taken from https://wowtoken.info", icon_url="http://wow.zamimg.com/images/wow/icons/large/wow_token01.jpg")
            embed.set_thumbnail(url="http://wow.zamimg.com/images/wow/icons/large/wow_token01.jpg")
            embed.add_field(name="Current Price", value=region_json['buy'], inline=True)
            embed.add_field(name="Minimum 24H", value=region_json['24min'], inline=True)
            embed.add_field(name="Maximum 24H", value=region_json['24max'], inline=True)
            embed.add_field(name="Percentage 24H Range", value="%s %%" % region_json['24pct'])
            await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Token(bot))