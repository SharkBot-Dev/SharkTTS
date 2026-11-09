import discord
from discord.ext import commands

from tools import make_embed

class ConnectCog(discord.Cog):
    def __init__(self, bot: commands.bot):
        print(f"init -> {self.__class__}")
        self.bot = bot
        self.text_channel = []

    @commands.slash_command(name="join", description="読み上げを開始します。")
    async def join_command(self, ctx: discord.ApplicationContext):
        if not ctx.author.voice:
            await ctx.send(embed=make_embed.error_embed(title="接続に失敗しました。", description="あなたがVCに接続している必要があります。"))
            return

        if not ctx.author.voice.channel:
            await ctx.send(embed=make_embed.error_embed(title="接続に失敗しました。", description="あなたがVCに接続している必要があります。"))
            return

        if ctx.voice_client:
            await ctx.send(embed=make_embed.error_embed(title="接続に失敗しました。", description="すでにVCに接続されています。"))
            return

        await ctx.defer()

        await ctx.author.voice.channel.connect()

        try:
            try:
                self.text_channel.remove(ctx.channel_id)
                self.text_channel.remove(ctx.author.voice.channel.id)
            except:
                pass
            self.text_channel.append(ctx.channel_id)
            self.text_channel.append(ctx.author.voice.channel.id)
        except:
            pass

        await ctx.edit(embed=make_embed.success_embed(title="接続しました。", description="読み上げを開始します。"))

    @commands.slash_command(name="leave", description="読み上げを終了します。")
    async def leave_command(self, ctx: discord.ApplicationContext):
        if not ctx.author.voice:
            await ctx.send(embed=make_embed.error_embed(title="終了に失敗しました。", description="あなたがVCに接続している必要があります。"))

        if not ctx.author.voice.channel:
            await ctx.send(embed=make_embed.error_embed(title="終了に失敗しました。", description="あなたがVCに接続している必要があります。"))
            return

        if not ctx.voice_client:
            await ctx.send(embed=make_embed.error_embed(title="終了に失敗しました。", description="まだ読み上げを開始していません。"))
            return

        if ctx.voice_client.channel.id != ctx.author.voice.channel.id:
            await ctx.send(embed=make_embed.error_embed(title="終了に失敗しました。", description="あなたの接続しているVCでは\nまだ読み上げを開始していません。"))
            return

        await ctx.defer()

        await ctx.voice_client.disconnect()

        try:
            self.text_channel.remove(ctx.channel_id)
            self.text_channel.remove(ctx.author.voice.channel.id)
        except:
            pass

        await ctx.edit(embed=make_embed.success_embed(title="退出しました。", description="読み上げを終了しました。"))

def setup(bot: commands.bot):
    bot.add_cog(ConnectCog(bot))