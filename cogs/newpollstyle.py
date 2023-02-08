from discord.ext import commands

from db_folder.sqldatabase import PollDatabase, VoteButtonDatabase
from poll_design.poll import Poll
from poll_design.poll_view import PollView
from ui.poll_embed import PollEmbed, PollEmbedBase


def error_handling(answer: tuple[str]) -> str:
    if len(answer) > Poll.MAX_OPTIONS:
        return f"Zadal jsi příliš mnoho odpovědí, můžeš maximálně {Poll.MAX_OPTIONS}!"
    elif len(answer) < Poll.MIN_OPTIONS:
        return f"Zadal jsi příliš málo odpovědí, můžeš alespoň {Poll.MIN_OPTIONS}!"


class PollCreate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def poll(self, ctx: commands.Context, question: str, *answer: str):
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
