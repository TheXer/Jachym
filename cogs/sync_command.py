from typing import TYPE_CHECKING, Literal

import discord
from discord.ext import commands
from discord.ext.commands import Context, Greedy

if TYPE_CHECKING:
    from src.jachym import Jachym


class SyncSlashCommands(commands.Cog):
    def __init__(self, bot: "Jachym"):
        self.bot = bot

    @commands.command()
    @commands.guild_only()
    @commands.is_owner()
    async def sync(
        self,
        ctx: Context,
        guilds: Greedy[discord.Guild],
        spec: Literal["-", "*", "^"] | None = None,
    ) -> None:
        """
        A command to sync all slash commands to servers user requires. Works like this:
        !sync
            global sync - syncs all slash commands with all guilds
        !sync -
            sync current guild
        !sync *
            copies all global app commands to current guild and syncs
        !sync ^
            clears all commands from the current guild target and syncs (removes guild commands)
        !sync id_1 id_2
            syncs guilds with id 1 and 2

        Args:
            ctx: commands.Context
            guilds: Greedy[discord.Object]
            spec: Optional[Literal]

        Returns: Synced slash command

        """

        if not guilds:
            if spec == "-":
                synced = await self.bot.tree.sync(guild=ctx.guild)
            elif spec == "*":
                self.bot.tree.copy_global_to(guild=ctx.guild)
                synced = await self.bot.tree.sync(guild=ctx.guild)
            elif spec == "^":
                self.bot.tree.clear_commands(guild=ctx.guild)
                await self.bot.tree.sync(guild=ctx.guild)
                synced = []
            else:
                synced = await self.bot.tree.sync()

            await ctx.send(
                f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}",
            )
            return

        ret = 0
        for guild in guilds:
            try:
                await self.bot.tree.sync(guild=guild)
            except discord.HTTPException:
                pass
            else:
                ret += 1

        await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")


async def setup(bot):
    await bot.add_cog(SyncSlashCommands(bot))
