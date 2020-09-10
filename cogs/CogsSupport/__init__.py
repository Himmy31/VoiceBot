from .cog import Cogs

def setup(bot):
    bot.add_cog(Cogs(bot))
