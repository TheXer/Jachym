import discord

from cogs.error import TooManyOptionsError, NoPermissionError
from src.db_folder.databases import VoteButtonDatabase


class NewOptionModal(discord.ui.Modal):
    EMOJIS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

    def __init__(self, embed, db_poll, poll, view):
        super().__init__(title="Nová možnost")

        self.new_option = discord.ui.TextInput(
            label="Jméno nové možnosti",
            max_length=255,
            required=True,
            placeholder="Vymysli príma otázku!",
            style=discord.TextStyle.short,
        )

        self.add_item(self.new_option)

        self.embed = embed
        self.db_poll = db_poll
        self.poll = poll
        self.view = view

    async def on_submit(self, interaction: discord.Interaction):
        em = await self.add_item_to_embed()
        await interaction.response.edit_message(embed=em, view=self.view)

    async def interaction_check(self, interaction: discord.Interaction):
        if not self.poll.user_id == interaction.user.id:
            raise NoPermissionError(
                "Nejsi uživatel, kdo vytvořil tuto anketu. Nemáš tedy nárok ji upravovat.",
                interaction,
            )
        if len(self.embed.fields) > 10:
            raise TooManyOptionsError("Nemůžeš mít víc jak 10 možností!", interaction)

    async def add_item_to_embed(self):
        from src.ui.button import ButtonBackend

        self.view.add_item(
            ButtonBackend(
                label=self.new_option.value,
                emoji=self.EMOJIS[len(self.embed.fields)],
                index=len(self.embed.fields),
                poll=self.poll,
                custom_id=f"{len(self.embed.fields)}:{self.poll.message_id}",
                embed=self.embed,
                db_poll=self.db_poll,
            )
        )
        await VoteButtonDatabase(self.db_poll).add_option(self.poll, self.new_option.value)

        return self.embed.add_field(
            name=f"{self.EMOJIS[len(self.embed.fields)]} {self.new_option.value}",
            value="**0** | ",
            inline=False,
        )
