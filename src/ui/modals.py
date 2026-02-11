import discord
from datetime import datetime

from src.ui.embeds import PollEmbed
from src.ui.emojis import NUMBER_EMOJIS
from src.models import PollOption, Vote, Poll, PollSubscriber
from src.ui.button import rebuild_and_display_poll

from loguru import logger

# ==================== Helper Functions ====================


async def get_option_vote_counts(
    poll_id: int,
) -> dict:
    """Fetch and group all votes by option ID.
    
    Groups votes from the database into a dictionary for efficient lookup.
    
    Args:
        poll_id: ID of the poll to fetch votes for.
        
    Returns:
        Dictionary mapping option_id to list of Vote objects.
    """
    all_votes = await Vote.filter(poll_id=poll_id).all()
    
    votes_by_option = {}
    for vote in all_votes:
        if vote.option_id not in votes_by_option:
            votes_by_option[vote.option_id] = []
        votes_by_option[vote.option_id].append(vote)
    
    return votes_by_option


async def notify_poll_subscribers(
    poll: Poll,
    results_embed: discord.Embed,
    bot,
) -> None:
    """Send poll results to all subscribers and poll creator via DM.
    
    Fetches all PollSubscriber entries and the poll creator, then attempts
    to send the results embed to each user via DM. Failed DM sends are
    silently ignored (e.g., if user has DMs disabled).
    
    Args:
        poll: Poll model instance.
        results_embed: Formatted embed with poll results.
        bot: Bot instance (for fetching users and sending DMs).
        
    Edge cases:
        - Poll creator receives notification regardless of subscription
        - User has DMs disabled: notification sent silently fails
        - User is both creator and subscriber: receives one DM
    """
    # Get all subscribers
    subscribers = await PollSubscriber.filter(poll_id=poll.id).all()
    subscriber_ids = {sub.user_id for sub in subscribers}
    
    # Always include creator
    notify_ids = subscriber_ids | {poll.creator_id}
    
    # Send DMs to all users
    for user_id in notify_ids:
        try:
            user = await bot.fetch_user(user_id)
            await user.send(embed=results_embed)
        except Exception as e:
            logger.debug(f"Failed to send DM to user {user_id}: {e}")


# ==================== New Option Modal ====================


class NewOptionModal(discord.ui.Modal):
    """Modal for adding a new option to an active poll.
    
    Accepts a single text input for the new option text. When submitted,
    creates a PollOption in the database, adds a new button to the view,
    and updates the embed.
    
    Attributes:
        poll: Poll model instance.
        options: List of PollOption instances.
        embed: Current poll embed.
        parent_view: Parent view containing vote buttons.
        new_option: discord.ui.TextInput for the option text.
        
    Edge cases:
        - Inserts new field before timestamp if present (maintains ordering)
        - Keeps local options list in sync for button reference
    """

    def __init__(
        self,
        poll,
        options,
        embed: PollEmbed,
        parent_view: discord.ui.View,
    ):
        """Initialize new option modal.
        
        Args:
            poll: Poll model instance.
            options: List of PollOption instances.
            embed: Current poll embed.
            parent_view: Parent view containing this modal's parent button.
        """
        super().__init__(title="Přidání nové možnosti do ankety")

        self.new_option = discord.ui.TextInput(
            label="Jméno nové možnosti",
            min_length=1,
            max_length=255,
            required=True,
            placeholder="Vymysli příma možnost!",
            style=discord.TextStyle.short,
        )
        self.add_item(self.new_option)

        self.embed = embed
        self.poll = poll
        self.options = options
        self.parent_view = parent_view

    async def on_submit(self, interaction: discord.Interaction):
        """Handle modal submission - create option and update view."""
        em = await self._add_option_to_embed(interaction)
        await interaction.response.edit_message(embed=em, view=self.parent_view)

    async def _add_option_to_embed(
        self, interaction: discord.Interaction
    ) -> discord.Embed:
        """Create option in database and add button to view.
        
        Args:
            interaction: Discord interaction context.
            
        Returns:
            Updated embed with new option field.
        """
        # Compute insertion index (before timestamp if present)
        has_timestamp = (
            self.embed.fields
            and self.embed.fields[-1].value.startswith("Anketa vyprší")
        )
        
        if has_timestamp:
            insertion_index = len(self.embed.fields) - 1
            emoji_index = insertion_index
        else:
            insertion_index = len(self.embed.fields)
            emoji_index = len(self.embed.fields)

        # Create new option in database
        position = len(self.options)
        new_opt = await PollOption.create(
            poll_id=self.poll.id,
            text=self.new_option.value,
            position=position,
            created_by=interaction.user.id,
        )

        # Add vote button for new option
        from src.ui.button import VoteButton

        new_btn = VoteButton(
            poll_id=self.poll.id,
            option_id=new_opt.id,
            index=insertion_index,
            label=new_opt.text,
            emoji=NUMBER_EMOJIS[emoji_index],
            embed=self.embed,
        )
        self.parent_view.add_item(new_btn)

        # Update embed with new option field
        self.options.append(new_opt)
        self.embed.insert_field_at(
            index=insertion_index,
            name=f"{NUMBER_EMOJIS[emoji_index]} {self.new_option.value}",
            value="**0** | ",
            inline=False,
        )

        return self.embed


# ==================== Remove Option View ====================


class SelectOptionView(discord.ui.View):
    """View with select dropdown to remove poll options.
    
    Displays a dropdown with all poll options. When user selects one,
    deletes that option and all its votes, rebuilds buttons with correct
    indices, and updates the poll message.
    
    Attributes:
        poll: Poll model instance.
        options: List of PollOption instances (reference).
        embed: Current poll embed.
        parent_view: Parent view containing vote buttons.
        select: discord.ui.Select dropdown component.
        
    Edge cases:
        - Keeps reference to original options list (mutates when option removed)
        - Rebuilds ALL vote buttons to reindex emojis correctly
        - Updates original poll message, not the ephemeral selector
    """

    def __init__(
        self,
        poll,
        options,
        embed: PollEmbed,
        parent_view: discord.ui.View,
    ):
        """Initialize option removal view.
        
        Args:
            poll: Poll model instance.
            options: List of PollOption instances (will be mutated).
            embed: Current poll embed.
            parent_view: Parent view containing vote buttons.
        """
        super().__init__(timeout=180)
        self.poll = poll
        self.options = options  # Reference, not copy
        self.embed = embed
        self.parent_view = parent_view

        # Build select options from current options list
        select_options = [
            discord.SelectOption(
                label=opt.text[:100],  # Discord max label length
                value=str(opt.id),
            )
            for opt in self.options
        ]

        self.select = discord.ui.Select(
            placeholder="Vyber možnost k odebrání",
            options=select_options,
            custom_id=f"remove_select::{poll.id}",
        )
        self.select.callback = self.on_select
        self.add_item(self.select)

    async def on_select(self, interaction: discord.Interaction):
        """Handle option selection - delete and rebuild."""
        await interaction.response.defer()

        selected_id = int(self.select.values[0])

        # Find the option to remove
        option_to_remove = next(
            (opt for opt in self.options if opt.id == selected_id), None
        )
        if not option_to_remove:
            await interaction.followup.send(
                "Možnost nenalezena!",
                ephemeral=True,
            )
            return

        # Delete from database (cascade deletes votes)
        await Vote.filter(option_id=selected_id).delete()
        await option_to_remove.delete()

        # Update local options list
        self.options.remove(option_to_remove)

        # Rebuild vote buttons with correct indices
        await self._rebuild_vote_buttons()

        # Update original poll message
        await self._update_poll_message(interaction)

        await interaction.followup.send(
            "✅ Možnost odebrána!",
            ephemeral=True,
        )
        self.stop()

    async def _rebuild_vote_buttons(self):
        """Remove old vote buttons and create new ones with correct indices."""
        from src.ui.button import VoteButton

        # Remove all vote buttons
        vote_buttons = [
            item
            for item in self.parent_view.children
            if isinstance(item, VoteButton)
        ]
        for btn in vote_buttons:
            self.parent_view.remove_item(btn)

        # Add new buttons with correct indices
        for index, option in enumerate(self.options):
            new_btn = VoteButton(
                poll_id=self.poll.id,
                option_id=option.id,
                index=index,
                label=option.text,
                emoji=NUMBER_EMOJIS[index],
                embed=self.embed,
            )
            self.parent_view.add_item(new_btn)

    async def _update_poll_message(self, interaction: discord.Interaction):
        """Rebuild embed and update original poll message."""
        try:
            fresh_embed = await rebuild_and_display_poll(
                interaction, self.poll.id, self.embed
            )
            
            channel = interaction.client.get_channel(self.poll.channel_id)
            poll_message = await channel.fetch_message(self.poll.message_id)
            await poll_message.edit(embed=fresh_embed, view=self.parent_view)
        except Exception as e:
            # Silently fail - user got confirmation message already
            pass


# ==================== Close Poll View ====================


class ClosePollView(discord.ui.View):
    """View with select dropdown to close poll and display results.
    
    Allows poll creator to choose result sorting order:
    - Original: Keep option order as-is
    - Highest: Sort by vote count descending
    - Lowest: Sort by vote count ascending
    
    Marks poll as ended in database and sends results as new message.
    
    Attributes:
        poll: Poll model instance.
        options: List of PollOption instances.
        embed: Current poll embed.
        parent_view: Parent view (unused but kept for consistency).
        select: discord.ui.Select dropdown component.
        
    Edge cases:
        - Handles polls with no votes (shows 0 votes per option)
        - Filters out deleted guild members from vote display
        - Results sent as new message in channel, not poll message edit
    """

    def __init__(
        self,
        poll,
        options,
        embed: PollEmbed,
        parent_view: discord.ui.View,
    ):
        """Initialize poll closing view.
        
        Args:
            poll: Poll model instance.
            options: List of PollOption instances.
            embed: Current poll embed.
            parent_view: Parent view (for consistency with other views).
        """
        super().__init__(timeout=180)
        self.poll = poll
        self.options = options
        self.embed = embed
        self.parent_view = parent_view

        # Create sort options
        sort_options = [
            discord.SelectOption(
                label="Zachovat původní pořadí",
                value="original",
                emoji="📋",
            ),
            discord.SelectOption(
                label="Od nejvíce hlasů",
                value="highest",
                emoji="⬇️",
            ),
            discord.SelectOption(
                label="Od nejméně hlasů",
                value="lowest",
                emoji="⬆️",
            ),
        ]

        self.select = discord.ui.Select(
            placeholder="Vyber způsob řazení",
            options=sort_options,
            custom_id=f"close_sort::{poll.id}",
        )
        self.select.callback = self.on_select
        self.add_item(self.select)

    async def on_select(self, interaction: discord.Interaction):
        """Handle poll closing with selected sorting."""
        await interaction.response.defer()

        sort_by = self.select.values[0]

        # Mark poll as ended
        self.poll.status = "ended"
        await self.poll.save()

        # Build and send results
        try:
            results_embed = await self._build_results_embed(sort_by, interaction)
            
            # Send results in channel
            channel = interaction.client.get_channel(self.poll.channel_id)
            await channel.send(embed=results_embed)
            
            # Send DMs to all subscribers and creator
            await notify_poll_subscribers(
                self.poll,
                results_embed,
                interaction.client,
            )
            
            await interaction.followup.send(
                "✅ Anketa ukončena a výsledky odeslány!",
                ephemeral=True,
            )
        except Exception as e:
            await interaction.followup.send(
                f"Chyba: {e}",
                ephemeral=True,
            )

        self.stop()

    async def _build_results_embed(
        self, sort_by: str, interaction: discord.Interaction
    ) -> discord.Embed:
        """Build ranked results embed with selected sorting.
        
        Args:
            sort_by: Sort method ("original", "highest", or "lowest").
            interaction: Discord interaction context.
            
        Returns:
            Formatted results embed showing ranked options.
        """
        from src.ui.embeds import PollEmbedBase

        results_embed = PollEmbedBase(f"📊 Výsledky: {self.poll.question}")
        results_embed.timestamp = datetime.now()
        results_embed.set_footer(text="Anketa ukončena ✅")

        # Get vote counts
        votes_by_option = await get_option_vote_counts(self.poll.id)

        # Sort options based on selection
        sorted_options = list(self.options)
        if sort_by == "highest":
            sorted_options.sort(
                key=lambda opt: len(votes_by_option.get(opt.id, [])),
                reverse=True,
            )
        elif sort_by == "lowest":
            sorted_options.sort(
                key=lambda opt: len(votes_by_option.get(opt.id, []))
            )

        # Add results to embed
        for rank, option in enumerate(sorted_options, 1):
            votes = votes_by_option.get(option.id, [])
            member_ids = {v.user_id for v in votes}
            members = {
                interaction.guild.get_member(mid)
                for mid in member_ids
                if interaction.guild.get_member(mid) is not None
            }

            vote_count = len(members)
            voter_names = ", ".join(m.display_name for m in members)
            vote_text = f"**{vote_count}** hlasů | {voter_names}"

            results_embed.add_field(
                name=f"#{rank} {option.text}",
                value=vote_text,
                inline=False,
            )

        return results_embed
