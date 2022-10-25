import discord
from discord.ext import commands


class PollView(discord.ui.View):
    def __init__(self, embed: discord.Embed):
        super().__init__()
        self.embed = embed
        self.users = set()

    @discord.ui.button(label="jedna", style=discord.ButtonStyle.gray)
    async def button_one(self, interaction: discord.Interaction, button: discord.ui.Button):

        if interaction.user.name not in self.users:
            self.users.add(interaction.user.name)
            button.style = discord.ButtonStyle.green

        else:
            self.users.remove(interaction.user.name)
            button.style = discord.ButtonStyle.red

        edit = self.embed.set_field_at(
            index=0,
            name=self.embed.fields[0].name,
            value=f"**{len(self.users)}** | {', '.join(self.users)}",
            inline=False)
        await interaction.response.edit_message(embed=edit, view=self)


class PollCreate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']

    @commands.command()
    async def anketa_test(self, ctx: commands.Context, question: str, *answer: str):
        if len(answer) > 10:
            return await ctx.send("Zadal jsi příliš mnoho odpovědí, maximum je 10!")

        elif len(answer) <= 10:

            embed = discord.Embed(
                title="📊 " + question,
                color=0xff0000)

            for x, option in enumerate(answer):
                embed.add_field(
                    name=f"{self.reactions[x]} {option}",
                    value="**0** |",
                    inline=False)

            await ctx.send(embed=embed, view=PollView(embed=embed))


async def setup(bot):
    await bot.add_cog(PollCreate(bot))
