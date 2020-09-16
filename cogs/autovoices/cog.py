import discord
import math
import asyncio
import aiohttp
import json
import datetime
from discord.ext import commands
import traceback
import sqlite3
from urllib.parse import quote
import validators
from discord.ext.commands.cooldowns import BucketType
from time import gmtime, strftime

PREFIX = 'v.'

class Cog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        conn = sqlite3.connect('voice.db')
        c = conn.cursor()
        guildID = member.guild.id
        c.execute("SELECT voiceChannelID FROM guild WHERE guildID = ?", (guildID,))
        voice=c.fetchone()
        if voice is None:
            pass
        else:
            voiceID = voice[0]
            try:
                if after.channel.id == voiceID:
                    c.execute("SELECT * FROM voiceChannel WHERE userID = ?", (member.id,))
                    cooldown=c.fetchone()
                    if cooldown is None:
                        pass
                    else:
                        await member.send("Нельзя создавать так часто каналы. Отдохните 5 секунд.")
                        await asyncio.sleep(5)
                    c.execute("SELECT voiceCategoryID FROM guild WHERE guildID = ?", (guildID,))
                    voice=c.fetchone()
                    c.execute("SELECT channelName, channelLimit FROM userSettings WHERE userID = ?", (member.id,))
                    setting=c.fetchone()
                    c.execute("SELECT channelLimit FROM guildSettings WHERE guildID = ?", (guildID,))
                    guildSetting=c.fetchone()
                    if setting is None:
                        name = f"{member.name}'"
                        if guildSetting is None:
                            limit = 0
                        else:
                            limit = guildSetting[0]
                    else:
                        if guildSetting is None:
                            name = setting[0]
                            limit = setting[1]
                        elif guildSetting is not None and setting[1] == 0:
                            name = setting[0]
                            limit = guildSetting[0]
                        else:
                            name = setting[0]
                            limit = setting[1]
                    categoryID = voice[0]
                    id = member.id
                    category = self.bot.get_channel(categoryID)
                    channel2 = await member.guild.create_voice_channel(name,category=category)
                    channelID = channel2.id
                    await member.move_to(channel2)
                    await channel2.set_permissions(self.bot.user, connect=True,read_messages=True)
                    await channel2.edit(name= name, user_limit = limit)
                    c.execute("INSERT INTO voiceChannel VALUES (?, ?)", (id,channelID))
                    conn.commit()
                    def check(a,b,c):
                        return len(channel2.members) == 0
                    await self.bot.wait_for('voice_state_update', check=check)
                    await channel2.delete()
                    await asyncio.sleep(3)
                    c.execute('DELETE FROM voiceChannel WHERE userID=?', (id,))
            except:
                pass
        conn.commit()
        conn.close()

    @commands.command()
    async def help(self, ctx):
        embed = discord.Embed(
            title = 'Команды',
            description = f'`{PREFIX}lock` - Закрыть свой голосовой канал\n' 
            f'`{PREFIX}unlock` - Открыт свой голосовой канал\n' 
            f'`{PREFIX}name` name - Изменить имя голосовому каналу\n' 
            f'`{PREFIX}limit` number - Изменить количество участников\n' 
            f'`{PREFIX}permit` @Name - Передать права канала\n'
            f'`{PREFIX}reject` @Name - Выгнать пользователя из голосового канал\n'
            f'`{PREFIX}claim` - Заявить свои права на голосовой канал',
            color = 0x2f3136)
        await ctx.send(embed = embed)

    @commands.command()
    async def setup(self, ctx):
        conn = sqlite3.connect('voice.db')
        c = conn.cursor()
        guildID = ctx.guild.id
        id = ctx.author.id
        if ctx.author.id == ctx.guild.owner.id or ctx.author.id == 151028268856770560:
            def check(m):
                return m.author.id == ctx.author.id
            embed = discord.Embed(
                description = 'У вас есть 60 секунд, чтобы ответить на каждый вопрос!',
                color = 0x2f3136)
            await ctx.channel.send(embed = embed, delete_after = 20)
            embed = discord.Embed(
                description = 'Введите название категории, в которой вы хотите создать каналы\n'
                'Например: **Приватные каналы**',
                color = 0x2f3136)
            await ctx.channel.send(embed = embed, delete_after = 60)
            try:
                category = await self.bot.wait_for('message', check=check, timeout = 60.0)
            except asyncio.TimeoutError:
                embed = discord.Embed(
                    title = 'Упс...',
                    description = 'Вы слишком долго отвечали...',
                    color = 0xFF0000)
                await ctx.channel.send(embed = embed, delete_after = 15)
            else:
                new_cat = await ctx.guild.create_category_channel(category.content)
                embed = discord.Embed(
                    description = 'Введите название канала, в которой должны заходить пользователи для создания канала\n'
                    'Например: **Создать приват**')
                await ctx.channel.send(embed = embed, delete_after = 60)
                try:
                    channel = await self.bot.wait_for('message', check=check, timeout = 60.0)
                except asyncio.TimeoutError:
                    embed = discord.Embed(
                        title = 'Упс...',
                        description = 'Вы слишком долго отвечали...',
                        color = 0xFF0000)
                    await ctx.channel.send(embed = embed, delete_after = 15)
                else:
                    try:
                        channel = await ctx.guild.create_voice_channel(channel.content, category=new_cat)
                        c.execute("SELECT * FROM guild WHERE guildID = ? AND ownerID=?", (guildID, id))
                        voice=c.fetchone()
                        if voice is None:
                            c.execute ("INSERT INTO guild VALUES (?, ?, ?, ?)",(guildID,id,channel.id,new_cat.id))
                        else:
                            c.execute ("UPDATE guild SET guildID = ?, ownerID = ?, voiceChannelID = ?, voiceCategoryID = ? WHERE guildID = ?",(guildID,id,channel.id,new_cat.id, guildID))
                        await ctx.channel.send("**You are all setup and ready to go!**")
                    except:
                        embed = discord.Embed(
                            title = 'Ошибка',
                            description = f'Воспользуйтесь снова командой {PREFIX}setup \n'
                            'Если ошибка повториться, свяжитесь с  <@750309318905036881>',
                            color = 0xFF0000)
                        await ctx.channel.send(embed = embed, delete_after = 15)
        else:
            embed = discord.Embed(
                description = 'Только владелец сервера может воспользоваться ботом.',
                color = 0xFF0000)
            await ctx.channel.send(embed = embed, delete_after = 15)
        conn.commit()
        conn.close()
    @commands.command()
    async def setlimit(self, ctx, num):
        conn = sqlite3.connect('voice.db')
        c = conn.cursor()
        if ctx.author.id == ctx.guild.owner.id or ctx.author.id == 151028268856770560:
            c.execute("SELECT * FROM guildSettings WHERE guildID = ?", (ctx.guild.id,))
            voice=c.fetchone()
            if voice is None:
                c.execute("INSERT INTO guildSettings VALUES (?, ?, ?)", (ctx.guild.id,f"{ctx.author.name}'s channel",num))
            else:
                c.execute("UPDATE guildSettings SET channelLimit = ? WHERE guildID = ?", (num, ctx.guild.id))
            await ctx.send("You have changed the default channel limit for your server!")
        else:
            await ctx.channel.send(f"{ctx.author.mention} only the owner of the server can setup the bot!")
        conn.commit()
        conn.close()

    @setup.error
    async def info_error(self, ctx, error):
        print(error)

    @commands.command()
    async def lock(self, ctx):
        conn = sqlite3.connect('voice.db')
        c = conn.cursor()
        id = ctx.author.id
        c.execute("SELECT voiceID FROM voiceChannel WHERE userID = ?", (id,))
        voice=c.fetchone()
        if voice is None:
            await ctx.channel.send(f"{ctx.author.mention} You don't own a channel.")
        else:
            channelID = voice[0]
            role = discord.utils.get(ctx.guild.roles, name='@everyone')
            channel = self.bot.get_channel(channelID)
            await channel.set_permissions(role, connect=False,read_messages=True)
            await ctx.channel.send(f'{ctx.author.mention} Voice chat locked! 🔒')
        conn.commit()
        conn.close()

    @commands.command()
    async def unlock(self, ctx):
        conn = sqlite3.connect('voice.db')
        c = conn.cursor()
        id = ctx.author.id
        c.execute("SELECT voiceID FROM voiceChannel WHERE userID = ?", (id,))
        voice=c.fetchone()
        if voice is None:
            await ctx.channel.send(f"{ctx.author.mention} You don't own a channel.")
        else:
            channelID = voice[0]
            role = discord.utils.get(ctx.guild.roles, name='@everyone')
            channel = self.bot.get_channel(channelID)
            await channel.set_permissions(role, connect=True,read_messages=True)
            await ctx.channel.send(f'{ctx.author.mention} Voice chat unlocked! 🔓')
        conn.commit()
        conn.close()

    @commands.command(aliases=["allow"])
    async def permit(self, ctx, member : discord.Member):
        conn = sqlite3.connect('voice.db')
        c = conn.cursor()
        id = ctx.author.id
        c.execute("SELECT voiceID FROM voiceChannel WHERE userID = ?", (id,))
        voice=c.fetchone()
        if voice is None:
            await ctx.channel.send(f"{ctx.author.mention} You don't own a channel.")
        else:
            channelID = voice[0]
            channel = self.bot.get_channel(channelID)
            await channel.set_permissions(member, connect=True)
            await ctx.channel.send(f'{ctx.author.mention} You have permited {member.name} to have access to the channel. ✅')
        conn.commit()
        conn.close()

    @commands.command(aliases=["deny"])
    async def reject(self, ctx, member : discord.Member):
        conn = sqlite3.connect('voice.db')
        c = conn.cursor()
        id = ctx.author.id
        guildID = ctx.guild.id
        c.execute("SELECT voiceID FROM voiceChannel WHERE userID = ?", (id,))
        voice=c.fetchone()
        if voice is None:
            await ctx.channel.send(f"{ctx.author.mention} You don't own a channel.")
        else:
            channelID = voice[0]
            channel = self.bot.get_channel(channelID)
            for members in channel.members:
                if members.id == member.id:
                    c.execute("SELECT voiceChannelID FROM guild WHERE guildID = ?", (guildID,))
                    voice=c.fetchone()
                    channel2 = self.bot.get_channel(voice[0])
                    await member.move_to(channel2)
            await channel.set_permissions(member, connect=False,read_messages=True)
            await ctx.channel.send(f'{ctx.author.mention} You have rejected {member.name} from accessing the channel. ❌')
        conn.commit()
        conn.close()



    @commands.command()
    async def limit(self, ctx, limit):
        conn = sqlite3.connect('voice.db')
        c = conn.cursor()
        id = ctx.author.id
        c.execute("SELECT voiceID FROM voiceChannel WHERE userID = ?", (id,))
        voice=c.fetchone()
        if voice is None:
            await ctx.channel.send(f"{ctx.author.mention} You don't own a channel.")
        else:
            channelID = voice[0]
            channel = self.bot.get_channel(channelID)
            await channel.edit(user_limit = limit)
            await ctx.channel.send(f'{ctx.author.mention} You have set the channel limit to be '+ '{}!'.format(limit))
            c.execute("SELECT channelName FROM userSettings WHERE userID = ?", (id,))
            voice=c.fetchone()
            if voice is None:
                c.execute("INSERT INTO userSettings VALUES (?, ?, ?)", (id,f'{ctx.author.name}',limit))
            else:
                c.execute("UPDATE userSettings SET channelLimit = ? WHERE userID = ?", (limit, id))
        conn.commit()
        conn.close()


    @commands.command()
    async def name(self, ctx,*, name):
        conn = sqlite3.connect('voice.db')
        c = conn.cursor()
        id = ctx.author.id
        c.execute("SELECT voiceID FROM voiceChannel WHERE userID = ?", (id,))
        voice=c.fetchone()
        if voice is None:
            await ctx.channel.send(f"{ctx.author.mention} You don't own a channel.")
        else:
            channelID = voice[0]
            channel = self.bot.get_channel(channelID)
            await channel.edit(name = name)
            await ctx.channel.send(f'{ctx.author.mention} You have changed the channel name to '+ '{}!'.format(name))
            c.execute("SELECT channelName FROM userSettings WHERE userID = ?", (id,))
            voice=c.fetchone()
            if voice is None:
                c.execute("INSERT INTO userSettings VALUES (?, ?, ?)", (id,name,0))
            else:
                c.execute("UPDATE userSettings SET channelName = ? WHERE userID = ?", (name, id))
        conn.commit()
        conn.close()

    @commands.command()
    async def claim(self, ctx):
        x = False
        conn = sqlite3.connect('voice.db')
        c = conn.cursor()
        channel = ctx.author.voice.channel
        if channel == None:
            await ctx.channel.send(f"{ctx.author.mention} you're not in a voice channel.")
        else:
            id = ctx.author.id
            c.execute("SELECT userID FROM voiceChannel WHERE voiceID = ?", (channel.id,))
            voice=c.fetchone()
            if voice is None:
                await ctx.channel.send(f"{ctx.author.mention} You can't own that channel!")
            else:
                for data in channel.members:
                    if data.id == voice[0]:
                        owner = ctx.guild.get_member(voice [0])
                        await ctx.channel.send(f"{ctx.author.mention} This channel is already owned by {owner.mention}!")
                        x = True
                if x == False:
                    await ctx.channel.send(f"{ctx.author.mention} You are now the owner of the channel!")
                    c.execute("UPDATE voiceChannel SET userID = ? WHERE voiceID = ?", (id, channel.id))
            conn.commit()
            conn.close()
