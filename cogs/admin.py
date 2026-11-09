import discord
from discord.ext import commands

class AdminCog(discord.Cog):
    def __init__(self, bot: commands.bot):
        print(f"init -> {self.__class__}")
        self.bot = bot

    @commands.command(name="reload")
    @commands.is_owner()
    async def reload_command(self, ctx: commands.Context, cog_name: str):
        self.bot.reload_extension(f"cogs.{cog_name}")
        await ctx.channel.send(f"{cog_name}をリロードしました。")

    @commands.command(name="load")
    @commands.is_owner()
    async def load_command(self, ctx: commands.Context, cog_name: str):
        self.bot.load_extension(f"cogs.{cog_name}")
        await ctx.channel.send(f"{cog_name}をロードしました。")

def setup(bot: commands.bot):
    bot.add_cog(AdminCog(bot))