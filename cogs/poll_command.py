import asyncio
import datetime

import discord
from discord import app_commands
from discord.app_commands import Transform
from discord.ext import commands, tasks
from loguru import logger
from src.jachym import Jachym
from src.ui.embeds import PollEmbed, PollEmbedBase
from src.ui.poll_view import PollView
from src.ui.transformers import DatetimeTransformer, OptionsTransformer

from src.models import Poll, PollOption


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
        answer: Transform[list[str], OptionsTransformer],
        date_time: Transform[datetime.datetime, DatetimeTransformer] | None,
    ):
        await interaction.response.defer()
        
        poll = await Poll.create(
            guild_id=interaction.guild_id,
            channel_id=interaction.channel_id,
            message_id=interaction.id,
            creator_id=interaction.user.id,
            question=question,
            is_anonymous=False,  # This command creates non-anonymous polls
            is_indefinite=(date_time is None),
            allow_multiple_votes=False,
            end_date=date_time,
        )
        
        options_data = [
            PollOption(
                poll=poll,
                text=text,
                position=i,
                created_by=interaction.user.id,
                )
        for i, text in enumerate(answer)
        ]
        
        await PollOption.bulk_create(options_data)

        # Fetch for embed
        
        logger.info(f"Successfully added Poll - {poll.id}")

        message = await interaction.followup.send(embed=embed, view=view, wait=True)
        
        poll.message_id = message.id
        await poll.save()
    
        await self.bot.set_presence()
        logger.info(f"Poll {poll.id} created in message {message.id}")




async def setup(bot):
    await bot.add_cog(PollCreate(bot))
