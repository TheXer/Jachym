import asyncio
import datetime

import discord
from discord import app_commands
from discord.app_commands import Transform
from discord.ext import commands, tasks
from loguru import logger

from src.db_folder.databases import PollDatabase, VoteButtonDatabase
from src.jachym import Jachym
from src.ui.embeds import PollEmbed, PollEmbedBase
from src.ui.poll import Poll
from src.ui.poll_view import PollView
from src.ui.transformers import DatetimeTransformer, OptionsTransformer


class PollCreate(commands.Cog):
    def __init__(self, bot: Jachym):
        self.bot = bot

    @app_commands.command(
        name="anketa",
        description="Anketa pro hlasování. Jsou vidět všichni hlasovatelé.",
    )
    @app_commands.rename(
        question="otázka",
        answer="odpovědi",
        date_time="datum",
    )
    @app_commands.describe(
        question="Otázka, kterou chceš položit.",
        answer='Odpovědi, rozděluješ odpovědi uvozovkou ("), maximálně pouze 10 možností',
        date_time="Den, na který anketa skončí.",
    )
    async def pool(
        self,
        interaction: discord.Interaction,
        question: str,
        answer: Transform[list[str, ...], OptionsTransformer],
        date_time: Transform[datetime.datetime, DatetimeTransformer] | None,
    ) -> discord.Message:
        await interaction.response.send_message(embed=PollEmbedBase("Nahrávám anketu..."))
        message = await interaction.original_response()

        poll = Poll(
            message_id=message.id,
            channel_id=message.channel.id,
            question=question,
            options=answer,
            user_id=interaction.user.id,
            date_created=date_time,
        )

        embed = PollEmbed(poll)
        view = PollView(poll, embed, db_poll=self.bot.pool)
        await PollDatabase(self.bot.pool).add(poll)
        await VoteButtonDatabase(self.bot.pool).add_options(poll)

        self.bot.active_discord_polls.add((poll, message))
        await self.bot.set_presence()

        logger.info(f"Successfully added Pool - {message.id}")
        return await message.edit(embed=embed, view=view)


class PollTaskLoops(commands.Cog):
    def __init__(self, bot: Jachym):
        self.bot = bot
        self.send_completed_pool.start()

    @tasks.loop(seconds=5)
    async def send_completed_pool(self):
        for poll, message in self.bot.active_discord_polls.copy():
            if poll.created_at is None or datetime.datetime.now() < poll.created_at:
                continue

            embed = message.embeds[0]
            embed.title = f"{embed.title[0]} [UZAVŘENO] {embed.title[1:]}"
            channel = self.bot.get_channel(poll.channel_id)
            await channel.send(embed=embed)

            asyncio.create_task(PollDatabase(self.bot.pool).remove(poll.message_id))
            asyncio.create_task(message.delete())
            self.bot.active_discord_polls.remove((poll, message))


async def setup(bot):
    await bot.add_cog(PollCreate(bot))
    await bot.add_cog(PollTaskLoops(bot))
