import discord
from discord.ext import commands

class Buttons(discord.ui.Button):
    def __init__(self, custom_id: str, embed: discord.Embed, index: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.custom_id = custom_id
        self.embed = embed
        self.index = index

        self.users = set()

    async def callback(self, interaction: discord.Interaction):
        if interaction.user not in self.users:
            self.users.add(interaction.user)

        else:
            self.users.remove(interaction.user)

        edit = self.embed.set_field_at(
            index=self.index,
            name=self.embed.fields[self.index].name,
            value=f"**{len(self.users)}** | {','.join(user.name for user in self.users)}",
            inline=False)

        await interaction.response.edit_message(embed=edit)


class PersistentView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    def add_button(self, answers, embed: discord.Embed, message_id):
        for index, answer in enumerate(answers):
            self.add_item(Buttons(
                label=f"{index + 1}",
                custom_id=f"{message_id}:{index}",
                index=index,
                embed=embed
            ))


def error_check(answer: tuple[str]) -> str:
    if len(answer) > 10:
        return "Zadal jsi příliš mnoho odpovědí, maximum je 10!"
    elif len(answer) < 2:
        return "Zadal jsi příliš málo odpovědí! Alespoň 2!"


class PollCreate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']

    @commands.command()
    async def poll(self, ctx: commands.Context, question: str, *answer: str):
        if error_check(answer):
            return await ctx.send(error_check(answer))

        embed = discord.Embed(
            title="📊 " + question,
            color=0xff0000)

        for index, option in enumerate(answer):
            embed.add_field(
                name=f"{self.reactions[index]} {option}",
                value="**0** |",
                inline=False)

        view = PersistentView()
        view.add_button(answer, embed, message_id=ctx.message.id)

        print(ctx.message.id)

        await ctx.send(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(PollCreate(bot))
