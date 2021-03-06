"""
Rina Bot: Discord Bot for Something Probably
Copyright (C) 2020 Rina

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import asyncio
import logging

import aiohttp
import asyncpg
import discord
from discord.ext import commands

from .config import TOKEN
from .context import Context


async def get_prefix(bot, message):
    default_prefix = [f"<@{bot.user.id}> ", f"<@!{bot.user.id}> "]
    if not message.guild:
        return default_prefix
    prefixes = await bot.pool.fetchval(
        """
        SELECT prefixes
            FROM guild_prefixes
            WHERE guild_id = $1
        """,
        message.guild.id,
    )

    if prefixes == None:
        return default_prefix
    else:
        return default_prefix + prefixes


class RinaBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents(
            guilds=True,
            members=True,
            presences=True,
            messages=True,
            guild_reactions=True,
        )

        super().__init__(
            command_prefix=get_prefix, case_insensitive=True, intents=intents
        )

        extensions = [
            "jishaku",
            "src.cogs.misc",
            "src.cogs.errors",
            "src.cogs.rng",
            "src.cogs.logs",
        ]

        for cog in extensions:
            self.load_extension(cog)

    def run(self):
        logger = logging.getLogger("discord")
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter(
                "[%(asctime)s] (%(levelname)s) %(name)s: %(message)s",
                datefmt="%y %b %d %H:%M:%S",
            )
        )
        logger.addHandler(handler)

        super().run(TOKEN)

    async def on_message(self, message):

        return await super().on_message(message)

    async def process_commands(self, message):
        if message.author.bot:
            return

        ctx = await self.get_context(message, cls=Context)
        await self.invoke(ctx)

    async def handle_guild(self, guild):
        await self.pool.execute(
            """
            INSERT INTO guilds (id)
                VALUES ($1)
            ON CONFLICT (id)
                DO NOTHING
            """,
            guild.id,
        )

    async def on_guild_available(self, guild):
        await self.handle_guild(guild)

    async def start(self, *args, **kwargs):
        self.pool = None

        while not self.pool:
            try:
                self.pool = await asyncpg.create_pool(user="postgres", host="db")
            except asyncpg.exceptions.CannotConnectNowError:
                await asyncio.sleep(1)

        async with aiohttp.ClientSession(
            loop=self.loop,
            headers={
                "User-Agent": "Rina Bot/0.1a (+https://github.com/araRina/Rina-Bot)"
            },
        ) as self.session:
            await super().start(*args, **kwargs)
