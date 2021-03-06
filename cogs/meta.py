from discord import Embed, Colour
from discord.ext import commands
from discord.ext.commands import Cog
from lbwebsite.models import GuildPrefix

from utils import checks
from utils.translate import _

class Prefix(commands.Converter):
    async def convert(self, ctx, argument):
        user_id = ctx.bot.user.id
        if argument.startswith((f'<@{user_id}>', f'<@!{user_id}>')):
            raise commands.BadArgument('That is a reserved prefix already in use.')
        return argument


class Meta(Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.group(name='prefix', invoke_without_command=True)
    @commands.guild_only()
    async def prefix(self, ctx):
        """Manages the Guild's custom prefixes.
        If called without a subcommand, this will list the currently set prefixes.
        """
        prefixes = GuildPrefix.objects.filter(guild_id=ctx.guild.id).all()
        embed = Embed(title=_('LegendaryBot prefixes configured.'), colour=Colour.blurple())
        if prefixes:
            embed.description = '\n'.join(f'{prefix.prefix}' for prefix in prefixes)
        else:
            embed.description = _("No prefixes set.")
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
        prefix_entry = GuildPrefix.objects.filter(guild_id=ctx.guild.id, prefix=prefix).first()
        if not prefix_entry:
            prefix_entry = GuildPrefix(guild_id=ctx.guild.id, prefix=prefix)
            prefix_entry.save()
            await ctx.send(_("Prefix {prefix} added to the server.").format(prefix=prefix))
        else:
            await ctx.send(_("Prefix {prefix} not set. Already existing.").format(prefix=prefix))

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
        prefix_entry = GuildPrefix.objects.filter(guild_id=ctx.guild.id, prefix=prefix).first()
        if prefix_entry:
            prefix_entry.delete()
            await ctx.send(_("Prefix {prefix} removed from the server").format(prefix=prefix))
        else:
            await ctx.send(_("Prefix {prefix} does not exist.").format(prefix=prefix))

    @commands.command()
    async def info(self, ctx):
        """
        Get information about the bot.
        """
        embed = Embed(title=_("LegendaryBot"))
        embed.set_author(name="Greatman", url="https://github.com/LegendaryBot/bot", icon_url="https://avatars3.githubusercontent.com/u/95754?v=3&s=460")
        embed.description = _("Created using Discord.py. Type @LegendaryBot help to show all the commands.")
        await ctx.send(embed=embed)

    @commands.command()
    async def invite(self, ctx):
        """
        Get the bot invite link
        """
        await ctx.send(_("To invite LegendaryBot to your server. Click this link: <{link}>").format(link="https://discordapp.com/oauth2/authorize?client_id=267134720700186626&scope=bot&permissions=3165248"))


def setup(bot):
    bot.add_cog(Meta(bot))
