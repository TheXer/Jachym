import asyncio

import discord
from discord.ext import Message, app_commands, commands

# Reminder command


class Reminder(commands.Cog):
    """Class for reminder command"""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="reminder", description="Nastav si připomínku!")
    @app_commands.describe(time="Za kolik minut se má připomínka zobrazit", topic="Předmět připomínky")
    async def reminder(self, interaction: discord.Interaction, time: int, topic: str) -> Message:
        """Reminder command"""
        await interaction.response.send_message(f"Za {time} minut ti připomenu!", ephemeral=True)
        await asyncio.sleep(time * 60)
        await interaction.followup.send(f"{interaction.user.mention} připomínám ti {topic}!", ephemeral=True)
