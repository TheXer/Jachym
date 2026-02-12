from discord.ext import commands
import asyncio
import discord
from tortoise import Tortoise
from loguru import logger
from os import getenv, listdir
from discord.ext.commands import ExtensionNotFound, ExtensionFailed, ExtensionAlreadyLoaded

from src.models import Poll, PollStatus
from src.ui.embeds import PollEmbed
from src.ui.poll_view import PollView
from src.helpers import timeit

class Jachym(commands.Bot):
    MY_BIRTHDAY = "27.12.2020"
    OWNER_ID = 337971071485607936

    def __init__(self) -> None:
        super().__init__(
            command_prefix=commands.when_mentioned_or("!"),
            intents=discord.Intents.all(),
            owner_id=self.OWNER_ID,
        )
        self.db_initialized = False
        self._poll_views_restored = False
        # Semaphore to limit concurrent message edits (avoid rate limit)
        self._message_edit_semaphore = asyncio.Semaphore(10)


    async def setup_hook(self) -> None:
        """Called when the bot is starting up."""
        logger.info("Getting setup ready...")

        # Initialize Tortoise ORM
        await self.init_database()

        # Load extensions (cogs)
        await self.load_extensions()

        logger.success("Setup ready!")

    async def init_database(self) -> None:
        """Initialize Tortoise ORM connection."""
        try:
            await Tortoise.init(
                db_url=self.get_database_url(),
                modules={"models": ["src.models"]},
            )
            # Generate schemas if they don't exist
            await Tortoise.generate_schemas()
            
            self.db_initialized = True
            logger.success("Database connected successfully!")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            self.db_initialized = False
            raise

    @staticmethod
    def get_database_url() -> str:
        """Build database URL from environment variables."""
        db_type = getenv("DB_TYPE", "sqlite")
        
        if db_type == "sqlite":
            db_path = getenv("DB_PATH", "db.sqlite3")
            return f"sqlite://{db_path}"
        
        elif db_type == "mysql":
            db_url = getenv("DB_URL", None)
            if not db_url:
                raise ValueError("DB_URL environment variable is required for MySQL")
            
            return db_url
        
        else:
            raise ValueError(f"Unsupported DB_TYPE: {db_type}")

    @timeit
    async def restore_poll_views(self) -> None:
        """Restore persistent views for all active polls.
        
        Processes polls sequentially with a conservative delay between API calls
        to respect Discord's strict per-message-channel rate limits.
        """
        active_polls = await Poll.filter(status=PollStatus.ACTIVE).all()
        
        restored_count = 0
        
        for poll in active_polls:
            try:
                # Get the channel
                channel = self.get_channel(poll.channel_id)
                if not channel:
                    logger.warning(f"Channel {poll.channel_id} not found for poll {poll.id}")
                    continue

                
                embed = PollEmbed(poll.question, options=await poll.options.all(), created_at=poll.created_at)  

                # Create and attach the view
                view = PollView(poll=poll, options=await poll.options.all(), embed=embed)
                
                self.add_view(view=view, message_id=poll.message_id)
                restored_count += 1
                logger.debug(f"Restored view for poll {poll.id}")

            except Exception as e:
                logger.error(f"Error restoring poll {poll.id}: {e}")
        
        logger.success(f"Restored {restored_count} active poll views!")

    async def set_presence(self) -> None:
        """Update bot presence with server and poll count."""
        active_count = await Poll.filter(status=PollStatus.ACTIVE).count()
        
        activity_name = f"Jsem na {len(self.guilds)} serverech a mám spuštěno {active_count} anket!"
        await self.change_presence(activity=discord.Game(name=activity_name))

    async def load_extensions(self) -> None:
        """Load all cogs from the cogs/ directory."""
        
        for filename in listdir("cogs/"):
            if filename.endswith(".py") and not filename.startswith("_"):
                try:
                    await self.load_extension(f"cogs.{filename[:-3]}")
                    logger.success(f"{filename[:-3]} loaded successfully")
                except (ExtensionNotFound, ExtensionFailed, ExtensionAlreadyLoaded) as error:
                    logger.error(f"Failed to load {filename}: {error}")

    async def on_ready(self) -> None:
        """Called when bot is fully ready and connected to Discord."""
        await self.set_presence()
        
        # Restore poll views only once when bot first becomes ready
        if not self._poll_views_restored:
            self._poll_views_restored = True
            await self.restore_poll_views()
        
        logger.success(f"Bot online as {self.user}!")

    async def close(self) -> None:
        """Cleanup when bot shuts down."""
        logger.info("Shutting down...")
        
        # Close Tortoise connections
        await Tortoise.close_connections()
        logger.success("Database connections closed")
        
        # Call parent close
        await super().close()