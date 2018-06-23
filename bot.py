import logging
import os

import discord

logging.basicConfig(level=logging.INFO)

class LegendaryBot(discord.Client):
    async def on_ready(self):
        print('Logged in as %s - %s' % (self.user.name, self.user.id))

    async def on_message(self,message):
        print(message)

client = LegendaryBot()
client.run(os.getenv("BOT_TOKEN"))