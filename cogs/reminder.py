import asyncio
from datetime import datetime, timedelta

import dateparser
import discord
from discord.ext import Message, app_commands, commands

# Reminder command


class Reminder(commands.Cog):
    """Class for reminder command"""

    def __init__(self, bot):
        self.bot = bot

    def countdown(self, trigger_time: datetime) -> str:
        """Calculate days, hours and minutes to a date.

        Args:
            trigger_time: The date.

        Returns:
            A string with the days, hours and minutes.
        """
        countdown_time: timedelta = trigger_time - datetime.now()

        days, hours, minutes = (
            countdown_time.days,
            countdown_time.seconds // 3600,
            countdown_time.seconds // 60 % 60,
        )

        # Return seconds if only seconds are left.
        if days == 0 and hours == 0 and minutes == 0:
            seconds: int = countdown_time.seconds % 60
            return f"{seconds} second" + ("s" if seconds != 1 else "")

        # TODO: Explain this.
        return ", ".join(
            f"{x} {y}{'s' * (x != 1)}"
            for x, y in (
                (days, "day"),
                (hours, "hour"),
                (minutes, "minute"),
            )
            if x
        )

    @app_commands.command(name="reminder", desription="Nastav si připomínku!")
    @app_commands.describe(topic="Co ti mám připomenout?", time="Kdy ti to mám připomenout?")
    async def reminder(self, interaction: discord.Interaction, time: str, topic: str) -> Message:
        """Reminder command"""
        trigger_time: datetime = dateparser.parse(time)
        await interaction.response.send_message(
            f"Za {self.countdown(trigger_time)} ti připomenu {topic}!", ephemeral=True
        )
        await asyncio.sleep(trigger_time.timestamp() - datetime.now().timestamp())
        await interaction.followup.send(f"{interaction.user.mention} připomínám ti {topic}!", ephemeral=True)
