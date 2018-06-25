from discord.ext import commands
from discord.ext.commands import has_role


async def check_guild_permissions(ctx, perms, *, check=all):
    is_owner = await ctx.bot.is_owner(ctx.author)
    if is_owner:
        return True

    if ctx.guild is None:
        return False

    resolved = ctx.author.guild_permissions
    return check(getattr(resolved, name, None) == value for name, value in perms.items())


def is_bot_admin():
    async def pred(ctx):
        return await check_guild_permissions(ctx, {'manage_guild': True, 'administrator': True}) or has_role('legendarybot-admin')
    return commands.check(pred)