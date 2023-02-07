from typing import Optional

import discord

from poll_design.poll import Poll
from ui.poll_embed import PollEmbed

"""
TODO: 

Najít způsob jak udělat z message_id objekt tak, abych mohl fetchovat embed z toho. 
Teď to funguje tak, že embed.edit_message nefunguje vůbec, protože: 

Traceback (most recent call last):
  File "/Users/robertsokola/PycharmProjects/Jachym-bot-main/virtualenv/lib/python3.10/site-packages/discord/ui/view.py", line 425, in _scheduled_task
    await item.callback(interaction)
  File "/Users/robertsokola/PycharmProjects/Jachym-bot-main/poll_design/button.py", line 39, in callback
    edit = self.message_id.set_field_at(
AttributeError: 'int' object has no attribute 'set_field_at'

Řešení je:

if payload.message_id in self.caching:
            channel = self.bot.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)

z původního kódu. 

SEŠ BLÍZKO, TAK TO DOTÁHNI AAAA
"""


class ButtonBackend(discord.ui.Button):
    def __init__(self,
                 custom_id: str,
                 message_id: Optional[Poll.message_id],
                 channel_id: Optional[Poll.channel_id],
                 embed: PollEmbed,
                 index: int,
                 label: str) -> None:

        super().__init__(label=label)
        self.custom_id = custom_id
        self.message_id = message_id
        self.channel_id = channel_id
        self.embed = embed
        self.index = index

        self.users = set()

    def id(self):
        return self.custom_id

    def edit_embed(self) -> discord.Embed:
        edit = self.embed.set_field_at(
            index=self.index,
            name=self.embed.fields[self.index].name,
            value=f"**{len(self.users)}** | {','.join(user.name for user in self.users)}",
            inline=False)
        return edit

    async def callback(self, interaction: discord.Interaction):
        if interaction.user not in self.users:
            self.users.add(interaction.user)

        else:
            self.users.remove(interaction.user)

        await interaction.response.edit_message(embed=self.edit_embed())

    def _load_users(self):
        # fetch from database
        pass
