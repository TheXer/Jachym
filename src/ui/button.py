import aiomysql.pool
import discord

from src.db_folder.databases import VoteButtonDatabase
from src.ui.embeds import PollEmbed
from src.ui.poll import Poll


class ButtonBackend(discord.ui.Button):
    def __init__(self,
                 custom_id: str,
                 poll: Poll,
                 emoji: str,
                 embed: PollEmbed,
                 index: int,
                 label: str,
                 db_poll: aiomysql.pool.Pool) -> None:

        super().__init__(
            label=label if len(label) <= 30 else "",
            emoji=emoji,
            custom_id=custom_id
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

        users_ID = await vote_button_db.fetch_all_users(self.poll.message_id, self.index)

        if user not in users_ID:
            await vote_button_db.add_user(self.poll.message_id, user, self.index)
            users_ID.add(user)
        else:
            await vote_button_db.remove_user(self.poll.message_id, user, self.index)
            users_ID.remove(user)

        members = set(
            interaction.guild.get_member(user_id).display_name
            for user_id in users_ID
        )

        return members

    async def edit_embed(self, members: set[str]) -> discord.Embed:
        edit = self.embed.set_field_at(
            index=self.index,
            name=self.embed.fields[self.index].name,
            value=f"**{len(members)}** | {', '.join(members)}",
            inline=False)

        return edit

    async def callback(self, interaction: discord.Interaction):
        members = await self.toggle_vote(interaction)

        edited_embed = await self.edit_embed(members)

        await interaction.response.edit_message(embed=edited_embed)
