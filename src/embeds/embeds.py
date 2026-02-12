import json
import pathlib
from datetime import datetime

import discord
from discord.colour import Color, Colour

from src.ui.emojis import NUMBER_EMOJIS, ScoutEmojis
from typing import Iterable


class ErrorMessage(discord.Embed):
    """Whether an error occurs, this embed is sent."""

    def __init__(self, message: str):
        title = "⚠️ Jejda, někde se stala chyba..."

        description = (
            f"{message}\n\n"
            f"{ScoutEmojis.FLEUR_DE_LIS.value} *Pokud máš pocit, že tohle by chyba být neměla, "
            f"napiš [sem](https://github.com/TheXer/Jachym/issues/new/choose)*"
        )

        self.set_footer(text="Uděláno s ♥!")

        super().__init__(
            title=title,
            description=description,
            colour=Colour.red(),
            timestamp=datetime.now(),
        )


class PollEmbedBase(discord.Embed):
    def __init__(self, question) -> None:
        super().__init__(title=f"📊 {question}", colour=Color.blue())
        self.set_footer(text="Momentální verze běží na beta verzi! Očekávej nějaké chyby sem a tam.")


class ManagedPollEmbed(PollEmbedBase):
    """Centralized embed manager for poll embeds with special field handling.
    
    This embed automatically manages:
    - Option fields (numbered 1️⃣, 2️⃣, etc.)
    - Special fields like the end date timestamp (always kept at the bottom)
    - Proper indexing when options are added or removed
    - Field insertion without corruption
    
    Methods like add_option(), remove_option(), etc., ensure:
    - Special fields (end_date, etc.) are always moved down
    - Emoji indices stay correct
    - No edge cases or format changes across different button/modal operations
    
    All buttons and modals should use this embed class.
    """
    
    # Special field markers (their value patterns)
    SPECIAL_FIELDS = {
        "end_date": lambda v: v.startswith("Anketa vyprší"),
    }
    
    def __init__(self, question: str, options: Iterable | None = None, created_at: datetime | None = None):
        super().__init__(question)
        self.timestamp = datetime.now()
        self._end_date_unix = None
        
        # Add initial options if provided
        if options:
            self._add_initial_options(options)
        
        if created_at is not None:
            self.set_end_date(created_at)
    
    def _add_initial_options(self, options: Iterable) -> None:
        """Add initial options during embed creation."""
        for index, option in enumerate(options):
            label = option.text if hasattr(option, "text") else str(option)
            self.add_field(
                name=f"{NUMBER_EMOJIS[index]} {label}",
                value="**0** |",
                inline=False,
            )
    
    @staticmethod
    def is_special_field(field: discord.Embed.Field) -> bool:
        """Check if a field is a special field (non-option field)."""
        for field_type, check_func in ManagedPollEmbed.SPECIAL_FIELDS.items():
            if check_func(field.value):
                return True
        return False
    
    def get_option_field_count(self) -> int:
        """Get count of option fields (excluding special fields)."""
        return sum(1 for field in self.fields if not self.is_special_field(field))
    
    def get_end_date_field_index(self) -> int | None:
        """Get the index of the end_date field, or None if not present."""
        for i, field in enumerate(self.fields):
            if field.value.startswith("Anketa vyprší"):
                return i
        return None
    
    def set_end_date(self, end_date: datetime) -> None:
        """Set or update the end date field. Always places it at the end."""
        # Remove existing end_date field if present
        end_date_idx = self.get_end_date_field_index()
        if end_date_idx is not None:
            self.fields.pop(end_date_idx)
        
        # Add new end_date field at the end
        unix_time = discord.utils.format_dt(end_date, "R")
        self.add_field(
            name="",
            value=f"Anketa vyprší {unix_time}",
            inline=False,
        )
        self._end_date_unix = end_date
    
    def add_option(self, text: str) -> int:
        """Add a new option field before any special fields.
        
        Returns:
            The emoji index of the newly added option.
        """
        option_count = self.get_option_field_count()
        
        # Find insertion point (before special fields)
        end_date_idx = self.get_end_date_field_index()
        if end_date_idx is not None:
            # Insert before end_date field
            insertion_idx = end_date_idx
        else:
            # Append at the end
            insertion_idx = len(self.fields)
        
        # Insert the new option field
        emoji = NUMBER_EMOJIS[option_count]
        self.insert_field_at(
            index=insertion_idx,
            name=f"{emoji} {text}",
            value="**0** | ",
            inline=False,
        )
        
        return option_count
    
    def remove_option(self, option_index: int) -> None:
        """Remove an option field by its index (0-based).
        
        This will automatically reindex the emojis of all options after the removed one.
        """
        if option_index >= self.get_option_field_count():
            raise IndexError(f"Option index {option_index} out of range")
        
        # Find and remove the option field
        removed_count = 0
        for i, field in enumerate(self.fields):
            if not self.is_special_field(field):
                if removed_count == option_index:
                    self.fields.pop(i)
                    break
                removed_count += 1
        
        # Update emojis for remaining options
        self._reindex_option_emojis()
    
    def update_option_text(self, option_index: int, new_text: str) -> None:
        """Update the text of an option field."""
        option_count = 0
        for i, field in enumerate(self.fields):
            if not self.is_special_field(field):
                if option_count == option_index:
                    emoji = NUMBER_EMOJIS[option_count]
                    self.fields[i].name = f"{emoji} {new_text}"
                    return
                option_count += 1
        
        raise IndexError(f"Option index {option_index} out of range")
    
    def update_option_votes(self, option_index: int, vote_text: str) -> None:
        """Update the vote count/display for an option field.
        
        Args:
            option_index: 0-based index of the option
            vote_text: The value to display (e.g., "**5** | Alice, Bob")
        """
        option_count = 0
        for i, field in enumerate(self.fields):
            if not self.is_special_field(field):
                if option_count == option_index:
                    self.fields[i].value = vote_text
                    return
                option_count += 1
        
        raise IndexError(f"Option index {option_index} out of range")
    
    def get_all_option_fields(self) -> list[tuple[int, discord.Embed.Field]]:
        """Get all option fields with their indices.
        
        Returns:
            List of (option_index, field) tuples for all option fields.
        """
        option_fields = []
        option_index = 0
        for field in self.fields:
            if not self.is_special_field(field):
                option_fields.append((option_index, field))
                option_index += 1
        return option_fields
    
    def _reindex_option_emojis(self) -> None:
        """Re-assign emoji numbers to all option fields (called after removals)."""
        option_index = 0
        for i, field in enumerate(self.fields):
            if not self.is_special_field(field):
                # Extract text without emoji prefix
                # Format is "emoji text", so split and keep from second part
                emoji_and_text = field.name
                # Get text without current emoji
                text_only = emoji_and_text[2:].strip() if len(emoji_and_text) > 2 else emoji_and_text
                
                # Re-assign correct emoji
                new_emoji = NUMBER_EMOJIS[option_index]
                self.fields[i].name = f"{new_emoji} {text_only}"
                option_index += 1





class EmbedFromJSON(discord.Embed):
    PATH = pathlib.Path("src/text_json/cz_text.json")
    PICTURE = discord.File("fotky/LogoPotkani.png", filename="LogoPotkani.png")

    def __init__(self):
        super().__init__(colour=Color.blue())

    @classmethod
    def add_fields_from_json(cls, root_path):
        with pathlib.Path.open(cls.PATH) as f:
            text = json.load(f)[root_path]
            em = EmbedFromJSON().from_dict(text)
            em.set_thumbnail(url="attachment://LogoPotkani.png")
            return em
