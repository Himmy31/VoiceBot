import discord
from discord.ext import commands
from platform import python_version
import datetime
import traceback
import os
import json

class Bot(commands.Bot):


    def __init__(self):
        super().__init__(max_messages= 100,
                        command_prefix= 'v.',
                        case_insensitive= True)

        self.loaded = False

        self.colors = {"main" : 0x9b59b6, "error" : 0xFF0000}

        with open('config.json', 'r') as fp:
            self.config = json.load(fp)

        self.load()


    def load(self):
        if self.loaded:
            return
        self.remove_command('help')
        self.load_extension('jishaku')
        for filename in os.listdir('./cogs'):
            try:
                self.load_extension(f'cogs.{filename}')
            except Exception as e:
                traceback.print_exception(type(e), e, e.__traceback__)


    async def on_ready(self):
        if self.loaded:
            return

        print(f'Python v{python_version()}')
        print(f'discord.py v{discord.__version__}')
        print(f'Bot account - {self.user}')
        print(f'Guilds: {len(self.guilds)}')

        self.loaded = True

        activity = discord.Activity(name= f"На Margo", type= discord.ActivityType.watching)
        await self.change_presence(status= discord.Status.online, activity= activity)


    async def on_message(self, message: discord.Message):

        if (message.author.bot or not message.guild):
            return

        if not message.channel.permissions_for(message.guild.me).send_messages:
            return

        ctx = await self.get_context(message)
        if (not ctx.valid):
            return

        try:
            await self.invoke(ctx)
        except Exception as e:
            await message.channel.send(f'```py\n{traceback.format_exc()}\n```')
            self.dispatch('command_error', ctx, e)

    def run(self):
        super().run(self.config['token'])

if __name__ == '__main__':
    Bot().run()