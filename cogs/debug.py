from discord.ext import commands


class Debug:

    def __init__(self, bot):
        self.bot = bot

    @commands.is_owner()
    @commands.command()
    async def debuguser(self, ctx, user_id):
        output = "Member in the following guilds:\n"
        for guild in self.bot.guilds:
            if guild.get_member(int(user_id)):
                output += f"{guild.id} - {guild.name}\n"
        await ctx.message.author.send(output)


def setup(bot):
    bot.add_cog(Debug(bot))