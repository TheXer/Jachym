import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger

from src.db_folder.databases import PollDatabase, VoteButtonDatabase
from src.jachym import Jachym
from src.ui.embeds import (
    PollEmbed,
    PollEmbedBase,
    CooldownErrorEmbed
)
from src.ui.poll import Poll
from src.ui.poll_view import PollView


def error_handling(answer: list[str]) -> str:
    if len(answer) > Poll.MAX_OPTIONS:
        return f"Zadal jsi příliš mnoho odpovědí, můžeš maximálně {Poll.MAX_OPTIONS}!"
    elif len(answer) < Poll.MIN_OPTIONS:
        return f"Zadal jsi příliš málo odpovědí, můžeš alespoň {Poll.MIN_OPTIONS}!"


class PollCreate(commands.Cog):
    def __init__(self, bot: Jachym):
        self.bot = bot

    @app_commands.command(
        name="anketa",
        description="Anketa pro hlasování. Jsou vidět všichni hlasovatelé.")
    @app_commands.describe(
        question="Otázka, na kterou potřebuješ vědět odpověď",
        answer='Odpovědi, rozděluješ odpovědi uvozovkou ("), maximálně pouze 10 možností')
    async def pool(self, interaction: discord.Interaction, question: str, answer: str) -> discord.Message:

        await interaction.response.send_message(embed=PollEmbedBase("Dělám na tom, vydrž!"))
        message = await interaction.original_response()

        answers = answer.split(sep='"')
        if error_handling(answers):
            return await message.edit(embed=PollEmbedBase(error_handling(answers)))

        poll = Poll(
            message_id=message.id,
            channel_id=message.channel.id,
            question=question,
            options=answers,
            user_id=interaction.user.id
        )

        embed = PollEmbed(poll)
        view = PollView(poll, embed, db_poll=self.bot.pool)
        await PollDatabase(self.bot.pool).add(poll)
        await VoteButtonDatabase(self.bot.pool).add_options(poll)

        self.bot.active_discord_polls.add(poll)
        await self.bot.set_presence()
        logger.info(f"Successfully added Pool - {message.id}")
        return await message.edit(embed=embed, view=view)

    @pool.error
    async def pool_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(embed=CooldownErrorEmbed(error.retry_after))

    @commands.command()
    async def anketa(self, ctx, question, *answers):
        message = await ctx.send(embed=PollEmbedBase("Dělám na tom, vydrž!"))

        if error_handling(answers):
            return await message.edit(embed=PollEmbedBase(error_handling(answers)))

        poll = Poll(
            message_id=message.id,
            channel_id=message.channel.id,
            question=question,
            options=answers,
            user_id=ctx.user.id
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
