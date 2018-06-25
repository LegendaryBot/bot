from discord import Embed, Colour, Guild
from discord.ext import commands

from utils import checks


class CommandType(commands.Converter):

    async def convert(self, ctx, argument):
        if argument != "text":
            raise commands.BadArgument("The only valid custom command type are: text")
        return argument


class CustomCommands:

    def __init__(self, bot):
        self.bot = bot

    def get_custom_commands(self, guild: Guild):
        return self.bot.get_guild_setting(guild, 'CUSTOM_COMMANDS')

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            if ctx.guild:
                custom_commands = self.get_custom_commands(ctx.guild)
                if custom_commands and ctx.invoked_with in custom_commands:
                    if custom_commands[ctx.invoked_with]['type'] == "text":
                        await ctx.send(custom_commands[ctx.invoked_with]['text'])

    @commands.group(name="commands", invoke_without_command=True)
    @commands.guild_only()
    async def custom_commands(self, ctx):
        """
        Manage the custom commands of the Discord server.
        This system allows you to create custom commands that the bot will reply with.
        Example: You can create a !ping text command that will reply Pong!
        """
        embed = Embed(title=f"Custom commands for the {ctx.guild.name} server.", colour=Colour.blurple())
        custom_commands = self.get_custom_commands(ctx.guild)
        if custom_commands:
            embed.description = '\n'.join(f'{key}' for key, value in custom_commands)
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
        custom_commands = self.get_custom_commands(ctx.guild)
        if custom_commands:
            custom_commands[command_name] = {
                "type": command_type,
                "text": " ".join(text)
            }
        else:
            custom_commands = {
                command_name: {
                    "type": command_type,
                    "text": " ".join(text)
                }
            }
        self.bot.set_guild_setting(ctx.guild, 'CUSTOM_COMMANDS', custom_commands)
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
        custom_commands = self.bot.get_guild_setting(ctx.guild, 'CUSTOM_COMMANDS')
        if command_name in custom_commands:
            custom_commands.remove(command_name)
            self.bot.set_guild_setting(ctx.guild, 'CUSTOM_COMMANDS', custom_commands)
            await ctx.message.author.send(f"Command {command_name} removed!")
        else:
            await ctx.message.author.send(f"Command {command_name} not found!")


def setup(bot):
    bot.add_cog(CustomCommands(bot))