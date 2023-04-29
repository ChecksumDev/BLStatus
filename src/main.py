from json import load
from logging import INFO, basicConfig, getLogger
from os import environ, listdir
from platform import system

from aiosqlite import connect as sql_connect
from dotenv import load_dotenv
from nextcord import Embed, Game, Intents, Color, Status, TextChannel
from nextcord.errors import ApplicationError
from nextcord.ext.commands import Bot
from nextcord.interactions import Interaction

from static import DATABASE

if system() == "Linux":
    try:
        import uvloop

        uvloop.install()
    except ModuleNotFoundError:
        print("BLStatus is running on Linux and uvloop is missing.\nInstall uvloop using pip install uvloop")
        exit(1)

load_dotenv()  # Load environment variables from .env file
basicConfig(level=INFO)  # Set logging level to INFO


class Client(Bot):
    def __init__(self, *args, **kwargs):
        # There are no command prefixes, the bot only responds to application commands (slash commands)
        super().__init__(*args, **kwargs, intents=Intents.all())

        self.logger = getLogger("client")
        with open("version.json", "r") as f:
            self.version = load(f)["version"]

        cogs = ["cogs." + x[:-3]
                for x in listdir("src/cogs") if x.endswith(".py")]
        for cog in cogs:
            try:
                self.load_extension(cog)
                self.logger.info(f"Loaded cog {cog}")
            except Exception as e:
                self.logger.error(f"Failed to load cog {cog}: {e}")

    async def on_ready(self):
        if self.user:
            self.logger.info(
                f"Logged in as {self.user} ({self.user.id}) on {len(self.guilds)} guilds")
            await self.change_presence(activity=Game(name="Beat Saber"), status=Status.idle)

        async with sql_connect(DATABASE) as conn:
            # Initialize the database
            async with conn.execute("CREATE TABLE IF NOT EXISTS meta (version TEXT)") as cursor:
                await cursor.fetchone()

            # Check if the database is up-to-date
            async with conn.execute("SELECT version FROM meta") as cursor:
                db_version = await cursor.fetchone()
                if db_version is None:
                    await conn.execute("INSERT INTO meta VALUES (?)", (self.version,))
                    await conn.commit()
                    return
                elif db_version[0] != self.version:
                    async with conn.execute("SELECT alert_channel FROM settings") as cursor:
                        settings = await cursor.fetchall()
                        if settings is None:
                            return

                        for row in settings:
                            channel = await self.fetch_channel(row[0])
                            if channel is None or not isinstance(channel, TextChannel):
                                continue

                            # Ensure the bot has permission to send messages in the channel
                            if not channel.permissions_for(channel.guild.me).send_messages:
                                continue

                            await channel.send(embed=Embed(
                                title=f"The bot has been updated to version v{self.version} 🎉",
                                color=Color.dark_green(),
                            ))

                    await conn.execute("UPDATE meta SET version = ? WHERE version = ?", (self.version, db_version[0]))
                    await conn.commit()

    async def on_application_command_error(self, interaction: Interaction, exception: ApplicationError):
        await interaction.response.send_message(f"Error: {exception}", ephemeral=True)


client = Client()  # Create an instance of the client

if __name__ == "__main__":
    if environ.get("TOKEN") is None:
        raise ValueError("TOKEN environment variable is not set")

    client.run(environ.get("TOKEN"))
