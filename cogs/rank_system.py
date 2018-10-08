import asyncio
import logging
import os

import requests
from discord.ext import commands
from lbwebsite.models import GuildSetting, Character, GuildRank, DiscordGuild
from social_django.models import UserSocialAuth


class RankSystem:

    def __init__(self, bot):
        self.timer = 1800
        self.bot = bot

    def generate_member_rank_map(self, guild):
        guild_ranks = GuildRank.objects.filter(guild=guild.guild).all()
        if guild_ranks:
            #Retrieve from blizzard the information about members in the guilds
            guilds = {}
            #Loop through the ranks to get which's guilds to fetch from blizzard
            for guild_rank in guild_ranks:
                region = guild_rank.wow_guild.get_region_display()
                realm = guild_rank.wow_guild.server_slug
                guild_name = guild_rank.wow_guild.guild_name
                if region not in guilds:
                    guilds[region] = {}
                if realm not in guilds[region]:
                    guilds[region][realm] = {}
                if guild_name not in guilds[region][realm]:
                    guilds[region][realm][guild_name] = {}
                if 'ranks' not in guilds[region][realm][guild_name]:
                    guilds[region][realm][guild_name]['ranks'] = {}
                guilds[region][realm][guild_name]['ranks'][guild_rank.rank_id] = guild_rank.discord_rank

            for region in guilds:
                for realm in guilds[region]:
                    for guild_name in guilds[region][realm]:
                        bnet_request = requests.get(f"https://{region}.api.battle.net/wow/guild/{realm}/{guild_name}",
                                                    params={"fields": "members", "apikey": os.getenv(f"{region}_KEY")})
                        if bnet_request.ok:
                            bnet_json = bnet_request.json()
                            guilds[region][realm][guild_name]["members"] = {}
                            for member in bnet_json['members']:
                                guilds[region][realm][guild_name]["members"][member['character']['name']] = member['rank']
            return guilds
        return None

    def generate_discord_rank_map(self, guild):
        #Retrieve the roles and make a list out of it
        roles = guild.roles

        roles_list = {}
        for role in roles:
            roles_list[role.name] = role
        return roles_list

    def get_user_main_character(self, guild, member):
        user_social = UserSocialAuth.objects.filter(provider='discord', uid=member.id).first()
        if user_social:
            character = Character.objects.filter(user=user_social.user, main_for_guild=guild.id).first()
            if character:
                return character
        return None

    def check_if_bot_can_update_rank(self, discord_guild):
        return discord_guild.me.top_role.permissions.manage_roles

    async def update_user_rank(self, guilds, discord_guild, member):
        roles_list = self.generate_discord_rank_map(discord_guild)
        bot_role = discord_guild.me.top_role
        character = self.get_user_main_character(discord_guild, member)
        if character:
            #We have a main character. Let's find the member from the guild list
            if character.name in guilds[character.get_region_display()][character.server_slug][character.guild_name]["members"]:
                #The user is found in the guild, let's get his rank ID
                rank_id = guilds[character.get_region_display()][character.server_slug][character.guild_name]["members"][character.name]
                discord_rank = guilds[character.get_region_display()][character.server_slug][character.guild_name]['ranks'][rank_id]

                #Search if the role is found in Discord
                if discord_rank in roles_list:
                    #Role found, let's see if the bot can set it
                    if roles_list[discord_rank] < bot_role:
                        #We can set it, remove all roles we can from the user and set this one.
                        member_roles = member.roles
                        roles_to_remove = []
                        already_has_role = False
                        #Loop through the current roles to see which role to remove and if we already have the wanted role
                        for member_role in member_roles:
                            if not member_role.is_default() and member_role < bot_role and member_role != roles_list[discord_rank]:
                                roles_to_remove.append(member_role)
                            if member_role == roles_list[discord_rank]:
                                already_has_role = True
                        if roles_to_remove:
                            await member.remove_roles(*roles_to_remove, reason="LegendaryBot WoW Sync")
                        if not already_has_role:
                            await member.add_roles(roles_list[discord_rank], reason="LegendaryBot WoW Sync")

    async def run_sync(self, guild):
        #Retrieve the Guild from Discord
        discord_guild = self.bot.get_guild(guild.guild.guild_id)
        if discord_guild:
            #Retrieve the rank settings for the guild
            guild_ranks = GuildRank.objects.filter(guild=guild.guild).all()
            #Check if we have any ranks setup
            if guild_ranks:
                member_rank_map = self.generate_member_rank_map(guild)
                #Retrieve LegendaryBot role and check if we can manage permissions
                if self.check_if_bot_can_update_rank(discord_guild):
                    #Retrieve he members
                    members = discord_guild.members
                    for member in members:
                        await self.update_user_rank(member_rank_map,discord_guild, member)

    async def run_user_sync(self, discord_guild, discord_guild_setting, member):
        guild_ranks = GuildRank.objects.filter(guild=discord_guild_setting.guild).all()
        #Check if we have any ranks setup
        if guild_ranks:
            member_rank_map = self.generate_member_rank_map(discord_guild_setting)
            #Retrieve LegendaryBot role and check if we can manage permissions
            if self.check_if_bot_can_update_rank(discord_guild):
                await self.update_user_rank(member_rank_map, discord_guild, member)

    async def background_task(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            #We get all the guilds that have the rank system enabled
            guildrank_enabled_guilds = GuildSetting.objects.filter(setting_name="rank_enabled_loop").all()
            for guild in guildrank_enabled_guilds:
                await self.run_sync(guild)
            await asyncio.sleep(self.timer)


    async def on_ready(self):
        self.bot.loop.create_task(self.background_task())

    @commands.command()
    @commands.guild_only()
    async def syncguild(self, ctx):
        '''
        Sync the Guild ranks with all users
        '''

        setting = GuildSetting.objects.filter(setting_name="rank_enabled", guild=ctx.guild.id).first()
        if setting:
            await self.run_sync(setting)
            await ctx.message.author.send("Guild Rank Sync started. It may take some minutes to apply. Check the server Audit log for any changes.")
        else:
            await ctx.message.author.send("The Rank System is not enabled. Please ask bot author to enable it.")

    @commands.command()
    @commands.guild_only()
    async def sync(self, ctx):
        '''
        Sync your rank on this Discord server.
        '''
        setting = GuildSetting.objects.filter(setting_name="rank_enabled", guild=ctx.guild.id).first()
        if setting:
            await self.run_user_sync(ctx.guild, setting, ctx.author)
            await ctx.message.author.send("Your rank is being synced. It may take some minutes to apply.")
        else:
            await ctx.message.author.send("The Rank System is not enabled. Please ask bot author to enable it.")

    @commands.command()
    async def synchelp(self, ctx):
        '''
        Get information about the Sync system
        '''
        await ctx.message.author.send("The Sync system allows you to have your Discord Rank Synced to your ingame WoW guild rank.\n"
                                      "For Server owners: Go on https://legendarybot.info, go in your server settings and configure the WoW Servers and the WoW Ranks section. \n"
                                      "This feature is still in BETA, which means it needs to be enabled by the bot owner (Greatman). Contact him here: https://discord.gg/Cr7G28H\n"
                                      "For Users: Go on https://legendarybot.info, go in the Myself section and sync your Battle.Net account with the website. Then, select which character is the main character in the discord server you want.")

def setup(bot):
    global logger
    logger = logging.getLogger('rank')
    bot.add_cog(RankSystem(bot))