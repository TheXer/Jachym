from discord.ext import commands

from poll_design.poll import Poll
from poll_design.poll_view import PollView
from ui.poll_embed import PollEmbed, PollEmbedBase


class PollCreate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def poll(self, ctx: commands.Context, question: str, *answer: str):
        message = await ctx.send(embed=PollEmbedBase("Dělám na tom, vydrž!"))

        poll = Poll(
            message_id=message.id,
            channel_id=message.channel.id,
            question=question,
            options=answer
        )
        embed = PollEmbed(poll)
        view = PollView(poll)

        await message.edit(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(PollCreate(bot))
