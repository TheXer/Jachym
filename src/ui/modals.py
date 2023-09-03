import aiomysql
import discord

from src.db_folder.databases import VoteButtonDatabase
from src.ui.embeds import PollEmbed
from src.ui.emojis import NUMBER_EMOJIS
from src.ui.poll import Poll


class NewOptionModal(discord.ui.Modal):
    def __init__(self, embed: PollEmbed, db_poll: aiomysql.pool.Pool, poll: Poll, view):
        super().__init__(title="Přidání nové možnosti do ankety")

        self.new_option = discord.ui.TextInput(
            label="Jméno nové možnosti",
            min_length=1,
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

    async def add_item_to_embed(self) -> PollEmbed:
        # To avoid circular import
        from src.ui.button import ButtonBackend

        date_field = len(self.embed.fields) - 1

        # Lmao, not ideal, but it is what it is.
        if self.embed.fields[date_field].value.startswith("Anketa vyprší"):
            index = date_field
            emoji = date_field
        else:
            index = len(self.embed.fields)
            emoji = len(self.embed.fields)

        options = {
            "name": f"{NUMBER_EMOJIS[emoji]} {self.new_option.value}",
            "value": "**0** | ",
            "inline": False,
            "index": index,
        }

        self.view.add_item(
            ButtonBackend(
                label=self.new_option.value,
                emoji=NUMBER_EMOJIS[emoji],
                index=index,
                poll=self.poll,
                custom_id=f"{len(self.embed.fields)}:{self.poll.message_id}",
                embed=self.embed,
                db_poll=self.db_poll,
            )
        )
        await VoteButtonDatabase(self.db_poll).add_option(self.poll, self.new_option.value)

        return self.embed.insert_field_at(**options)
