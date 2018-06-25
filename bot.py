import json
import logging
import os

from discord.ext import commands
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

logging.basicConfig(level=logging.INFO)

initial_extensions = {
    "cogs.token",
    "cogs.meta"
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
    print(base)
    return base


# SQL Init
engine = create_engine('sqlite:///:memory:', echo=True)
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

    def add_guild_prefix(self, guild, prefix):
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

    def remove_guild_prefix(self, guild, prefix):
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

    def get_guild_setting(self, guild, setting_key):
        """
        Retrieve the setting of a Guild
        :param guild: (Guild) A instance of a Discord Guild
        :param setting_key: (str) The key to retrieve
        :return: A JSON value (Can be object, Array, etc.) or None if the setting is not found.
        """
        if guild is None:
            return None
        guild = session.query(Guild).filter_by(id=guild.id).first()
        if guild:
            guild_json = json.loads(guild.json)
            if setting_key in guild_json:
                return guild_json[setting_key]

    def set_guild_setting(self, guild, setting_key, value):
        """
        Set a guild setting
        :param guild: The guild object
        :param setting_key: The setting key
        :param value: A Python dict
        :return: None
        """
        guild = session.query(Guild).filter_by(id=guild.id).first()
        if guild:
            guild_json = json.loads(guild.json)
            guild_json[setting_key] = value
            guild.json = json.dumps(guild_json)
            session.commit()
        else:
            guild_json = {
                setting_key: value
            }
            guild = Guild()
            guild.id = guild.id
            guild.json = json.dumps(guild_json)
            session.add(guild)
            session.commit()


guild_settings = {
    "prefix": ["??"]
}
guild_temp = Guild(id=214483665311236096, json=json.dumps(guild_settings))
session.add(guild_temp)
# Loading the bot
client = LegendaryBot()
client.run(os.getenv("BOT_TOKEN"))
