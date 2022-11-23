import discord
from discord.ext import commands


class PersistentView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)


class Buttons(discord.ui.Button):
    def __init__(self, custom_id, embed: discord.Embed, index: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.custom_id = custom_id
        self.embed = embed
        self.index = index

        self.users = set()

    def get_users_from_embed(self, embed: discord.Embed):
        dict1 = embed.to_dict()

        return set(
            x.rsplit("|", 1)
            for x in dict1["fields"][self.index].values())

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.name not in self.users:
            self.users.add(interaction.user.name)

        else:
            self.users.remove(interaction.user.name)

        edit = self.embed.set_field_at(
            index=self.index,
            name=self.embed.fields[self.index].name,
            value=f"**{len(self.users)}** | {', '.join(self.users)}",
            inline=False)

        print(self.get_users_from_embed(embed=self.embed))
        print(self.users)
        await interaction.response.edit_message(embed=edit)


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

            view = PersistentView()

            for x, option in enumerate(answer):
                embed.add_field(
                    name=f"{self.reactions[x]} {option}",
                    value="**0** |",
                    inline=False)

                view.add_item(Buttons(label=str(x + 1), custom_id="button_no" + str(x), index=x, embed=embed))

            print(embed.to_dict())
            await ctx.send(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(PollCreate(bot))
