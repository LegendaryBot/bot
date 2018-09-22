import asyncio

from discord import Game


class Played:

    def __init__(self, bot):
        self.timer = 60
        self.bot = bot

    async def background_task(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            await self.bot.change_presence(activity=Game(f"on {len(self.bot.guilds)} servers"))
            await asyncio.sleep(self.timer)

    async def on_ready(self):
        self.bot.loop.create_task(self.background_task())


def setup(bot):
    bot.add_cog(Played(bot))