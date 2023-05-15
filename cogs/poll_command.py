import re

import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger

from src.db_folder.databases import PollDatabase, VoteButtonDatabase
from src.jachym import Jachym
from src.ui.embeds import PollEmbed, PollEmbedBase
from src.ui.poll import Poll
from src.ui.poll_view import PollView


def error_handling(answer: list[str]) -> str:
    if len(answer) > Poll.MAX_OPTIONS:
        return f"Zadal jsi příliš mnoho odpovědí, můžeš maximálně {Poll.MAX_OPTIONS}!"
    elif len(answer) < Poll.MIN_OPTIONS:
        return f"Zadal jsi příliš málo odpovědí, můžeš alespoň {Poll.MIN_OPTIONS}!"


class PollCreate(commands.Cog):
    POLL_PARAMETERS = {
        "name": "anketa",
        "description": "Anketa pro hlasování. Jsou vidět všichni hlasovatelé.",
        "question": "Otázka, na kterou potřebuješ vědět odpověď",
        "answer": 'Odpovědi, rozděluješ odpovědi uvozovkou ("), maximálně pouze 10 možností',
        "help":
            """
            Jednoduchá anketa, která obsahuje otázku a odpovědi. Povoleno je 10 možností. 
            """
    }

    # Bugfix for iPhone users who have different font for aposthrofe
    REGEX_PATTERN = ['"', '”', '“', '„']

    def __init__(self, bot: Jachym):
        self.bot = bot

    @app_commands.command(
        name=POLL_PARAMETERS["name"],
        description=POLL_PARAMETERS["description"],
    )
    @app_commands.describe(
        question=POLL_PARAMETERS["question"],
        answer=POLL_PARAMETERS["answer"],
    )
    async def pool(self, interaction: discord.Interaction, question: str, answer: str) -> discord.Message:
        await interaction.response.send_message(
            embed=PollEmbedBase("Dělám na tom, vydrž!")
        )
        message = await interaction.original_response()

        answers = re.split('|'.join(self.REGEX_PATTERN), answer)
        if error_handling(answers):
            return await message.edit(embed=PollEmbedBase(error_handling(answers)))

        poll = Poll(
            message_id=message.id,
            channel_id=message.channel.id,
            question=question,
            options=answers,
            user_id=interaction.user.id,
        )

        embed = PollEmbed(poll)
        view = PollView(poll, embed, db_poll=self.bot.pool)
        await PollDatabase(self.bot.pool).add(poll)
        await VoteButtonDatabase(self.bot.pool).add_options(poll)

        self.bot.active_discord_polls.add(poll)
        await self.bot.set_presence()
        logger.info(f"Successfully added Pool - {message.id}")
        return await message.edit(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(PollCreate(bot))
