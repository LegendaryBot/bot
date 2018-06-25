from discord import Embed, Colour
from discord.ext import commands

from utils import checks


class Prefix(commands.Converter):
    async def convert(self, ctx, argument):
        user_id = ctx.bot.user.id
        if argument.startswith((f'<@{user_id}>', f'<@!{user_id}>')):
            raise commands.BadArgument('That is a reserved prefix already in use.')
        return argument


class Meta:

    def __init__(self, bot):
        self.bot = bot

    @commands.group(name='prefix', invoke_without_commands=True)
    @commands.guild_only()
    async def prefix(self, ctx):
        """Manages the Guild's custom prefixes.
        If called without a subcommand, this will list the currently set prefixes."""
        prefixes = self.bot.get_guild_setting(ctx.guild, 'prefixes')
        embed = Embed(title='LegendaryBot prefixes configured.', colour=Colour.blurple())
        if prefixes:
            embed.description = '\n'.join(f'{prefix}' for prefix in prefixes)
        else:
            embed.description = "No prefixes set."
        await ctx.message.author.send(embed=embed)

    @prefix.command(name='add')
    @checks.is_bot_admin()
    @commands.guild_only()
    async def prefix_add(self, ctx, prefix: Prefix):
        """
        Add a prefix to the list of custom prefixes for this Discord server.

        Previously set prefixes are not overridden.

        You must have one of the following to be able to use the command:
        - The legendarybot-admin role.
        - The Manage Server or the Administrator permission.
        """
        if self.bot.add_guild_prefix(ctx.guild, prefix):
            await ctx.send(f"Prefix {prefix} added to the server.")
        else:
            await ctx.send(f"Prefix {prefix} not set. Already existing.")

    @prefix.command(name='remove')
    @checks.is_bot_admin()
    @commands.guild_only()
    async def prefix_remove(self, ctx, prefix: Prefix):
        """
        Remove a prefix from the list of custom prefixes for this Discord server.

        You must have one of the following to be able to use the command:
        - The legendarybot-admin role.
        - The Manage Server or the Administrator permission.
        """
        if self.bot.remove_guild_prefix(ctx.guild, prefix):
            await ctx.send(f"Prefix {prefix} removed from the server")
        else:
            await ctx.send(f"Prefix {prefix} does not exist.")


def setup(bot):
    bot.add_cog(Meta(bot))
