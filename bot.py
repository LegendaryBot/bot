import logging
import os
import sys
import traceback
from logging.handlers import SysLogHandler

import django
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
load_dotenv()

syslog = SysLogHandler(address=(os.getenv("PAPERTRAIL_HOST"), int(os.getenv("PAPERTRAIL_PORT"))))
format = '%(asctime)s LEGENDARYBOT: %(levelname)s %(message)s'
formatter = logging.Formatter(format, datefmt='%b %d %H:%M:%S')
syslog.setFormatter(formatter)
logging.getLogger().addHandler(syslog)
logging.getLogger().setLevel(logging.INFO)

os.environ['DJANGO_SETTINGS_MODULE']='legendarybot.settings'
django.setup()

from discord.ext import commands
from lbwebsite.models import DiscordGuild




initial_extensions = {
    "cogs.worldofwarcraft",
    "cogs.meta",
    "cogs.custom_commands",
    "cogs.fun",
    "cogs.played",
    "cogs.botlist",
    "cogs.rank_system",
    "cogs.debug",
    "cogs.music",
    "cogs.stats"
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
            logging.info(f"Loading {cog}")
            self.load_extension(cog)

    async def on_ready(self):
        logging.info(f"Logged in as {self.user.name} - {self.user.id}")

    async def on_command(self, ctx):
        self.get_cog("Stats").command_count += 1
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
