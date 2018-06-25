import json
import logging
import os
import sys
import traceback

from discord.ext import commands
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

logging.basicConfig(level=logging.INFO)

initial_extensions = {
    "cogs.worldofwarcraft",
    "cogs.meta",
    "cogs.custom_commands"
}


def _prefix_callable(bot, msg):
    user_id = bot.user.id
    base = [f'<@!{user_id}> ', f'<@{user_id}> ']
    if msg.guild is None:
        base.append("!")
    prefixes = bot.get_guild_setting(msg.guild, 'prefixes')
    if prefixes:
        base.extend(prefixes)
    elif msg.guild:
        base.append("!")
    return base


# SQL Init
engine = create_engine('sqlite:///:memory:')
Base = declarative_base()


class Guild(Base):
    __tablename__ = 'guild'

    id = Column(Integer, primary_key=True)
    json = Column(String)

    def __repr__(self):
        return "<Guild(id='%s', json='%s'>" % (self.id, self.json)


Base.metadata.create_all(engine)
session = sessionmaker(bind=engine)()


class LegendaryBot(commands.AutoShardedBot):

    def __init__(self):
        super().__init__(command_prefix=_prefix_callable, pm_help=True)
        for cog in initial_extensions:
            print("Loading %s" % cog)
            self.load_extension(cog)

    async def on_ready(self):
        print('Logged in as %s - %s' % (self.user.name, self.user.id))

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.NoPrivateMessage):
            await ctx.author.send('This command cannot be used in private messages.')
        elif isinstance(error, commands.DisabledCommand):
            await ctx.author.send('Sorry. This command is disabled and cannot be used.')
        elif isinstance(error, commands.BadArgument):
            await ctx.author.send(error)
        else:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, error, exc_traceback)

    def add_guild_prefix(self, guild: Guild, prefix: str):
        """
        Add a prefix to the Guild
        :param guild: (Guild) A instance of a Discord Guild
        :param prefix: (str) The prefix to add.
        :return: None
        """
        prefixes = self.get_guild_setting(guild, 'prefixes')
        if prefixes:
            if prefix not in prefixes:
                prefixes.append(prefix)
                self.set_guild_setting(guild, 'prefixes', prefixes)
                return True
        else:
            prefixes = [prefix]
            self.set_guild_setting(guild, 'prefixes', prefixes)
            return True
        return False

    def remove_guild_prefix(self, guild: Guild, prefix: str):
        """
        Remove a prefix from a discord Guild
        :param guild: (Guild) A instance of a Discord Guild
        :param prefix: (str) The prefix to remove.
        :return: True if the prefix exists and is removed. Else false
        """
        prefixes = self.get_guild_setting(guild.id, 'prefixes')
        if prefix in prefixes:
            prefixes.remove(prefix)
            self.set_guild_setting(guild, 'prefixes', prefixes)
            return True
        return False

    def get_guild_setting(self, guild: Guild, setting_key: str, default_value = None):
        """
        Retrieve the setting of a Guild
        :param guild: (Guild) A instance of a Discord Guild
        :param setting_key: (str) The key to retrieve
        :param default_value: The value to return when no value is found in the database
        :return: A JSON value (Can be object, Array, etc.) or None if the setting is not found.
        """
        if guild is not None:
            guild_database = session.query(Guild).filter_by(id=guild.id).first()
            if guild_database:
                guild_json = json.loads(guild_database.json)
                if setting_key in guild_json:
                    return guild_json[setting_key]
        return default_value

    def set_guild_setting(self, guild: Guild, setting_key: str, value: dict):
        """
        Set a guild setting
        :param guild: The guild object
        :param setting_key: The setting key
        :param value: A Python dict
        :return: None
        """
        guild_database = session.query(Guild).filter_by(id=guild.id).first()
        if guild_database:
            guild_json = json.loads(guild_database.json)
            guild_json[setting_key] = value
            guild_database.json = json.dumps(guild_json)
            session.commit()
        else:
            guild_json = {
                setting_key: value
            }
            guild_database = Guild()
            guild_database.id = guild.id
            guild_database.json = json.dumps(guild_json)
            session.add(guild_database)
            session.commit()


# Loading the bot
client = LegendaryBot()
client.run(os.getenv("BOT_TOKEN"))
