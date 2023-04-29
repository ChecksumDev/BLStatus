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

from datetime import datetime, timedelta
from logging import getLogger
from random import choice
from typing import TYPE_CHECKING, Optional

from aiosqlite import connect as sql_connect
from nextcord import Color, Embed, TextChannel
from nextcord.ext.commands import Cog
from websockets.client import connect
from websockets.exceptions import (ConnectionClosed, ConnectionClosedError,
                                   ConnectionClosedOK)

from src.static import (CLOUDFLARE_PNG, CONNECTING_PNG, DATABASE, OFFLINE_PNG,
                        ONLINE_PNG, quotes)

if TYPE_CHECKING:
    from src.main import Client


def setup(client: "Client"):
    client.add_cog(WatchDog(client))


class WatchDog(Cog):
    def __init__(self, client: "Client"):
        self.client = client
        self.logger = getLogger("watchdog")

        self.last_status_check = datetime.now() - timedelta(minutes=1)
        self.client.loop.create_task(self.connect_websocket())

    async def connect_websocket(self):
        """Connects to the websocket"""
        async for websocket in connect('wss://api.beatleader.xyz/scores', ping_interval=5, ping_timeout=5):
            # We have connected to the websocket
            self.logger.info("Connected to websocket")
            await self.report_websocket("connected")

            try:
                while True:
                    _ = await websocket.recv()
            except ConnectionClosedOK:  # The websocket has closed normally
                self.logger.info("Websocket closed gracefully")

                await self.report_websocket("graceful")

            except ConnectionClosedError as cle:  # The websocket has closed with an error
                self.logger.error(
                    f"Websocket closed with an error: {cle.code} {cle.reason}")

                if "cloudflare" in str(cle.reason).lower():
                    return await self.report_websocket("cloudflare", cle)

                await self.report_websocket("error", cle)

    async def report_websocket(self, event_type: str, exception: Optional[ConnectionClosed] = None):
        """Reports the status of the websocket to the status channel"""

        if exception is None:
            exception_reason = "No exception was provided"
        else:
            exception_reason = str(exception)

        match event_type:
            case "connected":
                status_message = f"The websocket has connected successfully: ```{choice(quotes)}```"
                thumbnail = ONLINE_PNG
                color = Color.dark_green()
            case "graceful":
                status_message = "The websocket has closed gracefully, attempting to reconnect"
                thumbnail = CONNECTING_PNG
                color = Color.dark_blue()
            case "error":
                status_message = f"The websocket has closed with an error: ```{exception_reason}```"
                thumbnail = OFFLINE_PNG
                color = Color.dark_red()
            case "cloudflare":
                status_message = "The websocket has closed with a Cloudflare error"
                thumbnail = CLOUDFLARE_PNG
                color = Color.dark_orange()
            case "unknown":
                status_message = f"An unknown error has occured: ```{exception_reason}```"
                thumbnail = OFFLINE_PNG
                color = Color.dark_purple()
            case _:
                raise ValueError(f"Invalid type: {type}")

        embed = Embed(
            title="Websocket Status",
            description=status_message,
            color=color,
            timestamp=datetime.now()
        )

        embed.set_thumbnail(url=thumbnail)

        # Get all guilds status channels and send to them
        async with sql_connect(DATABASE) as db:
            async with db.execute("SELECT alert_channel FROM settings") as cursor:
                for row in await cursor.fetchall():
                    channel = await self.client.fetch_channel(row[0])

                    if isinstance(channel, TextChannel):
                        await channel.send(embed=embed)
