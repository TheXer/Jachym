import re
from src.ui.error_handling import TooFewOptionsError, TooManyOptionsError
import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger

from src.db_folder.databases import PollDatabase, VoteButtonDatabase
from src.jachym import Jachym
from src.ui.embeds import PollEmbed, PollEmbedBase
from src.ui.poll import Poll
from src.ui.poll_view import PollView


def error_handling(answer: list[str]) -> TooFewOptionsError | TooManyOptionsError | None:
    if len(answer) > Poll.MAX_OPTIONS:
        raise TooManyOptionsError(f"Zadal jsi příliš mnoho odpovědí, můžeš maximálně {Poll.MAX_OPTIONS}!")
    if len(answer) < Poll.MIN_OPTIONS:
        raise TooFewOptionsError(f"Zadal jsi příliš málo odpovědí, můžeš alespoň {Poll.MIN_OPTIONS}!")
    return None


class PollCreate(commands.Cog):
    POLL_PARAMETERS = {
        "name": "anketa",
        "description": "Anketa pro hlasování. Jsou vidět všichni hlasovatelé.",
        "question": "Otázka, na kterou potřebuješ vědět odpověď",
        "answer": 'Odpovědi, rozděluješ odpovědi uvozovkou ("), maximálně pouze 10 možností',
        "help": """
            Jednoduchá anketa, která obsahuje otázku a odpovědi. Povoleno je 10 možností.
            """,
    }

    # Bugfix for iPhone users who have different font for aposthrofe
    REGEX_PATTERN = ['"', "”", "“", "„"]

    def __init__(self, bot: Jachym):
        self.bot = bot

    @app_commands.command(
        name="anketa",
        description="Anketa pro hlasování. Jsou vidět všichni hlasovatelé.",
    )
    @app_commands.rename(question="otázka", answer="odpovědi")
    @app_commands.describe(
        question="Otázka, kterou chceš položit.",
        answer='Odpovědi, rozděluješ odpovědi uvozovkou ("), maximálně pouze 10 možností',
    )
    async def pool(
        self,
        interaction: discord.Interaction,
        question: str,
        answer: str,
    ) -> discord.Message:
        await interaction.response.send_message(
            embed=PollEmbedBase("Dělám na tom, vydrž!"),
        )
        message = await interaction.original_response()

        # bugfix for answers that were empty
        answers = [answer for answer in re.split("|".join(self.REGEX_PATTERN), answer) if answer.strip()]
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
