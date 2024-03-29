# -*- coding: utf-8 -*-

"""
jishaku.cog
~~~~~~~~~~~

The Jishaku debugging and diagnostics cog implementation.

:copyright: (c) 2019 Devon (Gorialis) R
:license: MIT, see LICENSE for more details.

"""

import sys

import discord
import humanize
from discord.ext import commands

from jishaku.cog_base import JISHAKU_HIDE, JishakuBase
from jishaku.meta import __version__
from jishaku.metacog import GroupCogMeta
from jishaku.modules import package_version

try:
    import psutil
except ImportError:
    psutil = None

__all__ = (
    "Jishaku",
    "JishakuBase",
    "jsk",
    "setup",
)

# We define the Group separately from the Cog now, as the subcommand assignment is facilitated
#  by the GroupCogMeta metaclass on the Cog itself.
# This allows both the jishaku base command to be overridden (by metaclass argument) and for the
#  subcommands to be overridden (by simply defining new ones in the subclass)

@commands.group(name="jishaku", aliases=["jsk"], hidden=True,
                invoke_without_command=True, ignore_extra=False)
async def jsk(self, ctx: commands.Context):
    """
    The Jishaku debug and diagnostic commands.

    This command on its own gives a status brief.
    All other functionality is within its subcommands.
    """

    summary = [
        f"Jishaku v{__version__}, discord.py `{package_version('discord.py')}`, "
        f"`Python {sys.version}` on `{sys.platform}`".replace("\n", ""),
        f"Module was loaded {humanize.naturaltime(self.load_time)}, "
        f"cog was loaded {humanize.naturaltime(self.start_time)}.",
        ""
    ]

    if psutil:
        proc = psutil.Process()

        with proc.oneshot():
            mem = proc.memory_full_info()
            summary.append(f"Using {humanize.naturalsize(mem.rss)} physical memory and "
                           f"{humanize.naturalsize(mem.vms)} virtual memory, "
                           f"{humanize.naturalsize(mem.uss)} of which unique to this process.")

            name = proc.name()
            pid = proc.pid
            thread_count = proc.num_threads()

            summary.append(f"Running on PID {pid} (`{name}`) with {thread_count} thread(s).")

            summary.append("")  # blank line

    cache_summary = f"{len(self.bot.guilds)} guild(s) and {len(self.bot.users)} user(s)"

    if isinstance(self.bot, discord.AutoShardedClient):
        summary.append(f"This bot is automatically sharded and can see {cache_summary}.")
    elif self.bot.shard_count:
        summary.append(f"This bot is manually sharded and can see {cache_summary}.")
    else:
        summary.append(f"This bot is not sharded and can see {cache_summary}.")

    summary.append(f"Average websocket latency: {round(self.bot.latency * 1000, 2)}ms")

    await ctx.send("\n".join(summary))


class Jishaku(JishakuBase, metaclass=GroupCogMeta, command_parent=jsk, name= 'jishaku'):
    """
    The frontend subclass that mixes in to form the final Jishaku cog.
    """


def setup(bot: commands.Bot):
    """
    The setup function defining the jishaku.cog and jishaku extensions.
    """

    bot.add_cog(Jishaku(bot=bot))
