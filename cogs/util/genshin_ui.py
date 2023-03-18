import json
import aiohttp
from io import BytesIO

import discord

from genshin.generater import generation


'''
ch_json : キャラ情報
n_json : jp名に変換
card_json : プレイヤー名刺
prop_json : propをjp名に変換
'''
with open("genshin/data/character.json", 'r', encoding='utf-8') as json_open:
    ch_json = json.load(json_open)

with open("genshin/data/names.json", 'r', encoding='utf-8') as json_open:
    n_json = json.load(json_open)

with open("genshin/data/namecards.json", 'r', encoding='utf-8') as json_open:
    card_json = json.load(json_open)

with open("genshin/data/prop.json", 'r', encoding='utf-8') as json_open:
    prop_json = json.load(json_open)


def data_json(uid : str):
    with open("data.json", 'r', encoding='utf-8') as json_open:
        data = json.load(json_open)
        p = data[uid]
    return p


elem_prop_id = {
    "Fire" : "40",
    "Electric" : "41",
    "Water" : "42",
    "Grass" : "43",
    "Wind" : "44",
    "Rock" : "45",
    "Ice" : "46",
}

elem_jp = {
    "Fire" : "炎元素",
    "Electric" : "雷元素",
    "Water" : "水元素",
    "Grass" : "草元素",
    "Wind" : "風元素",
    "Rock" : "岩元素",
    "Ice" : "氷元素",
}

elem_color = {
    "Fire" : 0xFF3902,
    "Electric" : 0x9F72FF,
    "Water" : 0x3A78FF,
    "Grass" : 0x8BFF59,
    "Wind" : 0x59FF7D,
    "Rock" : 0xFFD071,
    "Ice" : 0x50FFFF,
}

###############################
# View

class player_info_view(discord.ui.View):
    def __init__(self, uid : str, inter: discord.Interaction):
        super().__init__(timeout=120)
        self.inter = inter

        # キャラクター選択
        self.add_item(character_select(uid, inter))

        # Enka Network
        url = f"https://enka.network/u/{uid}/"
        self.add_item(discord.ui.Button(label="Enka Network", url=url))

        self.add_item(stop_button(inter))

    async def on_timeout(self) -> None:
        try:
            await self.inter.edit_original_response(view=None)
        except:
            pass
        return


class build_card_view(discord.ui.View):
    def __init__(self, uid, inter: discord.Interaction, c_data : dict):
        super().__init__(timeout=120)
        self.inter = inter

        self.add_item(character_select(uid, inter=inter))

        self.add_item(generate_img_select(uid, inter, c_data))

        # Enka Network
        url = f"https://enka.network/u/{uid}/"
        self.add_item(discord.ui.Button(label="Enka Network", url=url))

        self.add_item(stop_button(inter=inter))

    async def on_timeout(self) -> None:
        try:
            await self.inter.edit_original_response(view = None)
        except:
            pass
        return





##################################################
# 関数系

def create_img_url(name: str):
    return f"https://enka.network/ui/{name}.png"


###################################################
# UI

class uid_modal(discord.ui.Modal):
    def __init__(self, member_id : int,*args, **kwargs) -> None:

        with open("data.json", 'r', encoding='utf-8') as json_open:
            data = json.load(json_open)
        uid = data.get(str(member_id))

        super().__init__(
            discord.ui.InputText(label="UIDを入力してください/INPUT GENSHIN UID",
                                 min_length=9,
                                 max_length=9,
                                 style=discord.InputTextStyle.short,
                                 value=uid
                                 ),
            *args,
            **kwargs,
        )

    async def callback(self, ctx: discord.Interaction):
        uid = self.children[0].value

        try:
            int(self.children[0].value)
        except BaseException:
            return await ctx.response.send_message("UIDは数字でなければいけません", ephemeral=True)

        # UID書き込み
        with open("uid.json", 'r', encoding='utf-8') as json_open:
            data = json.load(json_open)

        data[str(ctx.user.id)] = uid

        with open("uid.json", "w", encoding = "utf-8") as json_write:
            json.dump(data, json_write, ensure_ascii = False, indent = 4)

        await ctx.response.send_message("プレイヤー情報を取得中...")

        api_url = f"https://enka.network/api/uid/{uid}/"

        resp = await self.api_request(api_url)
        self.resp = resp
        self.uid = uid

        if isinstance(resp, str):
            return await ctx.edit_original_response(content = resp)

        if "avatarInfoList" not in resp:
            await ctx.edit_original_response(content = "キャラ詳細情報が非表示です。\nもう一度表示になっているか確認してまたお試しください。")
            return
        # プロフィール
        embed = self.profile_embed()

        self.resp_json_write()

        await ctx.edit_original_response(content=None, embed=embed,
                                         view=player_info_view(uid, ctx)
                                         )


    # API request
    # もしエラーコードが返された場合
    # エラーメッセージが返される
    async def api_request(self, url) -> str | dict:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()

                elif response.status == 400:
                    return "Error : UIDが適切なものではありません。"
                elif response.status == 404:
                    return "Error : そのUIDのプレイヤーは存在しません。"
                elif response.status == 424:
                    return "Error : 原神がメンテナンス中かゲームで異常が起っています。"
                elif response.status == 429:
                    return "Error : レート制限にかかっています。\n__10分後に__またお試しください。"
                elif response.status == 500:
                    return "Error : サーバーエラーです。\n時間を空けてお試しください。"
                else:
                    return f"Error : {response.status}\nこれが時間をおいても何回も続く場合運営に提出してください。"


    # UIDごとにレスポンスデータ保存
    def resp_json_write(self):
        with open('data.json', 'r', encoding= 'utf-8') as json_open:
            data_json = json.load(json_open)

        data_json[f"{self.uid}"] = self.resp

        with open("data.json", "w", encoding = "utf-8") as json_write:
            json.dump(data_json, json_write, ensure_ascii = False, indent = 4)


    def profile_embed(self) -> discord.Embed:
        player_info = self.resp["playerInfo"]

        embed = discord.Embed(description=player_info["signature"],
                              color=discord.Colour.orange()
                              )
        embed.set_author(name=player_info["nickname"])
        embed.add_field(
            name="螺旋",
            value="{}層 {}間".format(
                player_info["towerFloorIndex"],
                player_info["towerLevelIndex"]))
        embed.add_field(name="アチーブメント",
                        value=player_info["finishAchievementNum"]
                        )

        level = player_info["level"]
        world_level = player_info["worldLevel"]
        embed.set_footer(text=f"冒険者ランク{level}・世界ランク{world_level}")

        card_id = player_info["nameCardId"]
        name_card = card_json[str(card_id)]["icon"]

        ch_id= player_info["profilePicture"]["avatarId"]
        ch_icon_name = ch_json[str(ch_id)]["iconName"]

        embed.set_thumbnail(url=create_img_url(ch_icon_name))
        embed.set_image(url=create_img_url(name_card))

        return embed



###################################################################
# キャラ選択
class character_select(discord.ui.Select):
    def __init__(self, uid, inter: discord.Interaction):
        self.uid = uid
        self.data = data_json(uid)
        self.inter = inter
        p_data = self.data["playerInfo"]
        self.c_data = self.data["avatarInfoList"]

        options = []
        for c in p_data["showAvatarInfoList"]:
            name = n_json[str(
                ch_json[str(c["avatarId"])]["nameTextMapHash"])]

            options.append(discord.SelectOption(
                label=name,
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
        await interaction.response.defer()
        if interaction.user != self.inter.user:
            return
        try:
            await self.inter.edit_original_response(content="読み込み中...", embed=None, view=None, attachments=[])
        except:
            await self.inter.edit_original_response(content="読み込み中...", embed=None, view=None)

        # キャラステータス
        embed, c_data= await self.status_embed()

        await self.inter.edit_original_response(content = None, embed = embed,
                                                view=build_card_view(self.uid, self.inter, c_data)
        )



    async def status_embed(self):
        embed = discord.Embed()


        c_data = {}
        for c in self.c_data:
            if str(c["avatarId"]) == self.values[0]:
                c_data = c
                c_id = c["avatarId"]

        c_url = create_img_url(ch_json[
                               str(c_data["avatarId"])]["sideIconName"])
        c_name = n_json[str(ch_json[self.values[0]]["nameTextMapHash"])]

        embed.set_author(icon_url = c_url, name = c_name)

        # 簡易プロフィール
        p_data = self.data["playerInfo"]
        p_name = p_data["nickname"]
        p_level = p_data["level"]
        p_w_level = p_data["worldLevel"]

        embed.description = f"{p_name}・冒険ランク{p_level}・世界ランク{p_w_level}"


        # 武器
        weapon_number = 0
        for n, w in enumerate(c_data["equipList"]):
            if "weapon" in w:
                weapon_number = n

        weapon = c_data["equipList"][weapon_number]
        weapon_name = n_json[str(weapon["flat"]["nameTextMapHash"])]
        weapon_level = weapon["weapon"]["level"]
        weapon_rera = weapon["flat"]["rankLevel"]

        weapon_value_text = ""
        for w in weapon["flat"]["weaponStats"]:
            weapon_state_name = prop_json[str(w["appendPropId"])]
            weapon_state = w["statValue"]
            weapon_value_text += f"**{weapon_state_name}** : {weapon_state}\n"

        embed.add_field(name = f"lv.{weapon_level}{weapon_name}:R{weapon_rera}",
                        value=weapon_value_text, inline=False)


        # キャラステータス
        HP = round(c_data["fightPropMap"]["2000"])
        HP_text = f"**HP上限** : {HP}\n"

        attack = round(c_data["fightPropMap"]["2001"])
        attack_text = f"**攻撃力** : {attack}\n"

        deffence = round(c_data["fightPropMap"]["2002"])
        deffence_text = f"**防御力** : {deffence}\n"

        elemental_mastery = round(c_data["fightPropMap"]["28"])
        elemental_mastery_text = f"**元素熟知** : {elemental_mastery}\n"

        energy_recharge = round(c_data["fightPropMap"]["23"] * 100)
        energy_recharge_text = f"**元素チャージ効率** : {energy_recharge}%\n"

        crit_rate = round(c_data["fightPropMap"]["20"] * 100)
        crit_rate_text = f"**会心率** : {crit_rate}%\n"

        crit_dmg = round(c_data["fightPropMap"]["22"] * 100)
        crit_dmg_text = f"**会心ダメージ** : {crit_dmg}%\n"

        elem = ch_json[str(c_id)]["costElemType"]
        elem_dmg = round(c_data["fightPropMap"][str(elem_prop_id[elem])] * 1000) / 10
        elem_jp_name = elem_jp[elem]
        elem_dmg_text = f"**{elem_jp_name}ダメージ** : {elem_dmg}%"


        character_status_text = HP_text + attack_text + deffence_text + elemental_mastery_text + energy_recharge_text + crit_rate_text + crit_dmg_text + elem_dmg_text
        embed.add_field(name = "ステータス", value = character_status_text, inline = False)
        embed.color = elem_color[elem]


        # 命の星座
        talent = 0
        if "talentIdList" in c_data:
            try:
                talent = len(c_data["talentIdList"])
            except:
                pass

        embed.add_field(name = "命の星座", value = f"{talent}凸")


        # スキルレベル
        skill_level_map = c_data["skillLevelMap"]
        skill_levels = skill_level_map.values()

        skill_levels_str = []
        for s in skill_levels:
            skill_levels_str.append(str(s))

        embed.add_field(name = "天賦レベル", value = "・".join(skill_levels_str))


        # footer
        c_level = c_data["propMap"]["4001"]["val"]
        c_friend_level = c_data["fetterInfo"]["expLevel"]
        embed.set_footer(text = f"Lv{c_level}・好感度{c_friend_level}")

        return embed, c_data




########################################
### 換算方法選択
### したのち画像生成

class generate_img_select(discord.ui.Select):
    def __init__(self, uid, inter: discord.Interaction, c_data : dict):
        self.data = data_json(uid)
        self.c_data = c_data
        self.inter = inter
        self.uid = uid

        options = [
            discord.SelectOption(label="HP", description="HP 基準でスコアを計算し、画像を生成します。", value = "HP"),
            discord.SelectOption(label="攻撃", description="攻撃 基準でスコアを計算し、画像を生成します。", value= "ATTACK"),
            discord.SelectOption(label="防御", description="防御 基準でスコアを計算し、画像を生成します。", value= "DEFENCE"),
            discord.SelectOption(label="チャージ", description="チャージ 基準でスコアを計算し、画像を生成します。", value = "CHARGE"),
            discord.SelectOption(label="元素熟知(β版)", description="元素熟知 基準(アタッカーベース)でスコアを計算し、画像を生成します。", value = "ELEMENT")]

        super().__init__(
            placeholder="ビルドカードを生成",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if interaction.user != self.inter.user:
            return

        try:
            await self.inter.edit_original_response(content="生成中...", embed=None, view=None, attachments=[])
        except:
            await self.inter.edit_original_response(content="生成中...", embed=None, view=None)

        data = await self.create_artifacter_dict()

        if isinstance(data, str):
            await self.inter.edit_original_message(content = data)
            return

        score = data["Score"]["total"]
        if score >= 220:
            m = "SS"
        elif score >= 200:
            m = "S"
        elif score >= 180:
            m = "A"
        else:
            m = "B"


        embed = discord.Embed(title = f"キャラクターの評価 : {m}",
                              color = elem_color[ch_json[str(self.c_data["avatarId"])]["costElemType"]])

        p_data = self.data["playerInfo"]
        p_name = p_data["nickname"]
        p_level = p_data["level"]
        p_w_level = p_data["worldLevel"]
        embed.description = f"{p_name}・冒険ランク{p_level}・世界ランク{p_w_level}"

        level = self.c_data["propMap"]["4001"]["val"]
        friendly = self.c_data["fetterInfo"]["expLevel"]
        score_type = data["Score"]["State"]
        embed.set_footer(text = f"Lv.{level}・好感度{friendly}・score:{score}/{score_type}換算")


        img = generation(data)
        with BytesIO() as buffer:
            img.save(buffer, "png")
            buffer.seek(0)
            file = discord.File(buffer, "image.png")
            embed.set_image(url="attachment://image.png")

        await self.inter.edit_original_response(content = None, embed = embed, view = build_card_view(self.uid, self.inter, self.c_data), file = file)



    async def create_artifacter_dict(self):
        character_name = n_json[str(
                            ch_json[str(self.c_data["avatarId"])]["nameTextMapHash"]
        )]

        url = f"https://genshin-api.kuroneko6423.com/api/genshindata/?uid={self.uid}&scoretype={self.values[0]}&charaName={character_name}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return f"Error : {response.status}\nサーバーエラーです。一度時間をおいてみてください。\nこれが時間をおいても何回も続く場合運営に提出してください。"







######################
# viewを消す

class stop_button(discord.ui.Button):
    def __init__(self, inter: discord.Interaction):
        super().__init__(
            label="操作を終了する",
            emoji="✖",
            style=discord.ButtonStyle.red
        )
        self.inter = inter

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if interaction.user != self.inter.user:
            return
        await self.inter.edit_original_response(view=None)