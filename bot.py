import os

import discord
from discord.ext import commands
import dotenv

dotenv.load_dotenv()

intents = discord.Intents.none()
intents.guilds = True
intents.guild_messages = True
intents.message_content = True
intents.voice_states = True

class SharkTTS(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="st!", intents=intents, help_command=None)

    async def on_connect(self):
        self.load_extension("cogs.admin")
        self.load_extension("cogs.connect")
        self.load_extension("cogs.tts")

        return await super().on_connect()

bot = SharkTTS()

if __name__ == "__main__":
    bot.run(os.environ.get('DISCORD_TOKEN'))