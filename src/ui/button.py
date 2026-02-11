import discord
from discord import Interaction
from datetime import datetime

from src.ui.embeds import PollEmbed
from src.ui.emojis import ScoutEmojis, NUMBER_EMOJIS
from src.models import Vote, Poll, PollOption, PollSubscriber


# ==================== Helper Functions ====================


async def rebuild_and_display_poll(
    interaction: discord.Interaction,
    poll_id: int,
    embed: PollEmbed,
) -> discord.Embed:
    """Rebuild poll embed from database with current vote counts.
    
    Fetches all poll data and votes from the database, then reconstructs
    the embed with up-to-date information. This is used after any vote
    or option change to ensure the display is consistent.
    
    Args:
        interaction: Discord interaction context.
        poll_id: ID of the poll to rebuild.
        embed: Original embed object (for reference).
        
    Returns:
        A fresh embed with current poll state.
        
    Edge cases:
        - Handles polls with no votes gracefully (shows "0 | " for empty options)
        - Filters out deleted guild members (if member left server)
    """
    from src.ui.embeds import PollEmbedBase
    
    # Fetch poll data (3 queries total)
    poll = await Poll.get(id=poll_id)
    options = await PollOption.filter(poll_id=poll_id).order_by("position").all()
    all_votes = await Vote.filter(poll_id=poll_id).all()
    
    # Group votes by option for O(1) lookup
    votes_by_option = {}
    for vote in all_votes:
        if vote.option_id not in votes_by_option:
            votes_by_option[vote.option_id] = []
        votes_by_option[vote.option_id].append(vote)
    
    # Build fresh embed
    fresh_embed = PollEmbedBase(poll.question)
    fresh_embed.timestamp = datetime.now()
    
    # Add option fields with vote counts
    for index, option in enumerate(options):
        votes = votes_by_option.get(option.id, [])
        member_ids = {v.user_id for v in votes}
        members = {
            interaction.guild.get_member(mid)
            for mid in member_ids
            if interaction.guild.get_member(mid) is not None
        }
        
        vote_text = f"**{len(members)}** | {', '.join(m.display_name for m in members)}"
        fresh_embed.add_field(
            name=f"{NUMBER_EMOJIS[index]} {option.text}",
            value=vote_text,
            inline=False,
        )
    
    # Add end date if present
    if poll.end_date is not None:
        unix_time = discord.utils.format_dt(poll.end_date, "R")
        fresh_embed.add_field(
            name="",
            value=f"Anketa vyprší {unix_time}",
            inline=False,
        )
    
    return fresh_embed


def check_poll_creator(poll, interaction: discord.Interaction) -> bool:
    """Check if interaction user is the poll creator.
    
    Args:
        poll: Poll model instance.
        interaction: Discord interaction context.
        
    Returns:
        True if user created the poll, False otherwise.
    """
    return poll.creator_id == interaction.user.id


# ==================== Base Button Classes ====================


class PollManagementButton(discord.ui.Button):
    """Base class for poll management buttons (add, remove, close).
    
    Handles common initialization and attributes for all management buttons.
    Subclasses should only implement the callback logic.
    
    Attributes:
        poll: Poll model instance.
        options: List of PollOption instances.
        embed: Current poll embed.
        parent_view: Parent discord.ui.View containing this button.
    """

    def __init__(
        self,
        label: str,
        emoji: str,
        custom_id: str,
        poll,
        options,
        embed: PollEmbed,
        parent_view: discord.ui.View,
    ):
        """Initialize a poll management button.
        
        Args:
            label: Button display label.
            emoji: Button emoji.
            custom_id: Unique identifier for discord.py.
            poll: Poll model instance.
            options: List of PollOption instances.
            embed: Current poll embed.
            parent_view: Parent view containing this button.
        """
        self.poll = poll
        self.options = options
        self.embed = embed
        self.parent_view = parent_view
        
        super().__init__(
            label=label,
            emoji=emoji,
            custom_id=custom_id,
            row=4,
        )


# ==================== Vote Button ====================


class VoteButton(discord.ui.Button):
    """Button to cast or remove a vote on a poll option.
    
    When clicked, toggles the user's vote for this option. Behavior depends
    on the poll's `allow_multiple_votes` setting:
    - If False: User can only vote for one option (clicking another removes previous)
    - If True: User can vote for multiple options (clicking again removes vote)
    
    Attributes:
        poll_id: ID of the poll.
        option_id: ID of the poll option.
        _index: Position of option in the list (for emoji selection).
        embed: Current poll embed.
        
    Edge cases:
        - User clicking same option twice removes their vote
        - User voting for option A then B (multiple=False) removes vote from A
        - Rebuilds entire embed after each vote to prevent race conditions
    """

    LENTGH_STRING = 30

    def __init__(
        self,
        poll_id: int,
        option_id: int,
        index: int,
        label: str,
        emoji: str,
        embed: PollEmbed,
    ):
        """Initialize a vote button.
        
        Args:
            poll_id: Poll ID for database queries.
            option_id: Option ID this button represents.
            index: Position in options list (for emoji).
            label: Button label (option text).
            emoji: Number emoji (1️⃣, 2️⃣, etc).
            embed: Current poll embed.
        """
        display_label = (
            label if len(label) <= self.LENTGH_STRING else label[: self.LENTGH_STRING]
        )
        super().__init__(
            label=display_label,
            emoji=emoji,
            custom_id=f"vote:{poll_id}:{option_id}",
        )
        self.poll_id = poll_id
        self.option_id = option_id
        self._index = index
        self.embed = embed

    @property
    def index(self) -> int:
        """Get the option index for emoji selection."""
        return self._index

    async def toggle_vote(self, user_id: int) -> None:
        """Toggle vote for this option in the database.
        
        Args:
            user_id: Discord user ID voting.
            
        Edge cases:
            - If user already voted same option and multiple=True, removes vote
            - If user votes different option and multiple=False, removes old vote first
        """
        poll = await Poll.get(id=self.poll_id)

        if not poll.allow_multiple_votes:
            # Single vote mode: remove other votes by this user
            existing_same = await Vote.filter(
                poll_id=self.poll_id,
                option_id=self.option_id,
                user_id=user_id,
            ).first()
            if existing_same:
                await existing_same.delete()
            else:
                # Remove any other votes for this poll
                await Vote.filter(poll_id=self.poll_id, user_id=user_id).delete()
                await Vote.create(
                    poll_id=self.poll_id,
                    option_id=self.option_id,
                    user_id=user_id,
                )
        else:
            # Multiple vote mode: toggle this option
            existing = await Vote.filter(
                poll_id=self.poll_id,
                option_id=self.option_id,
                user_id=user_id,
            ).first()
            if existing:
                await existing.delete()
            else:
                await Vote.create(
                    poll_id=self.poll_id,
                    option_id=self.option_id,
                    user_id=user_id,
                )

    async def callback(self, interaction: discord.Interaction):
        """Handle button click - register vote and update display."""
        await self.toggle_vote(interaction.user.id)
        fresh_embed = await rebuild_and_display_poll(
            interaction, self.poll_id, self.embed
        )
        await interaction.response.edit_message(embed=fresh_embed)


# ==================== Management Buttons ====================


class NewOptionButton(PollManagementButton):
    """Button to add a new option to an active poll.
    
    Only the poll creator can use this button. Opens a modal for the user
    to enter the new option text. Enforces a 10-option limit.
    
    Edge cases:
        - Non-creator gets an error message
        - Shows error if poll already has 10 options
        - Modal submission adds button and rebuild embed
    """

    def __init__(self, poll, options, embed: PollEmbed, parent_view: discord.ui.View):
        """Initialize add option button."""
        super().__init__(
            label="Přidat novou možnost",
            emoji=ScoutEmojis.FLEUR_DE_LIS.value,
            custom_id=f"option_button::{poll.id}",
            poll=poll,
            options=options,
            embed=embed,
            parent_view=parent_view,
        )

    async def callback(self, interaction: Interaction):
        """Handle button click - show modal or permission error."""
        if not check_poll_creator(self.poll, interaction):
            await interaction.response.send_message(
                "Nemáš oprávnění přidat možnost.",
                ephemeral=True,
            )
            return

        if len(self.embed.fields) >= 10:
            await interaction.response.send_message(
                "Nemůžeš mít víc jak 10 možností!",
                ephemeral=True,
            )
            return

        from src.ui.modals import NewOptionModal

        modal = NewOptionModal(
            self.poll, self.options, self.embed, self.parent_view
        )
        await interaction.response.send_modal(modal)


class RemoveOptionButton(PollManagementButton):
    """Button to remove an option from the poll.
    
    Only the poll creator can use this button. Enforces that at least one
    option must remain. Deletes the option and all its votes, then rebuilds
    the button list with correct indices.
    
    Edge cases:
        - Non-creator gets an error message
        - Shows error if only one option remains
        - Rebuilds all vote buttons with new indices after removal
    """

    def __init__(self, poll, options, embed: PollEmbed, parent_view: discord.ui.View):
        """Initialize remove option button."""
        super().__init__(
            label="Odebrat možnost",
            emoji="❌",
            custom_id=f"remove_option_button::{poll.id}",
            poll=poll,
            options=options,
            embed=embed,
            parent_view=parent_view,
        )

    async def callback(self, interaction: Interaction):
        """Handle button click - show option selection or permission error."""
        if not check_poll_creator(self.poll, interaction):
            await interaction.response.send_message(
                "Nemáš oprávnění odebrat možnost.",
                ephemeral=True,
            )
            return

        if len(self.options) <= 1:
            await interaction.response.send_message(
                "Anketa musí mít alespoň jednu možnost!",
                ephemeral=True,
            )
            return

        from src.ui.modals import SelectOptionView

        view = SelectOptionView(
            self.poll, self.options, self.embed, self.parent_view
        )
        await interaction.response.send_message(
            "Vyber možnost k odebrání:",
            view=view,
            ephemeral=True,
        )


class ClosePollButton(PollManagementButton):
    """Button to close the poll and display results.
    
    Only the poll creator can use this button. When clicked, shows sorting
    options for the final results (original order, highest votes, lowest votes).
    
    Edge cases:
        - Non-creator gets an error message
        - Marks poll as "ended" in database
        - Sends results as new message in channel
    """

    def __init__(self, poll, options, embed: PollEmbed, parent_view: discord.ui.View):
        """Initialize close poll button."""
        super().__init__(
            label="Ukončit anketu",
            emoji="🏁",
            custom_id=f"close_poll_button::{poll.id}",
            poll=poll,
            options=options,
            embed=embed,
            parent_view=parent_view,
        )

    async def callback(self, interaction: Interaction):
        """Handle button click - show sorting options or permission error."""
        if not check_poll_creator(self.poll, interaction):
            await interaction.response.send_message(
                "Nemáš oprávnění ukončit anketu.",
                ephemeral=True,
            )
            return

        from src.ui.modals import ClosePollView

        view = ClosePollView(
            self.poll, self.options, self.embed, self.parent_view
        )
        await interaction.response.send_message(
            "Jak chceš seřadit odpovědi?",
            view=view,
            ephemeral=True,
        )


class SubscribeButton(discord.ui.Button):
    """Button to subscribe to poll result notifications.
    
    When poll ends (manually or by time), all subscribers receive a DM
    with the final results. The poll creator is always notified.
    
    Clicking the button toggles subscription status. Visual feedback is
    provided via ephemeral message indicating subscription status.
    
    Attributes:
        poll: Poll model instance.
        
    Edge cases:
        - Creator can also subscribe (in addition to auto-notification)
        - Unsubscribing removes user from PollSubscriber table
        - Safe if user has DMs disabled (notification fails silently)
    """

    def __init__(self, poll):
        """Initialize subscribe button.
        
        Args:
            poll: Poll model instance.
        """
        self.poll = poll
        super().__init__(
            label="Sledovat",
            emoji="🔔",
            custom_id=f"subscribe_button::{poll.id}",
            row=4,
        )

    async def toggle_subscription(self, user_id: int) -> bool:
        """Toggle user's subscription status in database.
        
        Args:
            user_id: Discord user ID to toggle subscription for.
            
        Returns:
            True if now subscribed, False if now unsubscribed.
        """
        existing = await PollSubscriber.filter(
            poll_id=self.poll.id,
            user_id=user_id,
        ).first()

        if existing:
            await existing.delete()
            return False
        else:
            await PollSubscriber.create(
                poll_id=self.poll.id,
                user_id=user_id,
            )
            return True

    async def callback(self, interaction: discord.Interaction):
        """Handle button click - toggle subscription and show feedback."""
        is_subscribed = await self.toggle_subscription(interaction.user.id)

        if is_subscribed:
            message = "✅ Nyní budeš dostávat notifikace!"
        else:
            message = "❌ Notifikace vypnuty"

        await interaction.response.send_message(
            message,
            ephemeral=True,
        )
