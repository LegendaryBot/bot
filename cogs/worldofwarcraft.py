import os

from discord import Embed, Colour
from discord.ext import commands
import requests
from discord.ext.commands import Context
from slugify import slugify
from utils import battlenet_util


def get_guild_realm(ctx: Context):
    return ctx.bot.get_guild_setting(ctx.guild, "REALM_NAME")


class WoW:
    """
    World of Warcraft related commands
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def token(self, ctx):
        """
        Get the WoW token price of your region
        """
        token_request = requests.get("https://data.wowtoken.info/snapshot.json")
        token_json = token_request.json()
        if "NA" in token_json:
            region_json = token_json['NA']['formatted']
            embed = Embed(title="Price for 1 WoW Token in the NA region",
                          color=Colour.from_rgb(255, 215, 0))
            embed.set_footer(text="Information taken from https://wowtoken.info",
                             icon_url="http://wow.zamimg.com/images/wow/icons/large/wow_token01.jpg")
            embed.set_thumbnail(url="http://wow.zamimg.com/images/wow/icons/large/wow_token01.jpg")
            embed.add_field(name="Current Price", value=region_json['buy'], inline=True)
            embed.add_field(name="Minimum 24H", value=region_json['24min'], inline=True)
            embed.add_field(name="Maximum 24H", value=region_json['24max'], inline=True)
            embed.add_field(name="Percentage 24H Range", value="%s %%" % region_json['24pct'])
            await ctx.send(embed=embed)

    @commands.command(name="status", aliases=["server"], rest_is_raw = True)
    async def get_realm_status(self, ctx, *realm: str):
        """
        Get the status of a World of Warcraft realm.

        [realm]: The realm you want to check the status of. Optional if the server have a realm set during initial setup.
        If your realm name have spaces in it's name, please quote the name with "".
        Example: "Bleeding Hollow"
        """
        if realm is None:
            realm = get_guild_realm(ctx.guild)
            if realm is None:
                raise commands.BadArgument('You are required to type a realm.')
        else:
            realm = " ".join(realm)
        realm_slug = slugify(realm)
        region = self.bot.get_guild_setting(ctx.guild, 'REGION_NAME', 'US')
        oauth = battlenet_util.get_battlenet_oauth(region)
        r = oauth.get(f"https://{region}.api.battle.net/data/wow/realm/{realm_slug}?namespace=dynamic-us&locale=en_US")
        if r.ok:
            r = requests.get(f"https://{region}.api.battle.net/wow/realm/status",
                             params={"realms": realm_slug, "apikey": os.getenv(f"{region}_KEY")})
            json_result = r.json()
            if 'realms' in json_result and len(json_result['realms']) > 0:
                realm_json = json_result['realms'][0]
                embed = Embed(title=f"{realm_json['name']} - {region.upper()}",
                              colour=Colour.green() if realm_json['status'] else Colour.red())
                embed.add_field(name="Status", value="Online" if realm_json['status'] else "Offline", inline=True)
                embed.add_field(name="Population", value=realm_json['population'], inline=True)
                embed.add_field(name="Currently a Queue?", value="Yes" if realm_json['queue'] else "No", inline=True)
                await ctx.send(embed=embed)
        else:
            raise commands.BadArgument('Realm not found. Did you make a mistake?')

    @commands.command(name="affix")
    async def get_mythicplus_affix(self, ctx):
        """
        Get the Mythic+ affixes of this week.
        """
        region = self.bot.get_guild_setting(ctx.guild, 'REGION_NAME', 'US')
        oauth = battlenet_util.get_battlenet_oauth(region)
        r = oauth.get(f"https://{region}.api.battle.net/data/wow/mythic-challenge-mode/?namespace=dynamic-us&locale=en_US")
        json_mythicplus = r.json()
        embed = Embed()
        embed.set_thumbnail(url="http://wow.zamimg.com/images/wow/icons/large/inv_relics_hourglass.jpg")
        current_difficulty = 0
        for current_affix in json_mythicplus['current_keystone_affixes']:
            embed.add_field(name="(%i) %s" % (current_affix['starting_level'], current_affix['keystone_affix']['name']), value=mythicplus_affix[current_affix['keystone_affix']['id']]['description'], inline=False)
            current_difficulty += mythicplus_affix[current_affix['keystone_affix']['id']]['difficulty']
        if current_difficulty <= 3:
            embed.colour = Colour.green()
        elif current_difficulty == 4:
            embed.colour = Colour.from_rgb(255,255,0)
        else:
            embed.colour = Colour.red()
        await ctx.send(embed=embed)

    @commands.command()
    async def lookup(self, character_name: str, ):
        print("lol")

def setup(bot):
    bot.add_cog(WoW(bot))


mythicplus_affix = {
    1: {
        "difficulty": 1,
        "description": "Healing in excess of a target's maximum health is instead converted to a heal absorption effect.",
    },
    2: {
        "difficulty": 2,
        "description": "Enemies pay far less attention to threat generated by tanks. 80% Threat reduction.",
    },
    3: {
        "difficulty": 0,
        "description": "While in combat, enemies periodically cause gouts of flame to erupt beneath the feet of distant players.",
    },
    4: {
        "difficulty": 2,
        "description": "All enemies' melee attacks apply a stacking blight that inflicts damage over time and reduces healing received.",
    },
    5: {
        "difficulty": 1,
        "description": "Additional non-boss enemies are present throughout the dungeon.",
    },
    6: {
        "difficulty": 1,
        "description": "Non-boss enemies enrage at 30% health remaining, dealing 100% increased damage until defeated.",
    },
    7: {
        "difficulty": 1,
        "description": "When any non-boss enemy dies, its death cry empowers nearby allies, increasing their maximum health and damage by 20%.",
    },
    8: {
        "difficulty": 0,
        "description": "When slain, non-boss enemies leave behind a lingering pool of ichor that heals their allies and damages players.",
    },
    9: {
        "difficulty": 2,
        "description": "Boss enemies have 40% more health and inflict up to 15% increased damage.",
    },
    10: {
        "difficulty": 2,
        "description": "Non-boss enemies have 20% more health and inflict up to 30% increased damage.",
    },
    11: {
        "difficulty": 1,
        "description": "When slain, non-boss enemies explode, causing all players to suffer 10% of their max health in damage over 4 sec. This effect stacks.",
    },
    12: {
        "difficulty": 1,
        "description": "When injured below 90% health, players will suffer increasing damage over time until healed above 90% health.",
    },
    13: {
        "difficulty": 1,
        "description": "While in combat, enemies periodically summon Explosive Orbs that will detonate if not destroyed.",
    },
    14: {
        "difficulty": 1,
        "description": "Periodically, all players emit a shockwave, inflicting damage and interrupting nearby allies.",
    },

}
