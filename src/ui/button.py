import aiomysql.pool
import discord
from discord import InteractionResponse, Member

from src.db_folder.databases import VoteButtonDatabase
from src.ui.embeds import PollEmbed
from src.ui.emojis import ScoutEmojis
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

    async def toggle_vote(self, interaction: discord.Interaction) -> set[Member]:
        vote_button_db = VoteButtonDatabase(self.db_poll)
        user = interaction.user.id

        users_id = await vote_button_db.fetch_all_users(self.poll, self.index)

        if user not in users_id:
            await vote_button_db.add_user(self.poll, user, self.index)
            users_id.add(user)
        else:
            await vote_button_db.remove_user(self.poll, user, self.index)
            users_id.remove(user)

        return {interaction.guild.get_member(user_id) for user_id in users_id}

    async def edit_embed(self, members: set[Member]) -> discord.Embed:
        return self.embed.set_field_at(
            index=self.index,
            name=self.embed.fields[self.index].name,
            value=f"**{len(members)}** | {', '.join(member.mention for member in members)}",
            inline=False,
        )

    async def callback(self, interaction: discord.Interaction) -> InteractionResponse:
        members = await self.toggle_vote(interaction)

        edited_embed = await self.edit_embed(members)
        return await interaction.response.edit_message(embed=edited_embed)


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

    async def callback(self, interaction: discord.Interaction) -> InteractionResponse:
        await self.interaction_check(interaction)

        modal = NewOptionModal(self.embed, self.db_pool, self.poll, self.view)
        return await interaction.response.send_modal(modal)

    async def interaction_check(self, interaction: discord.Interaction) -> PermissionError | ValueError | None:
        """
        This function does error handling for pressing the button, before anything shows. Unfortunately it can't
        use PrettyError() class, because components derived from Item() class has errors silently passed. This means
        that we should use errors derived from Exception() class instead.

        Parameters
        ----------
            interaction: discord.Interaction

        Raises
        -------
            PermissionError, ValueError
        """
        if self.poll.user_id != interaction.user.id:
            msg = "Nejsi uživatel, kdo vytvořil tuto anketu. Nemáš tedy nárok ji upravovat."
            raise PermissionError(msg)
        if len(self.embed.fields) >= 10:
            msg = "Nemůžeš mít víc jak 10 možností!"
            raise ValueError(msg)
        return None
