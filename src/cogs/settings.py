#     BLStatus - A Discord bot that displays the status of BeatLeader.
#     Copyright (C) 2023  Checksum
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.

from typing import TYPE_CHECKING, Optional

from aiosqlite import connect
from nextcord import Interaction, slash_command
from nextcord.channel import TextChannel
from nextcord.ext import application_checks
from nextcord.ext.commands import Cog

from src.static import DATABASE

if TYPE_CHECKING:
    from src.main import Client


def setup(client: "Client"):
    client.add_cog(Settings(client))


class Settings(Cog):
    def __init__(self, client: "Client"):
        self.client = client

    @Cog.listener()
    async def on_ready(self):
        async with connect(DATABASE) as db:
            await db.execute(
                "CREATE TABLE IF NOT EXISTS settings (guild_id INTEGER PRIMARY KEY, alert_channel INTEGER)")
            await db.commit()

    @slash_command(name="settings")
    @application_checks.guild_only()
    @application_checks.check_any(application_checks.has_guild_permissions(manage_guild=True),
                                  application_checks.is_owner())
    async def settings(self, ctx: Interaction):
        pass  # This is a subcommand, so it doesn't need a function body

    @settings.subcommand(name="alert_channel")
    @application_checks.guild_only()
    @application_checks.check_any(application_checks.has_guild_permissions(manage_guild=True),
                                  application_checks.is_owner())
    async def alert_channel(self, ctx: Interaction, channel: Optional[TextChannel]):
        """Sets the channel where BeatLeader alerts are sent"""
        if ctx.guild is None:
            return await ctx.send("This command can only be used in a guild", ephemeral=True)

        # If no channel is specified, return the current alert channel
        if channel is None:
            async with connect(DATABASE) as db:
                async with db.execute("SELECT alert_channel FROM settings WHERE guild_id = ?",
                                      (ctx.guild.id,)) as cursor:
                    alert_channel = await cursor.fetchone()
                    if alert_channel is None:
                        return await ctx.send("No alert channel has been set", ephemeral=True)

                    return await ctx.send(f"The alert channel is <#{alert_channel[0]}>", ephemeral=True)

        # Otherwise, set the alert channel
        async with connect(DATABASE) as db:
            await db.execute(
                "INSERT INTO settings (guild_id, alert_channel) VALUES (?, ?) ON CONFLICT (guild_id) DO UPDATE SET alert_channel = ?",
                (ctx.guild.id, channel.id, channel.id))
            await db.commit()

        await ctx.send(f"Set the alert channel to {channel.mention}", ephemeral=True)
