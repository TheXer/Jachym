import aiomysql.pool
import discord

from db_folder.sqldatabase import VoteButtonDatabase
from poll_design.poll import Poll
from ui.poll_embed import PollEmbed


class ButtonBackend(discord.ui.Button):
    def __init__(self,
                 custom_id: str,
                 poll: Poll,
                 embed: PollEmbed,
                 index: int,
                 label: str,
                 db_poll: aiomysql.pool.Pool) -> None:
        super().__init__(label=label)
        self.custom_id = custom_id
        self.poll = poll
        self.embed = embed
        self.index = index
        self.db_poll = db_poll

        self.users = set()

    def button_id(self):
        return self.custom_id

    def message_id(self):
        return self.message_id

    def index(self):
        return self.index

    async def _load_users(self):
        all_users = await VoteButtonDatabase(self.db_poll).fetch_all_users(
            self.poll.message_id,
            self.index)

        return all_users

    async def edit_embed(self, interaction: discord.Interaction) -> discord.Embed:
        users_id = await self._load_users()
        members = set(
            interaction.guild.get_member(user_id)
            for user_id in users_id
        )

        edit = self.embed.set_field_at(
            index=self.index,
            name=self.embed.fields[self.index].name,
            value=f"**{len(members)}** | {', '.join(member.name for member in members)}",
            inline=False)

        return edit

    async def callback(self, interaction: discord.Interaction):
        await VoteButtonDatabase(self.db_poll).toggle_vote(
            self.poll.message_id,
            interaction.user.id,
            self.index
        )

        edited_embed = await self.edit_embed(interaction)

        await interaction.response.edit_message(embed=edited_embed)
