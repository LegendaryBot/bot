import decimal
import json
import logging
import os
import sys
import traceback

import boto3
import django
from slugify import slugify

from dotenv import load_dotenv
load_dotenv()

os.environ['DJANGO_SETTINGS_MODULE']='legendarybot.settings'
django.setup()

from discord.ext import commands
from lbwebsite.models import DiscordGuild, GuildPrefix, GuildServer, GuildCustomCommand

logging.basicConfig(level=logging.INFO)


initial_extensions = {
    "cogs.worldofwarcraft",
    "cogs.meta",
    "cogs.custom_commands",
    "cogs.fun",
    "cogs.played",
    "cogs.botlist"
}


def _prefix_callable(bot, msg):
    user_id = bot.user.id
    base = [f'<@!{user_id}> ', f'<@{user_id}> ']
    if msg.guild is None:
        base.append("!")
    try:
        if msg.guild:
            guild = DiscordGuild.objects.get(pk=msg.guild.id)
            for prefix in guild.guildprefix_set.all():
                base.append(prefix.prefix)
            if base.__len__() == 2:
                base.append("!")
    except DiscordGuild.DoesNotExist:
        base.append("!")
    return base


class LegendaryBotDiscord(commands.AutoShardedBot):

    def __init__(self):
        super().__init__(command_prefix=_prefix_callable, pm_help=True)
        for cog in initial_extensions:
            print("Loading %s" % cog)
            self.load_extension(cog)

    async def on_ready(self):
        print('Logged in as %s - %s' % (self.user.name, self.user.id))

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.NoPrivateMessage):
            await ctx.author.send('This command cannot be used in private messages.')
        elif isinstance(error, commands.DisabledCommand):
            await ctx.author.send('Sorry. This command is disabled and cannot be used.')
        elif isinstance(error, commands.BadArgument) or isinstance(error, commands.MissingRequiredArgument):
            await ctx.author.send(error)
        else:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, error, exc_traceback)



#Importer from old data
# Helper class to convert a DynamoDB item to JSON.
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table("LegendaryBot_discordGuild-prod")
response = table.scan()
for i in response['Items']:
    json_str = json.dumps(i, cls=DecimalEncoder)
    resp_dict = json.loads(json_str)
    try:
        guild = DiscordGuild.objects.get(pk=resp_dict['id'])
    except DiscordGuild.DoesNotExist:
        guild = DiscordGuild(pk=resp_dict['id'])
        guild.save()
    prefix = None
    if "settings" in resp_dict['json']:
        if "PREFIX" in resp_dict['json']['settings']:
            print(resp_dict['json']['settings']['PREFIX'])
            prefix = resp_dict['json']['settings']['PREFIX']
        elif "prefix" in resp_dict['json']['settings']:
            print(resp_dict['json']['settings']['prefix'])
            prefix = resp_dict['json']['settings']['prefix']
        if prefix:
            if prefix == "!help":
                prefix = "!"
            if prefix is not "!" and len(prefix) < 10:
                prefix_entry = GuildPrefix(guild=guild, prefix=prefix)
                prefix_entry.save()

        if "GUILD_NAME" in resp_dict['json']['settings'] and "WOW_REGION_NAME" in resp_dict['json']['settings'] and "WOW_SERVER_NAME" in resp_dict['json']['settings']:
            if resp_dict['json']['settings']['WOW_REGION_NAME'] == "US" or resp_dict['json']['settings']['WOW_REGION_NAME'] == "us":
                GuildServer(guild=guild, region=GuildServer.US, server_slug=slugify(resp_dict['json']['settings']['WOW_SERVER_NAME']), guild_name=resp_dict['json']['settings']['GUILD_NAME'], default=True).save()
            elif resp_dict['json']['settings']['WOW_REGION_NAME'] == "EU" or resp_dict['json']['settings']['WOW_REGION_NAME'] == "eu":
                GuildServer(guild=guild, region=GuildServer.EU, server_slug=slugify(resp_dict['json']['settings']['WOW_SERVER_NAME']), guild_name=resp_dict['json']['settings']['GUILD_NAME'], default=True).save()

        if "customCommands" in resp_dict['json']['settings']:
            for command in resp_dict['json']['settings']['customCommands']:
                txt = resp_dict['json']['settings']['customCommands'][command]['value']
                GuildCustomCommand(guild=guild, name=command, type=GuildCustomCommand.TEXT, value=txt).save()

# Loading the bot
client = LegendaryBotDiscord()
client.run(os.getenv("BOT_TOKEN"))
