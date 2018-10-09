import asyncio

from influxdb import InfluxDBClient

class Stats:

    def __init__(self, bot):
        self.bot = bot
        self.sleep = 60
        self.command_count = 0
        self.client = InfluxDBClient(database="legendarybot")
        self.bot.loop.create_task(self.recuring_task())

    async def recuring_task(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            guild_count = len(self.bot.guilds)
            user_count = len(self.bot.users)
            voice_connected = len(self.bot.voice_clients)
            latency = self.bot.latency
            json_body = [
                {
                    "measurement": "legendarybot_stats",
                    "fields": {
                        "guild_count": guild_count,
                        "user_count": user_count,
                        "voice_connected": voice_connected,
                        "latency": latency,
                        "command_count": self.command_count
                    }
                }
            ]
            self.command_count = 0
            self.client.write_points(json_body)

            await asyncio.sleep(self.sleep)


def setup(bot):
    bot.add_cog(Stats(bot))