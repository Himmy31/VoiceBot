from discord.ext import commands

class Cogs(commands.Cog):

    def __init__(self,  bot):
        self.bot = bot
        self.owner_ids = bot.config['owner_ids']

    async def cog_check(self, ctx):
        if ctx.author.id in self.owner_ids:
            return True
        else:
            return False

    @commands.command()
    async def load(self, ctx, extension_name : str):
        try:
            self.bot.load_extension('cogs.'+extension_name)
        except Exception as e:
            return await ctx.send("```py\n{}: {}\n```".format(type(e).__name__, str(e)))
        await ctx.send("{} loaded.".format(extension_name))

    @commands.command()
    async def unload(self, ctx, extension_name : str):
        try:
            self.bot.unload_extension('cogs.'+extension_name)
        except Exception as e:
            return await ctx.send("```py\n{}: {}\n```".format(type(e).__name__, str(e)))
        await ctx.send("{} unloaded.".format(extension_name))
    
    @commands.command()
    async def reload(self, ctx, extension_name : str):
        try:
            self.bot.unload_extension('cogs.'+extension_name)
            self.bot.load_extension('cogs.'+extension_name)
        except Exception as e:
            return await ctx.send("```py\n{}: {}\n```".format(type(e).__name__, str(e)))
        await ctx.send("{} reloaded.".format(extension_name))
