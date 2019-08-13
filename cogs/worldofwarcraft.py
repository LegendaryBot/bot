import datetime
import os
from decimal import Decimal

import requests
from discord import Embed, Colour
from discord.ext import commands
from lbwebsite.models import GuildServer, Character, RealmConnected
from slugify import slugify
from social_django.models import UserSocialAuth

from utils import battlenet_util
from utils.simple_utc import simple_utc
from utils.wow_utils import get_color_by_class_name, get_class_icon
from utils.translate import _


def convertMillis(millis):
    seconds=int((millis/1000)%60)
    minutes=int((millis/(1000*60))%60)
    hours=int((millis/(1000*60*60))%24)
    return seconds, minutes, hours

def affixEmbed(embed, difficulty, affix):
    embed.add_field(name="(%i) %s" % (affix['starting_level'], affix['keystone_affix']['name']["en_US"]),
                    value=mythicplus_affix[affix['keystone_affix']['id']]['description'], inline=False)
    difficulty += mythicplus_affix[affix['keystone_affix']['id']]['difficulty']
    return embed, difficulty

class WoW:
    """
    World of Warcraft related commands
    """

    def __init__(self, bot):
        self.bot = bot

    def __sub_format_ranking(self, difficulty):
        if difficulty is not None:
            ranking = _("World: **{world}**").format(world=difficulty['world']) + "\n"
            ranking += _("Region: **{region}**").format(region=difficulty['region']) + "\n"
            ranking += _("Realm: **{realm}**").format(difficulty['realm']) + "\n"
        else:
            ranking = _("**Not started**")+"\n"
        return ranking

    def __format_ranking(self, raid_json):
        return_string = ""
        normal = raid_json['normal']
        heroic = raid_json['heroic']
        mythic = raid_json['mythic']
        if normal['world'] != 0 and heroic['world'] == 0 and mythic['world'] == 0:
            return_string += _("**Normal**") + "\n"
            return_string += self.__sub_format_ranking(normal)
        elif heroic['world'] != 0 and mythic['world'] == 0:
            return_string += "\n" + _("**Heroic**") + "\n"
            return_string += self.__sub_format_ranking(heroic)
        elif mythic['world'] != 0:
            return_string += "\n" + _("**Mythic**") + "\n"
            return_string += self.__sub_format_ranking(mythic)
        else:
            return_string += self.__sub_format_ranking(None)
        return return_string

    @commands.command()
    async def token(self, ctx, region: str = None):
        """
        Get the WoW token price of your region
        """
        if region is None and ctx.guild:
            guild_server = GuildServer.objects.filter(guild_id=ctx.guild.id, default=True).first()
            if guild_server:
                region = guild_server.get_region_display()
            else:
                raise commands.BadArgument(_('You are required to type the region. Supported regions are: NA/EU/CN/TW/KR'))
        token_request = requests.get("https://data.wowtoken.info/snapshot.json")
        token_json = token_request.json()
        if region.upper() == "US":
            region = "NA"
        if region.upper() in token_json:
            region_json = token_json[region.upper()]['formatted']
            embed = Embed(title=_("Price for 1 WoW Token in the {region} region").format(region=region.upper()),
                          color=Colour.from_rgb(255, 215, 0))
            embed.set_footer(text=_("Information taken from https://wowtoken.info"),
                             icon_url="http://wow.zamimg.com/images/wow/icons/large/wow_token01.jpg")
            embed.set_thumbnail(url="http://wow.zamimg.com/images/wow/icons/large/wow_token01.jpg")
            embed.add_field(name=_("Current Price"), value=region_json['buy'], inline=True)
            embed.add_field(name=_("Minimum 24H"), value=region_json['24min'], inline=True)
            embed.add_field(name=_("Maximum 24H"), value=region_json['24max'], inline=True)
            embed.add_field(name=_("Percentage 24H Range"), value="%s %%" % region_json['24pct'])
            await ctx.send(embed=embed)
        else:
            raise commands.BadArgument(_('Region not found. Supported regions are: NA/EU/CN/TW/KR'))

    @commands.command(name="status", aliases=["server"], rest_is_raw=True)
    async def get_realm_status(self, ctx, region: str = None, *realm: str):
        """
        Get the status of a World of Warcraft realm.

        [realm]: The realm you want to check the status of. Optional if the server have a realm set during initial setup.
        If your realm name have spaces in it's name, please quote the name with "".
        Example: "Bleeding Hollow"
        """
        if region is None or realm is None and ctx.guild:
            guild_server = GuildServer.objects.filter(guild_id=ctx.guild.id, default=True).first()
            if guild_server:
                realm_slug = guild_server.server_slug
            else:
                raise commands.BadArgument(_('You are required to type a realm.'))
        else:
            realm = " ".join(realm)
            realm_slug = slugify(realm)
        if ctx.guild:
            guild_server = GuildServer.objects.filter(guild_id=ctx.guild.id, default=True).first()
            if guild_server:
                region = guild_server.get_region_display()
        params = {
            "namespace": f"dynamic-{region}",
            "locale": "en-US"
        }
        r = battlenet_util.execute_battlenet_request(f"https://{region}.api.blizzard.com/data/wow/realm/{realm_slug}", params)
        if r.ok:
            r = battlenet_util.execute_battlenet_request(f"https://{region}.api.blizzard.com/wow/realm/status", params={"realms": realm_slug})
            json_result = r.json()
            if 'realms' in json_result and len(json_result['realms']) > 0:
                realm_json = json_result['realms'][0]
                embed = Embed(title=f"{realm_json['name']} - {region.upper()}",
                              colour=Colour.green() if realm_json['status'] else Colour.red())
                embed.add_field(name=_("Status"), value=_("Online") if realm_json['status'] else _("Offline"), inline=True)
                embed.add_field(name=_("Population"), value=realm_json['population'], inline=True)
                embed.add_field(name=_("Currently a Queue?"), value=_("Yes") if realm_json['queue'] else _("No"), inline=True)
                await ctx.send(embed=embed)
        else:
            raise commands.BadArgument(_('Realm not found. Did you make a mistake?'))

    @commands.command(name="affix")
    async def get_mythicplus_affix(self, ctx):
        """
        Get the Mythic+ affixes of this week.
        """
        guild_server = GuildServer.objects.filter(guild_id=ctx.guild.id, default=True).first()
        region = "us"
        if guild_server:
            region = guild_server.get_region_display()
        params = {
            "namespace": f"dynamic-{region}",
            "locale": "en-US"
        }
        r = battlenet_util.execute_battlenet_request(f"https://{region}.api.blizzard.com/data/wow/mythic-challenge-mode/", params=params)
        json_mythicplus = r.json()
        embed = Embed()
        embed.set_thumbnail(url="http://wow.zamimg.com/images/wow/icons/large/inv_relics_hourglass.jpg")
        current_difficulty = 0
        embed, current_difficulty = affixEmbed(embed, current_difficulty, json_mythicplus['current_keystone_affixes'][0])
        embed, current_difficulty = affixEmbed(embed, current_difficulty, json_mythicplus['current_keystone_affixes'][1])
        embed, current_difficulty = affixEmbed(embed, current_difficulty, json_mythicplus['current_keystone_affixes'][2])
        embed, current_difficulty = affixEmbed(embed, current_difficulty, json_mythicplus['current_keystone_affixes'][3])

        if current_difficulty <= 3:
            embed.colour = Colour.green()
        elif current_difficulty == 4:
            embed.colour = Colour.from_rgb(255, 255, 0)
        else:
            embed.colour = Colour.red()
        await ctx.send(embed=embed)

    @commands.command()
    async def lookup(self, ctx, character_name: str = None, realm_name: str = None, region: str = None):
        """
        Lookup a specific character
        character_name: The character name you want to search (Optional if your main character is set)
        realm_name: The realm of the character (Optional if the guild is set in this server)
        region: The region (US/EU) the character is in (Optional if the guild is set in this server)
        """
        if not character_name:
            user_social = UserSocialAuth.objects.filter(provider='discord', uid=ctx.author.id).first()
            if user_social:
                character = Character.objects.filter(user=user_social.user, main_for_guild=ctx.guild.id).first()
                if character:
                    character_name = character.name
                    realm_name = character.server_slug
                    region = character.get_region_display()
                else:
                    raise commands.BadArgument(_("You must enter a character name."))
            else:
                raise commands.BadArgument(_("You must enter a character name."))
        if not realm_name:
            guild_server = GuildServer.objects.filter(guild_id=ctx.guild.id, default=True).first()
            if guild_server:
                realm_name = guild_server.server_slug
                region = guild_server.get_region_display()
            else:
                raise commands.BadArgument(_("You must put the realm and the region."))

        if not region:
            raise commands.BadArgument(_("The only valid regions are US or EU."))
        
        if region.lower() != "us" and region.lower() != "eu":
            raise commands.BadArgument(_("The only valid regions are US or EU."))

        region = region.lower()
        realm_name = slugify(realm_name)
        not_ok = True

        while not_ok:
            payload = {
                "region": region,
                "realm": realm_name,
                "name": character_name,
                "fields": "gear,raid_progression,mythic_plus_scores,previous_mythic_plus_scores,mythic_plus_best_runs"
            }
            r = requests.get(f"https://raider.io/api/v1/characters/profile", params=payload)
            i = 0
            if r.ok:
                not_ok = False
            else:
                #We did not find the character, let's see another connected realm
                realm_database = RealmConnected.objects.filter(server_slug=realm_name).first()
                connected_realms = realm_database.connected_realm.all()
                if len(connected_realms) > i:
                    realm_name = realm_database.connected_realm.all()[i]
                    i += 1
                else:
                    raise commands.BadArgument(_("Character not found! Does it exist on Raider.IO?"))
            raiderio = r.json()
            embed = Embed()
            embed.set_thumbnail(url=raiderio['thumbnail_url'])
            embed.colour = get_color_by_class_name(raiderio['class'])
            if raiderio['region'].lower() == "us":
                wow_link = f"https://worldofwarcraft.com/en-us/character/{realm_name}/{character_name}"
            else:
                wow_link = f"https://worldofwarcraft.com/en-gb/character/{realm_name}/{character_name}"
            embed.set_author(
                name=f"{raiderio['name']} {raiderio['realm']} - {raiderio['region'].upper()} | {raiderio['race']} {raiderio['active_spec_name']}  {raiderio['class']}",
                icon_url=get_class_icon(raiderio['class']), url=wow_link)
            raid_progression = raiderio['raid_progression']
            embed.add_field(name=_("Progression"),
                            value=_("**EP** : {epprogression} **CoS**: {cosprogression} **BoD** : {bodprogression} **Uldir **: {progression}").format(progression=raid_progression['uldir']['summary'], bodprogression=raid_progression["battle-of-dazaralor"]["summary"], cosprogression=raid_progression["crucible-of-storms"]["summary"], epprogression=raid_progression["the-eternal-palace"]["summary"]),
                            inline=False)
            embed.add_field(name=_("iLVL"),
                            value=f"{raiderio['gear']['item_level_equipped']}/{raiderio['gear']['item_level_total']}",
                            inline=True)
            embed.add_field(name=_("Current Mythic+ Score"), value=raiderio['mythic_plus_scores']['all'], inline=True)
            if "previous_mythic_plus_scores" in raiderio:
                embed.add_field(name=_("Last Mythic+ Season Score"), value=raiderio['previous_mythic_plus_scores']['all'],
                            inline=True)
            best_runs = ""
            for mythicplus_run in raiderio['mythic_plus_best_runs']:
                best_runs += f"[{mythicplus_run['dungeon']} - **"
                if mythicplus_run['num_keystone_upgrades'] == 1:
                    best_runs += "+ "
                elif mythicplus_run['num_keystone_upgrades'] == 2:
                    best_runs += "++ "
                elif mythicplus_run['num_keystone_upgrades'] == 3:
                    best_runs += "+++ "
                seconds, minutes, hour = convertMillis(mythicplus_run['clear_time_ms'])
                best_runs += f"{mythicplus_run['mythic_level']}** {hour}:{minutes}:{seconds}]({mythicplus_run['url']})\n"
            if best_runs:
                embed.add_field(name=_("Best Mythic+ Runs"), value=best_runs, inline=True)
            bnet_request = battlenet_util.execute_battlenet_request(f"https://{region}.api.blizzard.com/wow/character/{realm_name}/{character_name}", params={"fields": "achievements,stats"})
            if bnet_request.ok:
                bnet_json = bnet_request.json()
                mplus_totals = ""
                try:
                    index = bnet_json['achievements']['criteria'].index(33097)
                    mplus_totals += f"**M+5**:{bnet_json['achievements']['criteriaQuantity'][index]}\n"
                except ValueError:
                    pass

                try:
                    index = bnet_json['achievements']['criteria'].index(33098)
                    mplus_totals += f"**M+10**:{bnet_json['achievements']['criteriaQuantity'][index]}\n"
                except ValueError:
                    pass

                try:
                    index = bnet_json['achievements']['criteria'].index(32028)
                    mplus_totals += f"**M+15**:{bnet_json['achievements']['criteriaQuantity'][index]}\n"
                except ValueError:
                    pass
                embed.add_field(name=_("Mythic+ Completed"), value=mplus_totals, inline=True)
                stats = ""
                strength = bnet_json['stats']['str']
                agi = bnet_json['stats']['agi']
                intel = bnet_json['stats']['int']
                if strength > agi and strength > intel:
                    stats += _("**STR**: {strength}").format(strength=strength) + " - "
                elif agi > strength and agi > intel:
                    stats += _("**AGI**: {agility}").format(agility=agi) + " - "
                else:
                    stats += _("**INT**: {intel}").format(intel=intel) + " - "
                stats += _("**Crit**: {percent}% {rating}").format(percent=round(Decimal(bnet_json['stats']['crit']), 2), rating=bnet_json['stats']['critRating']) + "\n"
                stats += _("**Haste**: {percent}% {rating}").format(percent=round(Decimal(bnet_json['stats']['haste']), 2), rating=bnet_json['stats']['hasteRating']) + " - "
                stats += _("**Mastery**: {percent}% {rating}").format(percent=round(Decimal(bnet_json['stats']['mastery']), 2), rating=bnet_json['stats']['masteryRating']) + "\n"
                stats += _("**Versatility**: D:{percent_damage} B:{percent_block} ({rating})").format(percent_damage=round(Decimal(bnet_json['stats']['versatilityDamageDoneBonus']),2), percent_block=round(Decimal(bnet_json['stats']['versatilityDamageTakenBonus']),2), rating=bnet_json['stats']['versatility']) + "\n"
                embed.add_field(name=_("Stats"), value=stats, inline=False)
            embed.add_field(name="WoWProgress",
                            value=_("[Click Here]({url})").format(url=f"https://www.wowprogress.com/character/{region}/{realm_name}/{character_name}"),
                            inline=True)
            embed.add_field(name="Raider.IO",
                            value=_("[Click Here]({url})").format(url=f"https://raider.io/characters/{region}/{realm_name}/{character_name}"),
                            inline=True)
            embed.add_field(name="WarcraftLogs",
                            value=_("[Click Here]({url})").format(url=f"https://www.warcraftlogs.com/character/{region}/{realm_name}/{character_name}"),
                            inline=True)
            embed.set_footer(text=_("Information taken from Raider.IO"))
            await ctx.send(embed=embed)

    @commands.command(aliases=["logs"])
    async def log(self, ctx):
        """
        Retrieve the latest log from WarcraftLogs for your guild.
        """
        # TODO Allow a parameter to give the guild name.
        guild_server = GuildServer.objects.filter(guild_id=ctx.guild.id, default=True).first()
        if not guild_server:
            raise commands.BadArgument(_("The owner of the server needs to configure at least 1 default guild first!"))
        key = os.getenv("WARCRAFTLOGS_KEY")
        wc_request = requests.get(f"https://www.warcraftlogs.com/v1/reports/guild/{guild_server.guild_name}/{guild_server.server_slug}/{guild_server.get_region_display()}", params={"api_key": key})
        if not wc_request.ok:
            await ctx.send(content=_("The guild is not found on WarcraftLogs. Does the guild exist on the website?"))
            return
        wc_json = wc_request.json()
        if wc_json:
            log = wc_json[0]
            embed = Embed()
            embed.title = log["title"]
            embed.url = f"https://www.warcraftlogs.com/reports/{log['id']}"
            embed.set_thumbnail(url=f"https://dmszsuqyoe6y6.cloudfront.net/img/warcraft/zones/zone-{log['zone']}-small.jpg")
            embed.add_field(name=_("Created by"), value=log['owner'], inline=True)
            embed.timestamp = datetime.datetime.utcfromtimestamp(log['start'] / 1000).replace(tzinfo=simple_utc())
            wc_zones = requests.get("https://www.warcraftlogs.com/v1/zones", params={"api_key": key})
            if wc_zones.ok:
                zones_json = wc_zones.json()
                for zone in zones_json:
                    if log['zone'] == zone['id']:
                        embed.add_field(name="Zone", value=zone['name'], inline=True)
            await ctx.send(embed=embed)
        else:
            await ctx.send(_("The guild {guild_name} got no public logs!").format(guild_name=guild_server.guild_name))

    @commands.command(aliases=["iorank", "wprank"])
    async def rank(self, ctx):
        """
        Retrieve your Guild Raider.IO Ranking
        """
        guild_server = GuildServer.objects.filter(guild_id=ctx.guild.id, default=True).first()
        if not guild_server:
            raise commands.BadArgument(_("The owner of the server needs to configure at least 1 default guild first!"))
        query_parameters = {
            "region": guild_server.get_region_display(),
            "realm": guild_server.server_slug,
            "name": guild_server.guild_name,
            "fields": "raid_rankings"
        }
        raiderio_request = requests.get("https://raider.io/api/v1/guilds/profile", params=query_parameters)
        if not raiderio_request.ok:
            await ctx.send(content=_("The guild is not found on Raider.IO. Does the guild exist on the website?"))
            return
        ranking_json = raiderio_request.json()
        raid_rankings = ranking_json['raid_rankings']
        embed = Embed()
        embed.title = _("{guild_name}-{server_name} Raid Rankings").format(guild_name=guild_server.guild_name, server_name=guild_server.server_slug)
        embed.add_field(name=_("Battle of Dazar'alor"), value=self.__format_ranking(raid_rankings['battle-of-dazaralor']), inline=True)
        embed.add_field(name=_("Uldir"), value=self.__format_ranking(raid_rankings['uldir']), inline=True)
        await ctx.send(embed=embed)

    @commands.command()
    async def linkwowchars(self, ctx):
        """
        Let LegendaryBot know your characters.
        """
        await ctx.send(_("To link the bot to your characters, please go to https://legendarybot.info/myself"))


def setup(bot):
    bot.add_cog(WoW(bot))


mythicplus_affix = {
    1: {
        "difficulty": 1,
        "description": _("Healing in excess of a target's maximum health is instead converted to a heal absorption effect."),
    },
    2: {
        "difficulty": 2,
        "description": _("Enemies pay far less attention to threat generated by tanks. 80% Threat reduction."),
    },
    3: {
        "difficulty": 0,
        "description": _("While in combat, enemies periodically cause gouts of flame to erupt beneath the feet of distant players."),
    },
    4: {
        "difficulty": 2,
        "description": _("All enemies' melee attacks apply a stacking blight that inflicts damage over time and reduces healing received."),
    },
    5: {
        "difficulty": 1,
        "description": _("Additional non-boss enemies are present throughout the dungeon."),
    },
    6: {
        "difficulty": 1,
        "description": _("Non-boss enemies enrage at 30% health remaining, dealing 100% increased damage until defeated."),
    },
    7: {
        "difficulty": 1,
        "description": _("When any non-boss enemy dies, its death cry empowers nearby allies, increasing their maximum health and damage by 20%."),
    },
    8: {
        "difficulty": 0,
        "description": _("When slain, non-boss enemies leave behind a lingering pool of ichor that heals their allies and damages players."),
    },
    9: {
        "difficulty": 2,
        "description": _("Boss enemies have 40% more health and inflict up to 15% increased damage."),
    },
    10: {
        "difficulty": 2,
        "description": _("Non-boss enemies have 20% more health and inflict up to 30% increased damage."),
    },
    11: {
        "difficulty": 1,
        "description": _("When slain, non-boss enemies explode, causing all players to suffer 10% of their max health in damage over 4 sec. This effect stacks."),
    },
    12: {
        "difficulty": 1,
        "description": _("When injured below 90% health, players will suffer increasing damage over time until healed above 90% health."),
    },
    13: {
        "difficulty": 1,
        "description": _("While in combat, enemies periodically summon Explosive Orbs that will detonate if not destroyed."),
    },
    14: {
        "difficulty": 1,
        "description": _("Periodically, all players emit a shockwave, inflicting damage and interrupting nearby allies."),
    },
    16: {
        "difficulty": 0,
        "description": _("Some non-boss enemies have been infested with a Spawn of G'huun.")
    }

}

