import os
import random
import sqlite3
from datetime import datetime, timedelta, timezone
from pkg.plugin.context import *
from pkg.plugin.events import *
from pkg.platform.types import *
import asyncio
import json
# img
from PIL import Image as Image_
from PIL import ImageDraw, ImageFont
import logging

# 创建UTC+8时区对象
china_tz = timezone(timedelta(hours=8))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "luck_records_advanced.db")

# ==== 一些可自定义的随机素材 ====
FORTUNE_TEXTS = ["大吉", "小吉", "吉", "末吉", "凶", "大凶"]
COLORS = [
    "红色",
    "蓝色",
    "绿色",
    "紫色",
    "白色",
    "黑色",
    "灰色",
    "粉色",
    "金色",
    "黄色",
    "橙色",
    "青色",
    "银色",
    "棕色",
    "透明色",
    "彩虹色",
    "铁锈色",
    "铜绿色",
    "靛蓝色",
    "翠绿色",
    "橄榄色",
    "茶色",
    "杏色",
    "铅灰色",
    "赤色",
    "雨色",
    "雪色",
    "霞色",
    "霜色",
    "霁色",
    "霰色",
    "霓色",
    "霪色",
    "霭色",
    "露色",
    "霹雳色",
    "霾色",
    "靥色",
    "青莲色",
    "青缥色",
    "青白色",
    "五彩斑斓的黑色",
    "五彩斑斓的白色",
    "五彩斑斓的透明色",
]
ADVICE_DO = [
    "出门逛街",
    "加班学习",
    "打扫卫生",
    "看书充电",
    "给喜欢的人表白",
    "搞副业",
    "出门逛街时顺便去游戏厅打太鼓达人",
    "加班学习后用太鼓达人来放松一下",
    "打扫卫生完毕后再来一曲太鼓达人减压",
    "看书充电之余练习太鼓达人提高节奏感",
    "给喜欢的人表白前一起玩太鼓达人增进感情",
    "搞副业的间隙打打太鼓达人激发灵感",
    "考段",
    "越级",
]
ADVICE_DONT = [
    "熬夜",
    "和人吵架",
    "冲动消费",
    "吃太多甜食",
    "迟到",
    "赖床",
    "深夜不戴耳机在家猛敲太鼓达人扰民",
    "为冲高分通宵达旦地敲太鼓达人损害身体",
    "在公共场所外放音量狂热打太鼓达人",
    "为攒金币砸钱抽太鼓达人周边买到吃土",
    "沉迷太鼓达人导致工作或学习荒废",
    "刚练手就直接开高难度谱面伤鼓又伤心",
    "考段",
    "越级",
    "熬夜打太鼓达人",
]


def init_db():
    """
    初始化数据库，如果 luck_records 和 luck_steals 表不存在，则创建。
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # 主表：存储每日运势
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS luck_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            date TEXT NOT NULL,        -- YYYY-MM-DD
            luck_value INTEGER NOT NULL,
            fortune_text TEXT NOT NULL,  -- 吉凶签
            color TEXT NOT NULL,         -- 幸运色
            advice_do TEXT NOT NULL,     -- 今日宜
            advice_dont TEXT NOT NULL    -- 今日忌
        )
    """
    )
    # 记录偷取运势事件，防止一天多次偷
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS luck_steals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stealer_id TEXT NOT NULL,   -- 偷运势的人
            target_id TEXT NOT NULL,    -- 被偷的人
            date TEXT NOT NULL          -- YYYY-MM-DD
        )
    """
    )
    conn.commit()
    conn.close()


def get_today_record(user_id: str):
    """
    获取用户今日的运势记录 (如果有)，返回一行(dict形式或tuple)。
    如果没有记录，返回 None。
    """
    today_str = datetime.now(china_tz).strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        SELECT id, luck_value, fortune_text, color, advice_do, advice_dont 
        FROM luck_records
        WHERE user_id = ? AND date = ?
    """,
        (user_id, today_str),
    )
    row = c.fetchone()
    conn.close()
    if row:
        # row: (id, luck_value, fortune, color, do, dont)
        return {
            "id": row[0],
            "luck_value": row[1],
            "fortune_text": row[2],
            "color": row[3],
            "advice_do": row[4],
            "advice_dont": row[5],
        }
    return None


def create_today_record(user_id: str):
    """
    为用户在当天创建一条新的运势记录，并返回生成的数据。
    """
    today_str = datetime.now(china_tz).strftime("%Y-%m-%d")
    luck_value = random.randint(0, 100)
    fortune_text = random.choice(FORTUNE_TEXTS)
    color = random.choice(COLORS)
    advice_do_str = random.choice(ADVICE_DO)
    advice_dont_str = random.choice(ADVICE_DONT)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO luck_records (user_id, date, luck_value, fortune_text, color, advice_do, advice_dont)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
        (
            user_id,
            today_str,
            luck_value,
            fortune_text,
            color,
            advice_do_str,
            advice_dont_str,
        ),
    )
    conn.commit()
    conn.close()

    return {
        "luck_value": luck_value,
        "fortune_text": fortune_text,
        "color": color,
        "advice_do": advice_do_str,
        "advice_dont": advice_dont_str,
    }


def get_all_luck_records(user_id: str):
    """
    获取该用户全部的运势记录，按日期降序。
    返回列表：[(date, luck_value, fortune_text, color, advice_do, advice_dont), ...]
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        SELECT date, luck_value, fortune_text, color, advice_do, advice_dont
        FROM luck_records
        WHERE user_id = ?
        ORDER BY date DESC
    """,
        (user_id,),
    )
    rows = c.fetchall()
    conn.close()
    return rows


def delete_today_luck(user_id: str) -> bool:
    """
    删除用户当天的运势记录。返回 True 表示删除成功，False 表示无记录。
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    today_str = datetime.now(china_tz).strftime("%Y-%m-%d")
    c.execute(
        """
        DELETE FROM luck_records
        WHERE user_id = ? AND date = ?
    """,
        (user_id, today_str),
    )
    rowcount = c.rowcount
    conn.commit()
    conn.close()
    return rowcount > 0


def delete_all_luck(user_id: str) -> int:
    """
    删除用户所有运势记录，返回删除的条数。
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        DELETE FROM luck_records
        WHERE user_id = ?
    """,
        (user_id,),
    )
    rowcount = c.rowcount
    conn.commit()
    conn.close()
    return rowcount


def get_today_rank():
    """
    获取今天所有人的运势，按 luck_value DESC 排序。
    返回列表 [ (user_id, luck_value, fortune_text, color, advice_do, advice_dont), ...]
    """
    today_str = datetime.now(china_tz).strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        SELECT user_id, luck_value, fortune_text, color, advice_do, advice_dont
        FROM luck_records
        WHERE date = ?
        ORDER BY luck_value DESC
    """,
        (today_str,),
    )
    rows = c.fetchall()
    conn.close()
    return rows


def has_stolen_today(stealer_id: str):
    """
    检查偷运势表中，stealer_id 今日是否已经偷过。
    """
    today_str = datetime.now(china_tz).strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        SELECT 1 FROM luck_steals
        WHERE stealer_id = ? AND date = ?
    """,
        (stealer_id, today_str),
    )
    row = c.fetchone()
    conn.close()
    return row is not None


def record_steal(stealer_id: str, target_id: str):
    """
    在 luck_steals 表中记录一条偷运势行为。
    """
    today_str = datetime.now(china_tz).strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO luck_steals (stealer_id, target_id, date)
        VALUES (?, ?, ?)
    """,
        (stealer_id, target_id, today_str),
    )
    conn.commit()
    conn.close()


def update_luck_value(user_id: str, date_str: str, new_value: int):
    """
    更新 luck_records 表中某条记录的运势值（仅限当日），注意需要保证不超过范围 [0, 100]。
    """
    if new_value < 0:
        new_value = 0
    if new_value > 100:
        new_value = 100
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        UPDATE luck_records
        SET luck_value = ?
        WHERE user_id = ? AND date = ?
    """,
        (new_value, user_id, date_str),
    )
    conn.commit()
    conn.close()


# 配置

def generate_luck_image_with_icons(user_id: str, luck_data: dict, save_path: str):
    print('init pic func')
    print(user_id)
    print(luck_data)
    print(save_path)
    medal_path = os.path.join(os.path.dirname(__file__), "img/medal.png")
    hong_guan_path = os.path.join(os.path.dirname(__file__), "img/hong_guan.png")
    jin_guan_path=os.path.join(os.path.dirname(__file__), "img/jin_guan.png")
    yin_guan_path=os.path.join(os.path.dirname(__file__), "img/yin_guan.png")
    font_path = os.path.join(os.path.dirname(__file__), "Kaiti.ttf") # 替代字体路径（实际使用中替换为楷体）
    
    # 创建画布
    width, height = 720, 540
    img = Image_.new("RGB", (width, height), (255, 250, 240))
    draw = ImageDraw.Draw(img)

    # 加载字体
    title_font = ImageFont.truetype(font_path, 48)
    mid_font = ImageFont.truetype(font_path, 28)
    small_font = ImageFont.truetype(font_path, 22)

    # 标题与用户信息
    draw.text((width//2 - 100, 20), "今日運勢", font=title_font, fill=(139, 69, 19))
    draw.text((20, 20), f"用户：{user_id}", font=small_font, fill=(90, 90, 90))

    # RP值与签文
    draw.text((50, 100), f"RP值：{luck_data['luck_value']}", font=mid_font, fill=(0, 0, 0))
    draw.text((300, 100), f"签文：{luck_data['fortune_text']}", font=mid_font, fill=(0, 0, 0))

    # 幸运色块
    draw.rectangle([50, 160, 150, 210], fill="gray")
    try:
        draw.rectangle([50, 160, 150, 210], fill=luck_data['color'])
    except:
        pass
    draw.text((160, 170), f"幸运色：{luck_data['color']}", font=mid_font, fill=(0, 0, 0))

    # 宜忌
    draw.text((50, 260), f"宜：{luck_data['advice_do']}", font=small_font, fill=(0, 100, 0))
    draw.text((50, 300), f"忌：{luck_data['advice_dont']}", font=small_font, fill=(139, 0, 0))

    # 贴段位图标（左上角）
    val_score = luck_data.get("val_score", "")
    val_map = {
        "白粋": 0, "铜粋": 1, "银粋": 2,
        "金雅": 3, "粉雅": 4, "紫雅": 5, "極": 6
    }
    if val_score in val_map:
        sheet = Image_.open(medal_path).convert("RGBA")
        icon_w, icon_h = 80, 80
        row = val_map[val_score]
        x0, y0 = 0, row * icon_h
        val_icon = sheet.crop((x0, y0, x0 + icon_w, y0 + icon_h))
        img.paste(val_icon, (20, 60), val_icon)

    # 贴王冠图标（右上角）
    if luck_data['luck_value'] >= 95:
        crown = Image_.open(hong_guan_path).convert("RGBA").resize((64, 64))
        img.paste(crown, (width - 84, 20), crown)
    else:
        crown = Image_.open(jin_guan_path).convert("RGBA").resize((64, 64))
        img.paste(crown, (width - 84, 20), crown)

    img.save(save_path)




@register(
    name="LuckGetProPlugin",
    description="测试运势的插件(进阶版)：带吉凶签、幸运色、宜忌、排行榜、偷取等功能。",
    version="0.5",
    author="Rio",
)
class LuckPluginAdvanced(BasePlugin):

    def __init__(self, host: APIHost):
        self.host = host

    async def initialize(self):
        init_db()

    @handler(PersonMessageReceived)
    @handler(GroupMessageReceived)
    async def on_message(self, ctx: EventContext):
        """
        监听聊天事件，根据用户输入的命令来进行处理
        """
        msg = str(ctx.event.message_chain).strip()
        if not msg:
            return  # 空消息则不处理

        user_id = str(ctx.event.sender_id)
        # 如果你需要群号的话可以获取:
        # group_id = str(ctx.event.launcher_id)  # 群聊时的群号

        parts = msg.split(maxsplit=1)
        cmd = parts[0].lstrip("/").lower()  # 去除命令中的 '/', 并转小写
        arg = parts[1].strip() if len(parts) > 1 else ""

        # --- 帮助命令 ---
        if cmd == "rp帮助":
            help_text = (
                "【rp命令帮助】\n"
                "/rp               查看/生成今天的运势\n"
                "/rp记录           查看你全部历史运势\n"
                # "/rp删除 today     删除今天运势\n"
                # "/rp删除 all       删除所有运势记录\n"
                "/rp排行榜         今日运势排行榜\n"
                "/rp偷 @某人       偷取对方运势(每日一次)\n"
                "更多说明可自行扩展~"
            )
            await ctx.reply(MessageChain([Plain(help_text)]))
            return

        # --- /rp: 当日运势 ---
        if cmd == "rp1":
            record = get_today_record(user_id)
            if record is None:
                # 当天未抽，随机生成
                data = create_today_record(user_id)
            else:
                # 已有记录，直接返回
                data = record
            val_score = "  "
            if data['luck_value']>99:
                val_score = "極"
            elif data['luck_value']>94:
                val_score = "紫雅"
            elif data['luck_value']>89:
                val_score = "粉雅"
            elif data['luck_value']>79:
                val_score = "金雅"
            elif data['luck_value']>69:
                val_score = "银粋"
            elif data['luck_value']>59:
                val_score = "铜粋"
            elif data['luck_value']>49:
                val_score = "白粋"
            else:
                val_score = "  "
            reply_msg = (
                f"【今日运势】\n"
                f"《{val_score}》\n"
                f"今日人品（RP）值：{data['luck_value']}\n"
                f"今日签：{data['fortune_text']}\n"
                f"幸运色：{data['color']}\n"
                f"宜：{data['advice_do']}；忌：{data['advice_dont']}"
            )
            # 获取当前时间
            # now = datetime.now()
            # # 格式化为指定格式
            # formatted_time = now.strftime("%Y_%m_%d")
            # png_path = os.path.join(os.path.dirname(__file__), f"/geners/{formatted_time}_{user_id}.png")
            # if not os.path.exists(png_path):
            #     generate_luck_image_with_icons(user_id, data, png_path)
            
            # await ctx.reply(MessageChain([Image(png_path)]))
            png_path_test =  os.path.join(os.path.dirname(__file__), "img", "hong_guan.jpg")
            # png_path_test = "./img/hong_guan.png"
            
            # print(png_path_test)
            # ctx.logger.info(png_path_test)
            # await ctx.reply(MessageChain([Plain(png_path_test)]))
            await ctx.reply(MessageChain([Image(path=png_path_test)]))
            
            return

        # --- /rp记录: 查看全部历史 ---
        if cmd == "rp1记录":
            all_records = get_all_luck_records(user_id)
            if not all_records:
                await ctx.reply(MessageChain([Plain("你还没有任何运势记录~")]))
                return

            report_lines = ["【你的运势记录（由近到远）】"]
            for row in all_records:
                date_str, val, fortune, color, do, dont = row
                # 如有需要，可只展示部分信息
                line = f"{date_str} => {val} ({fortune},{color} | 宜:{do}, 忌:{dont})"
                report_lines.append(line)
            await ctx.reply(MessageChain([Plain("\n".join(report_lines))]))
            return

        # # --- /rp删除: 删除记录 ---
        # if cmd == "rp删除":
        #     if arg == "today":
        #         success = delete_today_luck(user_id)
        #         if success:
        #             await ctx.reply(MessageChain([Plain("已删除你今天的运势记录")]))
        #         else:
        #             await ctx.reply(MessageChain([Plain("你今天还没有运势记录，无需删除")]))
        #         return
        #     elif arg == "all":
        #         count = delete_all_luck(user_id)
        #         await ctx.reply(MessageChain([Plain(f"已删除你全部 {count} 条运势记录")]))
        #         return
        #     else:
        #         tip = "用法：\n/rp删除 today  （删除今天的运势）\n/rp删除 all    （删除全部运势）"
        #         await ctx.reply(MessageChain([Plain(tip)]))
        #         return

        # --- /rp排行榜: 今日最高 ---
        if cmd == "rp1排行榜":
            # 也可以在这里判断是否是群聊才执行，比如:
            # if ctx.event.launcher_type != "GROUP":
            #     await ctx.reply(MessageChain([Plain("排行榜仅限群聊使用")]))
            #     return
            rows = get_today_rank()
            if not rows:
                await ctx.reply(MessageChain([Plain("今天还没有任何运势记录哦~")]))
                return

            lines = ["【今日运势排行榜】"]
            # 取前 5 名或者全部
            top_n = rows[:5]
            rank = 1
            for r in top_n:
                # (user_id, luck_value, fortune, color, do, dont)
                uid, val, fortune, color, do, dont = r
                lines.append(f"{rank}. 用户 {uid} => {val} ({fortune}, {color})")
                rank += 1
            await ctx.reply(MessageChain([Plain("\n".join(lines))]))
            return

        # --- /rp偷: 偷取他人运势 ---
        if cmd == "rp1偷":
            if not arg:
                await ctx.reply(MessageChain([Plain("用法：/rp偷 @某人")]))
                return

            # 简单示例：如果是群聊 @xxx，可能需要先解析@对象的 user_id
            # 不同框架里 At() 解析方式不同，这里示例用字符串匹配或先前取event.mention这种……
            # 如果你无法准确获取，那就简单让用户写 /rp偷 <数字ID> 也行。
            # 这里只演示：假设 arg 就是个纯数字 user_id，或者你自己有实现解析 @xxx => user_id 的功能。

            target_id = arg
            if target_id.startswith("@"):
                target_id = target_id[1:].strip()  # 去掉 @

            if target_id == user_id:
                await ctx.reply(MessageChain([Plain("你不能偷自己哦~")]))
                return

            # 看看自己今天有没有运势
            self_record = get_today_record(user_id)
            if not self_record:
                await ctx.reply(
                    MessageChain([Plain("你今天还没有运势，先用 /rp 抽取吧！")])
                )
                return

            # 看看对方今天有没有运势
            target_record = get_today_record(target_id)
            if not target_record:
                await ctx.reply(
                    MessageChain([Plain("对方今天还没抽运势，暂时偷不到任何东西~")])
                )
                return

            # 检查自己今天是否偷过
            if has_stolen_today(user_id):
                await ctx.reply(
                    MessageChain([Plain("你今天已经偷过别人了，每日只能偷一次~")])
                )
                return

            # 开始偷运势：比如随机 1~10
            steal_amount = random.randint(1, 10)
            if target_record["luck_value"] <= 0:
                await ctx.reply(
                    MessageChain([Plain("对方的运势已经见底，偷不到什么了…")])
                )
                return

            final_steal = min(steal_amount, target_record["luck_value"])
            # 更新对方运势
            new_target_val = target_record["luck_value"] - final_steal
            today_str = datetime.now(china_tz).strftime("%Y-%m-%d")
            update_luck_value(target_id, today_str, new_target_val)

            # 更新自己运势
            new_self_val = self_record["luck_value"] + final_steal
            update_luck_value(user_id, today_str, new_self_val)

            # 记录偷取
            record_steal(user_id, target_id)

            msg_steal = (
                f"你成功从 {target_id} 身上偷取了 {final_steal} 点运势！\n"
                f"你的运势：{self_record['luck_value']} => {new_self_val}\n"
                f"对方运势：{target_record['luck_value']} => {new_target_val}"
            )
            await ctx.reply(MessageChain([Plain(msg_steal)]))
            return

    def __del__(self):
        pass
