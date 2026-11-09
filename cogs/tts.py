import asyncio
import hashlib
import io
import os
import re
import sys

import discord
from discord.ext import commands

import tempfile

class TTSCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        print(f"init -> {self.__class__}")

        self.bot = bot

        self.NUMBER_TO_HTVOICEMAP = {
            0: "mei_normal.htsvoice",
            1: "mei_happy.htsvoice",
            2: "mei_angry.htsvoice",
            3: "mei_bashful.htsvoice",
        }

        self.queue = asyncio.Queue()

        self.worker_task = None

        self.MAX_TEXT_LENGTH = 30

        if sys.platform == "win32":
            self.open_jtalk = r"C:\open_jtalk\bin\open_jtalk.exe"
            self.dictionary = r"C:\open_jtalk\bin\dic"
            self.voice_dir = r"C:\open_jtalk\bin"
        else:
            self.open_jtalk = os.path.expanduser(
                "~/bin/open-jtalk/bin/open_jtalk"
            )
            self.dictionary = os.path.expanduser(
                "~/bin/open-jtalk/dic"
            )
            self.voice_dir = os.path.expanduser(
                "~/bin/open-jtalk/bin"
            )

    async def cog_load(self):
        self.worker_task = asyncio.create_task(self.speech_worker())

    async def cog_unload(self):
        if self.worker_task:
            self.worker_task.cancel()

            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass

    @staticmethod
    def classify(text: str) -> int:
        hash_value = hashlib.sha256(
            text.encode("utf-8")
        ).digest()

        return int.from_bytes(hash_value[:8], "big") % 4

    def replace_mentions(self, message: discord.Message) -> str:
        text = message.content

        # カスタム絵文字
        text = re.sub(
            r"<a?:[a-zA-Z0-9_]+:\d+>",
            "絵文字",
            text
        )

        # ロールメンション
        text = re.sub(
            r"<@&\d+>",
            "ロール",
            text
        )

        # チャンネルメンション
        text = re.sub(
            r"<#\d+>",
            "チャンネル",
            text
        )

        # ユーザーメンション
        text = re.sub(
            r"<@!?\d+>",
            "ユーザー",
            text
        )

        # Unicode絵文字
        text = re.sub(
            r"(?:[\U0001F000-\U0001FAFF]"
            r"|[\u2600-\u27BF]"
            r"|\uFE0F|\u200D)+",
            "絵文字",
            text
        )

        # 改行・連続空白
        text = re.sub(r"\s+", " ", text)

        return text.strip()[:self.MAX_TEXT_LENGTH]

    async def generate_audio(
        self,
        text: str,
        author_id: int
    ) -> io.BytesIO | None:

        voice = self.NUMBER_TO_HTVOICEMAP[
            self.classify(str(author_id))
        ]

        cmd = [
            self.open_jtalk,
            "-x", self.dictionary,
            "-m", os.path.join(self.voice_dir, voice),
            "-ow", "/dev/stdout" if sys.platform != "win32" else "CON",
        ]

        
        with await asyncio.to_thread(tempfile.NamedTemporaryFile, suffix=".wav") as wav:
            cmd[cmd.index("-ow") + 1] = wav.name

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            try:
                _, stderr = await asyncio.wait_for(
                    process.communicate(
                        text.encode("utf-8")
                    ),
                    timeout=30
                )

                if process.returncode != 0:
                    print(
                        "Open JTalk error:",
                        stderr.decode("utf-8", errors="replace")
                    )
                    return None

                wav.seek(0)

                audio = io.BytesIO(wav.read())
                audio.seek(0)

                return audio

            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return None

    async def speech_worker(self):
        while True:
            guild, text, author_id = await self.queue.get()

            try:
                if guild.voice_client is None:
                    continue

                audio = await self.generate_audio(
                    text,
                    author_id
                )

                if audio is None:
                    continue

                voice_client = guild.voice_client

                if not voice_client or not voice_client.is_connected():
                    continue

                while voice_client.is_playing():
                    await asyncio.sleep(0.1)

                source = discord.FFmpegOpusAudio(
                    audio,
                    pipe=True
                )

                finished = asyncio.Event()

                def after(error):
                    if error:
                        print(f"TTS playback error: {error}")

                    self.bot.loop.call_soon_threadsafe(
                        finished.set
                    )

                voice_client.play(
                    source,
                    after=after
                )

                await finished.wait()

                audio.close()

            except asyncio.CancelledError:
                raise

            except Exception as e:
                print(f"TTS error: {e}")

            finally:
                self.queue.task_done()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):

        if message.author.bot or not message.guild:
            return

        if not message.guild.voice_client:
            return

        connect_cog = self.bot.get_cog("ConnectCog")

        if not connect_cog:
            return

        if message.channel.id not in connect_cog.text_channel:
            return

        text = self.replace_mentions(message)

        if not text:
            return

        await self.queue.put((
            message.guild,
            text,
            message.author.id
        ))


def setup(bot: commands.Bot):
    bot.add_cog(TTSCog(bot))