"""将上游动作契约与本角色的分层动画设计逐项对应；未设计的动作一律报错。"""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
UPSTREAM = ROOT.parents[1] / "dsh-pet" / "assets" / "config.jsonc"


def read_upstream():
    source = UPSTREAM.read_text(encoding="utf-8")
    pattern = r'"(?:\\.|[^"\\])*"|//[^\n]*|/\*[\s\S]*?\*/'
    clean = re.sub(pattern, lambda m: m[0] if m[0].startswith('"') else "", source)
    return json.loads(re.sub(r",(\s*[}\]])", r"\1", clean))


# pose 决定肢体动作，prop 决定道具演出；每个上游名字都必须显式分配。
DESIGNS = {
    "待机呼吸休闲": ("idle", "none"), "东张西望": ("look", "none"),
    "被鼠标拖拽悬空反馈": ("drag", "none"),
    "点击回应-开心跃动": ("jump", "hearts"), "点击回应-害羞惊讶": ("shy", "blush"),
    "点击回应-傲娇生气": ("angry", "anger"), "点击回应-挠痒咯咯笑": ("laugh", "laugh"),
    "点击回应-元气挥手": ("wave", "hello"),
    "螃蟹走路": ("crab", "none"), "原地漂浮踏步": ("float", "bubbles"),
    "原地左转奔跑": ("run", "speed"),
    "悠闲哼歌": ("sway", "music"), "超大伸懒腰": ("stretch", "stretch"),
    "原地敲击桌面互动": ("tap", "desk"), "原地重力下蹲压缩": ("squat", "squat"),
    "哈欠连天": ("yawn", "yawn"), "原地小憩沉眠": ("sleep", "pillow"),
    "女仆屈膝礼仪": ("curtsy", "sparkles"), "被吓一跳": ("startle", "surprise"),
    "小幅度原地360度旋转展示": ("spin", "sparkles"),
    "偷吃零食被抓住": ("guilty", "cookie"), "用鲸鱼尾巴拍打地面": ("tail", "splash"),
    "打瞌睡被惊醒": ("wake", "alarm"), "照镜子": ("mirror", "mirror"),
    "整体换装试色": ("dress", "palette"), "轻快记录": ("write", "notebook"),
    "写代码": ("type", "laptop"), "摇扇纳凉": ("fan", "fan"), "晨间刷牙": ("brush", "toothbrush"),
    "原地专心玩魔方": ("cube", "cube"), "原地蹲下玩玩具汽车": ("toy", "car"),
    "鲸鱼吐泡泡特效": ("blow", "bubbles"), "原地跳跃抓碎头顶物品": ("reach", "breakstar"),
    "玩游戏气急败坏": ("game", "console"), "玩水枪": ("shoot", "watergun"),
    "小提琴演奏": ("violin", "violin"), "蓝鲸现世": ("summon", "whale"),
    "优雅女仆舞": ("ballet", "ribbon"), "轻快摇摆舞": ("dance", "music"),
    "可爱宅舞": ("idol", "hearts"), "吹气球": ("blow", "balloon"),
    "动物环绕": ("pet", "animals"), "放风筝": ("kite", "kite"),
    "拆礼物": ("gift", "gift"), "变鸽子": ("magic", "dove"),
    "扑克魔术": ("magic", "cards"), "抽陀螺": ("whip", "top"),
    "吹笛子": ("flute", "flute"), "蝴蝶蜜蜂环绕头顶开花": ("garden", "butterflies"),
    "撸猫": ("pet", "cat"), "凭空生花": ("magic", "flower"),
    "骑木马": ("ride", "rockinghorse"), "三球抛接": ("juggle", "balls"),
    "踢毽子": ("kick", "shuttlecock"), "下五子棋": ("board", "gomoku"),
    "荡秋千": ("swing", "swing"),
    "吃白饭": ("eat", "rice"), "大口吃零食": ("eat", "snacks"),
    "吃Token": ("eat", "tokens"), "吃早餐": ("eat", "breakfast"),
    "吃午餐": ("eat", "bento"), "吃晚餐": ("eat", "dinner"),
    "吃冰淇淋融化": ("lick", "icecream"), "吃大闸蟹": ("eat", "crabfood"),
    "吃糖葫芦": ("lick", "tanghulu"), "吃长寿面": ("noodles", "noodles"),
    "吃西瓜": ("eat", "watermelon"), "涮火锅": ("hotpot", "hotpot"),
    "被落叶淹没": ("leaves", "leaves"), "中秋赏月吃月饼": ("eat", "mooncake"),
    "堆雪人": ("build", "snowman"), "放烟花": ("celebrate", "fireworks"),
    "吃粽子": ("eat", "zongzi"), "吃年糕": ("eat", "ricecake"),
    "吃青团": ("eat", "qingtuan"), "吃腊八粥": ("eat", "porridge"),
    "吃重阳糕": ("eat", "osmanthus"), "收红包": ("gift", "redpacket"),
    "写福字": ("write", "fu"), "穿针乞巧": ("thread", "needle"),
    "舞狮头": ("lion", "lion"), "讨糖南瓜灯": ("gift", "pumpkin"),
    "插茱萸赏菊": ("garden", "chrysanthemum"), "放河灯": ("lantern", "lotus"),
    "萌化小幽灵": ("ghost", "ghost"), "装点圣诞树": ("tree", "christmastree"),
    "放孔明灯": ("lantern", "skylantern"), "吃汤圆": ("eat", "tangyuan"),
    "吃饺子": ("eat", "dumplings"),
    "是啊，吃什么": ("shrug", "foodquestion"), "深度思考碎碎念": ("think", "thought"),
    "余额-钱袋满溢": ("money", "money0"), "余额-金袋叮当": ("money", "money1"),
    "余额-钱袋如常": ("money", "money2"), "余额-数金皱眉": ("count", "money3"),
    "余额-袋空如洗": ("sad", "money4"), "余额-分文不剩": ("sad", "money5"),
    "碎碎念-擦桌碎碎念": ("wipe", "wipedesk"), "碎碎念-发呆碎碎念": ("look", "chat"),
    "碎碎念-对屏碎碎念": ("type", "screenchat"),
    "工作状态-思考冒泡": ("think", "thought"), "工作状态-忙碌点按": ("type", "terminal"),
    "工作状态-清点归档": ("file", "folder"), "工作状态-原地踱步张望": ("wait", "clock"),
    "工作状态-雀跃庆祝": ("celebrate", "confetti"), "工作状态-垂头叹气冒汗": ("sad", "sweat"),
}


def catalogue():
    config = read_upstream()
    a = config["animations"]
    rows = []
    for slot in ("idle", "turn", "drag", "clicks"):
        rows.extend({"name": name, "group": slot} for name in a[slot])
    rows.extend({"name": item["name"], "group": "moves"} for item in a["moves"]["actions"])
    for category in a["categories"]:
        rows.extend({"name": name, "group": category["id"]} for name in category["actions"])
    for event, slots in a["events"].items():
        for index, name in enumerate(slots):
            if not isinstance(name, str):
                raise ValueError("需要先为上游多候选事件显式补充设计")
            rows.append({"name": name, "group": event, "slot": index})
    assert {r["name"] for r in rows} == set(DESIGNS), "上游动作清单发生变化，需显式更新设计映射"
    for row in rows:
        row["pose"], row["prop"] = DESIGNS[row["name"]]
        row["duration"] = 5 if row["group"] == "moves" else 3
        row["technique"] = "layered-puppet"
    return config, rows


def write_catalogue():
    _, rows = catalogue()
    result = {"upstreamSha256": hashlib.sha256(UPSTREAM.read_bytes()).hexdigest(), "count": len(rows), "actions": rows}
    (ROOT / "sources" / "action-catalogue.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return rows


if __name__ == "__main__":
    rows = write_catalogue()
    from collections import Counter
    print(len(rows), dict(Counter(row["group"] for row in rows)))
