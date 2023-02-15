from discord.ext import commands

from src.db_folder.databases import PollDatabase, VoteButtonDatabase
from src.ui.embeds import PollEmbed, PollEmbedBase
from src.ui.poll import Poll
from src.ui.poll_view import PollView


def error_handling(answer: tuple[str]) -> str:
    if len(answer) > Poll.MAX_OPTIONS:
        return f"Zadal jsi příliš mnoho odpovědí, můžeš maximálně {Poll.MAX_OPTIONS}!"
    elif len(answer) < Poll.MIN_OPTIONS:
        return f"Zadal jsi příliš málo odpovědí, můžeš alespoň {Poll.MIN_OPTIONS}!"


class PollCreate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["anketa"])
    async def pool(self, ctx: commands.Context, question: str, *answer: str):
        await ctx.message.delete()

        message = await ctx.send(embed=PollEmbedBase("Dělám na tom, vydrž!"))
        if error_handling(answer):
            return await message.edit(embed=PollEmbedBase(error_handling(answer)))

        poll = Poll(
            message_id=message.id,
            channel_id=message.channel.id,
            question=question,
            options=answer,
            user_id=ctx.message.author.id
        )

        embed = PollEmbed(poll)
        view = PollView(poll, embed, db_poll=self.bot.pool)
        await PollDatabase(self.bot.pool).add(poll)
        await VoteButtonDatabase(self.bot.pool).add_options(poll)

        await message.edit(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(PollCreate(bot))
