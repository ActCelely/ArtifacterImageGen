import discord
from discord.ext import commands
from cogs.util.genshin_ui import uid_modal


class genshin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @discord.slash_command(name="build", description="UIDからキャラクタービルドカードを生成できます。")
    async def build(self, ctx: discord.ApplicationContext):
        await ctx.response.send_modal(uid_modal(member_id = ctx.author.id, title = "UID入力"))


def setup(bot: commands.Bot):
    bot.add_cog(genshin(bot))
