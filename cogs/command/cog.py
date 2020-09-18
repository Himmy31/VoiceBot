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
from typing import Optional


PREFIX = 'v.'

class Cog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def help(self, ctx):
        embed = discord.Embed(
            title = 'Команды',
            description = f'`{PREFIX}lock` - Закрыть свой голосовой канал\n' 
            f'`{PREFIX}unlock` - Открыт свой голосовой канал\n' 
            f'`{PREFIX}name` name - Изменить имя голосовому каналу\n' 
            f'`{PREFIX}limit` number - Изменить количество участников\n' 
            f'`{PREFIX}inv` @Name - Окрыть достпу к каналу\n'
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
                    'Например: **Создать приват**',
                    color = 0x2f3136)
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
                        embed = discord.Embed(
                            title = '^^',
                            description = 'Каналы успешно созданы, и я готов к работе',
                            color = 0x2f3136)
                        await ctx.channel.send(embed = embed, delete_after = 15)
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
            embed = discord.Embed(
                description = 'Вы установили стандартый лимит входа в канал по всему серверу',
                color = 0x2f3136)
            await ctx.send(embed = embed, delete_after = 15)
        else:
            embed = discord.Embed(
                description = f'{ctx.author.mention}, только владелец сервера может установить лимит.',
                color = 0x2f3136)
            await ctx.channel.send(embed = embed, delete_after = 15)
        conn.commit()
        conn.close()

    @setup.error
    async def info_error(self, ctx, error):
        print(error)

    @commands.command()
    async def lock(self, ctx, role: Optional[discord.Role] = None, member: Optional[discord.Member] = None):
        await ctx.message.delete()
        conn = sqlite3.connect('voice.db')
        c = conn.cursor()
        id = ctx.author.id
        c.execute("SELECT voiceID FROM voiceChannel WHERE userID = ?", (id,))
        voice=c.fetchone()
        overwrite = discord.PermissionOverwrite(connect = False)
        overwrite.send_messages = False        
        if voice is None:
            embed = discord.Embed(
                description = f'<a:Deny:756507558625149041> **{PREFIX}lock Участник / Роль**',
                color = 0xFF0000)
            embed.set_footer(text = 'Вы не владелец этого канала')
            await ctx.channel.send(embed = embed, delete_after = 20)
        if role:
            channelID = voice[0]
            channel = self.bot.get_channel(channelID)
            await channel.set_permissions(role, overwrite = overwrite)
            embed = discord.Embed(
                description = f'🔒 Приватный канал успешно закрыт для {role.mention}',
                color = 0x2f3136)
            await ctx.channel.send(embed = embed)
        if member:
            channelID = voice[0]
            channel = self.bot.get_channel(channelID)
            await channel.set_permissions(member, overwrite = overwrite)
            embed = discord.Embed(
                description = f'🔒 Приватный канал успешно закрыт для {member.mention}',
                color = 0x2f3136)
            await ctx.channel.send(embed = embed)
        else:
            if role is None:
                channelID = voice[0]
                role = discord.utils.get(ctx.guild.roles, name = '@everyone')
                channel = self.bot.get_channel(channelID)
                await channel.set_permissions(role, overwrite = overwrite)
                embed = discord.Embed(
                    description = f'🔒 Приватный канал успешно закрыт',
                    color = 0x2f3136)
                await ctx.channel.send(embed = embed)
            
        conn.commit()
        conn.close()

    @commands.command(aliases = ['открыть'] )
    async def unlock(self, ctx, role: Optional[discord.Role] = None, member: Optional[discord.Member] = None):
        await ctx.message.delete()
        conn = sqlite3.connect('voice.db')
        c = conn.cursor()
        id = ctx.author.id
        c.execute("SELECT voiceID FROM voiceChannel WHERE userID = ?", (id,))
        voice=c.fetchone()
        overwrite = discord.PermissionOverwrite(connect = True)
        overwrite.send_messages = False        
        if voice is None:
            embed = discord.Embed(
                description = f'<a:Deny:756507558625149041> **{PREFIX}lock Участник / Роль**',
                color = 0xFF0000)
            embed.set_footer(text = 'Вы не владелец этого канала')
        if role:
            channelID = voice[0]
            channel = self.bot.get_channel(channelID)
            await channel.set_permissions(role, overwrite = overwrite)
            embed = discord.Embed(
                description = f'🔓 Приватный канал успешно закрыт для {role.mention}',
                color = 0x2f3136)
            await ctx.channel.send(embed = embed)
        if member:
            channelID = voice[0]
            channel = self.bot.get_channel(channelID)
            await channel.set_permissions(member, overwrite = overwrite)
            embed = discord.Embed(
                description = f'🔓 Приватный канал успешно закрыт для {member.mention}',
                color = 0x2f3136)
            await ctx.channel.send(embed = embed)
        else:
            if role is None:
                channelID = voice[0]
                role = discord.utils.get(ctx.guild.roles, name = '@everyone')
                channel = self.bot.get_channel(channelID)
                await channel.set_permissions(role, overwrite = overwrite)
                embed = discord.Embed(
                    description = f'🔓 Приватный канал успешно закрыт',
                    color = 0x2f3136)
                await ctx.channel.send(embed = embed)
            
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
            embed = discord.Embed(
                description = f'{ctx.author.mention}, вы не владелец данного канала',
                color = 0xFF0000)
            await ctx.channel.send(embed = embed, delete_after = 20)
        else:
            channelID = voice[0]
            channel = self.bot.get_channel(channelID)
            await channel.edit(user_limit = limit)
            embed = discord.Embed(
                description = f'{ctx.author.mention}, установил лимит на канал в количестви' + '{}'.format(limit),
                color = 0x2f3136)
            await ctx.channel.send(embed = embed)
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
            embed = discord.Embed(
                description = f'{ctx.author.mention}, вы не владелец данного канала',
                color = 0xFF0000)
            await ctx.channel.send(embed = embed, delete_after = 20)
        else:
            channelID = voice[0]
            channel = self.bot.get_channel(channelID)
            await channel.edit(name = name)
            embed = discord.Embed(
                description = f'{ctx.author.mention}, изменил название канала' + '{}'.format(name),
                color = 0x2f3136)            
            await ctx.channel.send(embed = embed)
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
            embed = discord.Embed(
                description = f'{ctx.author.mention}, вы не находитесь в голосовом канале',
                color = 0xFF0000)
            await ctx.channel.send(embed = embed, delete_after = 30)
        else:
            id = ctx.author.id
            c.execute("SELECT userID FROM voiceChannel WHERE voiceID = ?", (channel.id,))
            voice=c.fetchone()
            if voice is None:
                embed = discord.Embed(
                    description = f'{ctx.author.mention}, вы не владелец данного канала',
                    color = 0xFF0000)
                await ctx.channel.send(embed = embed, delete_after = 20)
            else:
                for data in channel.members:
                    if data.id == voice[0]:
                        owner = ctx.guild.get_member(voice [0])
                        embed = discord.Embed(
                            description = f'{ctx.author.mention}, этот канал уже пренадлоежит {owner.mention}',
                            color = 0xFF0000)
                        await ctx.channel.send(embed = embed)
                        x = True
                if x == False:
                    embed = discord.Embed(
                        description = f'{ctx.author.mention} Стал владельцем канала' + '{}'.format(channel.id))
                    await ctx.channel.send(embed = embed)
                    c.execute("UPDATE voiceChannel SET userID = ? WHERE voiceID = ?", (id, channel.id))
            conn.commit()
            conn.close()
