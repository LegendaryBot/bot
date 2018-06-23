import logging
import os

from discord.ext import commands

logging.basicConfig(level=logging.INFO)

initial_extensions = {
    "cogs.token"
}

class LegendaryBot(commands.AutoShardedBot):

    def __init__(self):
        super().__init__(command_prefix="!", pm_help=True)
        for cog in initial_extensions:
            self.load_extension(cog)

    async def on_ready(self):
        print('Logged in as %s - %s' % (self.user.name, self.user.id))


client = LegendaryBot()
client.run(os.getenv("BOT_TOKEN"))