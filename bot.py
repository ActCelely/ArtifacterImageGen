import discord
from discord.ext import commands
from Generater import test
from io import BytesIO
import json
import aiohttp

import os
from dotenv import load_dotenv
load_dotenv()
TOKEN = os.getenv("token")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents = intents, help_command= None)


with open("data/character.json", 'r', encoding= 'utf-8') as json_open:
    c_json = json.load(json_open)

with open("data/names.json", 'r', encoding= 'utf-8') as json_open:
    n_json = json.load(json_open)

with open("data/namecards.json", 'r', encoding= 'utf-8') as json_open:
    card_json = json.load(json_open)



def create_img_url(name : str):
    return f"https://enka.network/ui/{name}.png"


class get_data():
    def character_names(p_data : dict):

        character_info = p_data["showAvatarInfoList"]

        for c in character_info:
            character_name = n_json[str(c_json[str(c["avatarId"])]["nameTextMapHash"])]

            c["avatarId"] = character_name

        return character_info



class uid_modal(discord.ui.Modal):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(
            discord.ui.InputText(label="UIDを入力してください/INPUT GENSHIN UID",
                                 min_length=9,
                                 max_length=9,
                                 style=discord.InputTextStyle.short
            ),
            *args,
            **kwargs,
        )


    async def callback(self, ctx: discord.Interaction):
        try:
            int(self.children[0].value)
        except:
            return await ctx.response.send_message("UIDは数字でなければいけません", ephemeral=True)

        await ctx.response.send_message("プレイヤー情報を取得中...")

        api_url = f"https://enka.network/api/uid/{self.children[0].value}/"

        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as response:
                if response.status == 200:
                    resp = await response.json()

                elif response.status == 400:
                    return await ctx.edit_original_response("Error : UIDが適切なものではありません。")
                elif response.status == 404:
                    return await ctx.edit_original_response("Error : そのUIDのプレイヤーは存在しません。")
                elif response.status == 424:
                    return await ctx.edit_original_response("Error : 原神がメンテナンス中かゲームで異常が起っています。")
                elif response.status == 429:
                    return await ctx.edit_original_response("Error : レート制限にかかっています。\n__10分後に__またお試しください。")
                elif response.status == 500:
                    return await ctx.edit_original_response("Error : サーバーエラーです。\n時間を空けてお試しください。")
                else:
                    return await ctx.edit_original_response(f"Error : {response.status}\nこれが時間をおいても何回も続く場合運営に提出してください。")


        # プロフィール
        player_info = resp["playerInfo"]

        embed = discord.Embed(description= player_info["signature"], color= discord.Colour.orange())
        embed.set_author(name = player_info["nickname"])
        embed.add_field(name = "螺旋",
                        value= str(player_info["towerFloorIndex"]) + "層 " + str(player_info["towerLevelIndex"]) + "間"
        )
        embed.add_field(name = "アチーブメント",
                        value = player_info["finishAchievementNum"]
        )
        level = player_info["level"]
        world_level = player_info["worldLevel"]
        embed.set_footer(text = f"冒険者ランク{level}・世界ランク{world_level}")

        card_id = player_info["nameCardId"]
        name_card = card_json[str(card_id)]["icon"]

        ch_name = player_info["profilePicture"]["avatarId"]
        character = c_json[str(ch_name)]["iconName"]

        embed.set_thumbnail(url = create_img_url(character))
        embed.set_image(url = create_img_url(name_card))


        await ctx.edit_original_response(content = None, embed=embed, view=player_info_view(data = resp, inter = ctx))#


# キャラ選択
class character_select(discord.ui.Select):
    def __init__(self, data : dict, inter : discord.Interaction):
        self.data = data
        self.inter = inter
        p_data = data["playerInfo"]
        names = get_data.character_names(p_data)
        options = []

        for c in names:
            options.append(discord.SelectOption(
                label=c["avatarId"],
                description="Lv" + str(c["level"]),
                value=str(c["avatarId"])
            ))

        super().__init__(
                placeholder="キャラクターを選択",
                min_values=1,
                max_values=1,
                options=options,
            )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(None)
        await self.inter.edit_original_message()



class player_info_view(discord.ui.View):
    def __init__(self, data : dict, inter : discord.Interaction):
        super().__init__()
        self.add_item(character_select(data=data, inter = inter))











@bot.event
async def on_ready():
    print("Ready")

@bot.slash_command(name = "build", description = "UIDからキャラクタービルドカードを生成できます。")
async def build(ctx: discord.ApplicationContext):
    await ctx.response.send_modal(uid_modal(title = "UID入力"))

    '''
    img = test()
    with BytesIO() as buffer:
        img.save(buffer, "png")
        buffer.seek(0)
        file = discord.File(buffer, "image.png")
        await ctx.send(file = file)
    '''


bot.run(token = TOKEN)