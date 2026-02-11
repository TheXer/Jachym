import asyncio
import datetime

import discord
from discord import app_commands
from discord.app_commands import Transform
from discord.ext import commands, tasks
from loguru import logger
from src.jachym import Jachym
from src.ui.embeds import PollEmbed, PollEmbedBase
from src.ui.poll_view import PollView
from src.ui.transformers import DatetimeTransformer, OptionsTransformer

from src.models import Poll, PollOption


class PollCreate(commands.Cog):
    """Cog for managing poll creation and auto-expiration.
    
    Handles:
    - Creating polls with single/multiple choice options
    - Auto-closing polls when end_date is reached
    - Sending results to subscribers and channel
    """

    def __init__(self, bot: Jachym):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        """Start the poll expiration task when bot is ready."""
        if not self.check_expired_polls.is_running():
            self.check_expired_polls.start()
            logger.info("Poll expiration task started")


    @app_commands.command(
        name="anketa",
        description="Anketa pro hlasování. Jsou vidět všichni hlasovatelé.",
    )
    @app_commands.rename(
        question="otázka",
        answer="odpovědi",
        date_time="datum",
        multiple_choice="vícenásobné_hlasování",
    )
    @app_commands.describe(
        question="Otázka, kterou chceš položit.",
        answer='Odpovědi, rozděluješ odpovědi uvozovkou ("), maximálně pouze 10 možností',
        date_time="Den, na který anketa skončí (např. zítra ve 12 nebo 2025-02-12).",
        multiple_choice="Mohou uživatelé volit více odpovědí? (True pokud ano, False pokud ne, defaultně False)",
    )
    async def pool(
        self,
        interaction: discord.Interaction,
        question: str,
        answer: Transform[list[str], OptionsTransformer],
        date_time: Transform[datetime.datetime, DatetimeTransformer] | None,
        multiple_choice: bool = False,
    ):
        await interaction.response.defer()
        
        # Create poll with user-specified settings
        poll = await Poll.create(
            guild_id=interaction.guild_id,
            channel_id=interaction.channel_id,
            message_id=interaction.id,
            creator_id=interaction.user.id,
            question=question,
            is_anonymous=False,
            allow_multiple_votes=multiple_choice,
            end_date=date_time,
        )
        
        logger.info(
            f"Creating poll: question='{question}', multiple={multiple_choice}, "
            f"end_date={date_time}"
        )
        
        options_data = [
            PollOption(
                poll=poll,
                text=text,
                position=i,
                created_by=interaction.user.id,
                )
        for i, text in enumerate(answer)
        ]
        
        await PollOption.bulk_create(options_data)

        # Fetch created options ordered by position
        options = await PollOption.filter(poll=poll).order_by("position").all()

        # Build embed with poll mode indicator
        embed = PollEmbed(poll.question, options, created_at=poll.created_at)
        
        
        view = PollView(poll, options, embed)

        logger.info(f"Successfully added Poll - {poll.id}")

        message = await interaction.followup.send(embed=embed, view=view, wait=True)

        poll.message_id = message.id
        await poll.save()

        await self.bot.set_presence()
        logger.info(f"Poll {poll.id} created in message {message.id}")

    @tasks.loop(minutes=1)
    async def check_expired_polls(self):
        """Background task to check and close expired polls.
        
        Runs every minute to find polls that have reached their end_date.
        For each expired poll:
        - Marks it as ended
        - Rebuilds results from database
        - Sends results to channel
        - Notifies all subscribers and creator
        
        Only checks polls that:
        - Have status=active
        - Have end_date set (not indefinite)
        - end_date <= current time
        """
        try:
            now = datetime.datetime.now(datetime.timezone.utc)
            
            # Find all active polls that should be expired
         
            expired_polls = await Poll.filter(
                status="active",
                end_date=None,
            ).all()
        
            expired_polls = [
                p for p in expired_polls
                if p.end_date and p.end_date <= now
            ]
            
            # Close polls
            for poll in expired_polls:
                await self._close_expired_poll(poll)
                    
        except Exception as e:
            logger.error(f"Error in check_expired_polls: {e}")

    @check_expired_polls.before_loop
    async def before_check_expired_polls(self):
        """Wait for bot to be ready before starting the loop."""
        await self.bot.wait_until_ready()
        # Give database time to initialize
        await asyncio.sleep(1)

    async def _close_expired_poll(self, poll: Poll) -> None:
        """Close an expired poll and notify subscribers.
        
        Args:
            poll: Poll model to close.
            
        Operations:
        - Marks poll as ended in database
        - Fetches all options and votes
        - Builds results embed
        - Sends results to original channel
        - Sends DMs to all subscribers + creator
        """
        try:
            # Mark as ended
            poll.status = "ended"
            await poll.save()
            
            logger.info(f"Auto-closing poll {poll.id}")
            
            # Rebuild data from database
            options = await PollOption.filter(
                poll_id=poll.id
            ).order_by("position").all()
            
            from src.ui.modals import get_option_vote_counts
            votes_by_option = await get_option_vote_counts(poll.id)
            
            # Build results embed
            results_embed = await self._build_poll_results(
                poll, options, votes_by_option
            )
            
            # Send to channel
            channel = self.bot.get_channel(poll.channel_id)
            if channel:
                await channel.send(embed=results_embed)
            
            # Notify subscribers
            from src.ui.modals import notify_poll_subscribers
            await notify_poll_subscribers(
                poll,
                results_embed,
                self.bot,
            )
            
            logger.info(f"Poll {poll.id} closed and results sent")
            
        except Exception as e:
            logger.error(f"Error closing poll {poll.id}: {e}")

    async def _build_poll_results(
        self,
        poll: Poll,
        options: list[PollOption],
        votes_by_option: dict,
    ) -> discord.Embed:
        """Build results embed for a closed poll.
        
        Args:
            poll: Poll model.
            options: List of PollOption instances.
            votes_by_option: Dict mapping option_id to Vote list.
            
        Returns:
            Formatted results embed with ranked options.
        """
        results_embed = PollEmbedBase(f"📊 Výsledky: {poll.question}")
        results_embed.timestamp = datetime.datetime.now()
        results_embed.set_footer(text="Anketa ukončena ✅")
        
        # Sort options by vote count descending
        sorted_options = sorted(
            options,
            key=lambda opt: len(votes_by_option.get(opt.id, [])),
            reverse=True,
        )
        
        # Add results
        for rank, option in enumerate(sorted_options, 1):
            votes = votes_by_option.get(option.id, [])
            vote_count = len(votes)
            
            # Get member names (filter out deleted members)
            guild = self.bot.get_guild(poll.guild_id)
            member_names = []
            for vote in votes:
                member = guild.get_member(vote.user_id) if guild else None
                if member:
                    member_names.append(member.display_name)
            
            voter_text = ", ".join(member_names) if member_names else "(nikdo)"
            vote_text = f"**{vote_count}** hlasů | {voter_text}"
            
            results_embed.add_field(
                name=f"#{rank} {option.text}",
                value=vote_text,
                inline=False,
            )
        
        return results_embed


async def setup(bot):
    await bot.add_cog(PollCreate(bot))
