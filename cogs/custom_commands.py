from discord import Embed, Colour, Guild
from discord.ext import commands
from lbwebsite.models import GuildCustomCommand

from utils import checks


class CommandType(commands.Converter):

    async def convert(self, ctx, argument):
        if argument != "text":
            raise commands.BadArgument("The only valid custom command type are: text")
        return argument


class CustomCommands:

    def __init__(self, bot):
        self.bot = bot

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
        embed = Embed(title=f"Custom commands for the {ctx.guild.name} server.", colour=Colour.blurple())
        custom_commands = GuildCustomCommand.objects.filter(guild_id=ctx.guild.id).all()
        if custom_commands:
            embed.description = '\n'.join(f'{command.name}' for command in custom_commands)
        else:
            embed.description = 'No custom commands!'
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
            await ctx.message.author.send(f"Command {command_name} updated!")
        else:
            custom_command = GuildCustomCommand(guild_id=ctx.guild.id, name=command_name, type=GuildCustomCommand.TEXT, value=" ".join(text))
            custom_command.save()
            await ctx.message.author.send(f"Command {command_name} created!")

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
            await ctx.message.author.send(f"Command {command_name} removed!")
        else:
            await ctx.message.author.send(f"Command {command_name} not found!")


def setup(bot):
    bot.add_cog(CustomCommands(bot))