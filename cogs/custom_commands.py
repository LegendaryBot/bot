from discord import Embed, Colour
from discord.ext import commands
from discord.ext.commands import Cog
from lbwebsite.models import GuildCustomCommand

from utils import checks
from utils.translate import _


class CommandType(commands.Converter):

    async def convert(self, ctx, argument):
        if argument != "text":
            raise commands.BadArgument(_("The only valid custom command type are: text"))
        return argument


class CustomCommands(Cog):

    def __init__(self, bot):
        self.bot = bot

    @Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            if ctx.guild:
                custom_command = GuildCustomCommand.objects.filter(guild_id=ctx.guild.id, name=ctx.invoked_with).first()
                if custom_command:
                    await ctx.send(custom_command.value)

    @commands.group(name="commands", invoke_without_command=True)
    @commands.guild_only()
    async def custom_commands(self, ctx):
        """
        Manage the custom commands of the Discord server.
        This system allows you to create custom commands that the bot will reply with.
        Example: You can create a !ping text command that will reply Pong!
        """
        embed = Embed(title=_("Custom commands for the {guild_name} server.").format(guild_name=ctx.guild.name), colour=Colour.blurple())
        custom_commands = GuildCustomCommand.objects.filter(guild_id=ctx.guild.id).all()
        if custom_commands:
            embed.description = '\n'.join(f'{command.name}' for command in custom_commands)
        else:
            embed.description = _('No custom commands!')
        await ctx.message.author.send(embed=embed)

    @custom_commands.command(name="add", rest_is_raw=True)
    @checks.is_bot_admin()
    @commands.guild_only()
    async def add_custom_command(self, ctx, command_name: str, command_type: CommandType, *text: str):
        """
        Add a custom command to the Discord server.
        The only supported command_type currently is "text".

        You must have one of the following to be able to use the command:
        - The legendarybot-admin role.
        - The Manage Server or the Administrator permission.
        """

        custom_command = GuildCustomCommand.objects.filter(guild_id=ctx.guild.id, name=command_name).first()
        if custom_command:
            custom_command.type = GuildCustomCommand.TEXT
            custom_command.value = " ".join(text)
            custom_command.save()
            await ctx.message.author.send(_("Command {command_name} updated!").format(command_name=command_name))
        else:
            custom_command = GuildCustomCommand(guild_id=ctx.guild.id, name=command_name, type=GuildCustomCommand.TEXT, value=" ".join(text))
            custom_command.save()
            await ctx.message.author.send(_("Command {command_name} created!").format(command_name=command_name))

    @custom_commands.command(name="remove")
    @checks.is_bot_admin()
    @commands.guild_only()
    async def remove_custom_command(self, ctx, command_name: str):
        """
        Remove a custom command from a Discord server.
        You must have one of the following to be able to use the command:
        - The legendarybot-admin role.
        - The Manage Server or the Administrator permission.
        """
        custom_command = GuildCustomCommand.objects.filter(guild_id=ctx.guild.id, name=command_name).first()
        if custom_command:
            custom_command.delete()
            await ctx.message.author.send(_("Command {command_name} removed!").format(command_name=command_name))
        else:
            await ctx.message.author.send(_("Command {command_name} not found!").format(command_name=command_name))


def setup(bot):
    bot.add_cog(CustomCommands(bot))