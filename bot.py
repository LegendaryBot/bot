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

# Loading the bot
client = LegendaryBotDiscord()
client.run(os.getenv("BOT_TOKEN"))
