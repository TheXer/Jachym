import aiomysql.pool
import discord

from cogs.error import TooManyOptionsError
from src.db_folder.databases import VoteButtonDatabase
from src.ui.embeds import PollEmbed
from src.ui.emojis import EssentialEmojis, ScoutEmojis
from src.ui.modals import NewOptionModal
from src.ui.poll import Poll


class ButtonBackend(discord.ui.Button):
    """
    Button class to edit a poll embed with.
    """

    LENTGH_STRING = 30

    def __init__(
        self,
        custom_id: str,
        poll: Poll,
        emoji: str,
        embed: PollEmbed,
        index: int,
        label: str,
        db_poll: aiomysql.pool.Pool,
    ) -> None:
        super().__init__(
            label=label if len(label) <= self.LENTGH_STRING else "",
            emoji=emoji,
            custom_id=custom_id,
        )
        self.poll = poll
        self.embed = embed
        self._index = index
        self.db_poll = db_poll

    @property
    def index(self):
        return self._index

    async def toggle_vote(self, interaction: discord.Interaction) -> set[str]:
        vote_button_db = VoteButtonDatabase(self.db_poll)
        user = interaction.user.id

        users_id = await vote_button_db.fetch_all_users(self.poll, self.index)

        if user not in users_id:
            await vote_button_db.add_user(self.poll, user, self.index)
            users_id.add(user)
        else:
            await vote_button_db.remove_user(self.poll, user, self.index)
            users_id.remove(user)

        return {interaction.guild.get_member(user_id).display_name for user_id in users_id}

    async def edit_embed(self, members: set[str]) -> discord.Embed:
        return self.embed.set_field_at(
            index=self.index,
            name=self.embed.fields[self.index].name,
            value=f"**{len(members)}** | {', '.join(members)}",
            inline=False,
        )

    async def callback(self, interaction: discord.Interaction):
        members = await self.toggle_vote(interaction)

        edited_embed = await self.edit_embed(members)

        await interaction.response.edit_message(embed=edited_embed)


class NewOptionButton(discord.ui.Button):
    LABEL = "Přidat novou možnost"

    def __init__(self, embed: PollEmbed, poll: Poll, db_pool: aiomysql.pool.Pool):
        self.embed = embed
        self.poll = poll
        self.db_pool = db_pool

        super().__init__(
            label=self.LABEL,
            emoji=ScoutEmojis.FLEUR_DE_LIS.value,
            custom_id=f"option_button::{poll.message_id}",
            row=4,
        )

    async def callback(self, interaction: discord.Interaction):
        modal = NewOptionModal(self.embed, self.db_pool, self.poll, self.view)
        await interaction.response.send_modal(modal)
