"""分层动作的代码原生道具与特效；每种道具都有独立演出，不绘制角色本体。"""
import math
from pathlib import Path
from PIL import ImageDraw, ImageFont

INK = "#33415f"
BLUE = "#73b8ec"
CREAM = "#fff5df"
ORANGE = "#e9a356"
PINK = "#e99cb6"
TAU = math.tau
_FONTS = {}


def font(size):
    if size not in _FONTS:
        choices = [Path("C:/Windows/Fonts/msyh.ttc"), Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")]
        path = next((p for p in choices if p.exists()), None)
        _FONTS[size] = ImageFont.truetype(str(path), size) if path else ImageFont.load_default(size=size)
    return _FONTS[size]


def star(d, x, y, r, fill=ORANGE, points=5):
    coords = []
    for i in range(points * 2):
        angle = i * math.pi / points - math.pi / 2
        radius = r if i % 2 == 0 else r * .42
        coords.append((x + math.cos(angle) * radius, y + math.sin(angle) * radius))
    d.polygon(coords, fill=fill, outline=INK, width=1)


def flower(d, x, y, r=10, fill=PINK):
    for i in range(5):
        a = i * TAU / 5
        cx, cy = x + math.cos(a) * r * .6, y + math.sin(a) * r * .6
        d.ellipse((cx-r*.5, cy-r*.5, cx+r*.5, cy+r*.5), fill=fill, outline=INK, width=1)
    d.ellipse((x-r*.3, y-r*.3, x+r*.3, y+r*.3), fill="#ffe69a", outline=INK)


def heart(d, x, y, r=10, fill=PINK):
    d.ellipse((x-r, y-r*.7, x, y+r*.2), fill=fill)
    d.ellipse((x, y-r*.7, x+r, y+r*.2), fill=fill)
    d.polygon([(x-r,y), (x+r,y), (x,y+r)], fill=fill)


def cat(d, x, y, scale=1, t=0, fill="#a6b6ce"):
    r = 17 * scale
    d.ellipse((x-r, y-r*.2, x+r, y+r*1.25), fill=fill, outline=INK, width=2)
    d.polygon([(x-r*.8,y-r*.6),(x-r*.7,y-r*1.4),(x-r*.1,y-r*.8)], fill=fill, outline=INK)
    d.polygon([(x+r*.8,y-r*.6),(x+r*.7,y-r*1.4),(x+r*.1,y-r*.8)], fill=fill, outline=INK)
    d.ellipse((x-r,y-r, x+r,y+r*.4), fill=fill, outline=INK, width=2)
    for sign in (-1,1):
        d.arc((x+sign*r*.38-3,y-r*.5,x+sign*r*.38+3,y-r*.15), 0,180,fill=INK,width=2)
    d.arc((x-4,y-r*.3,x+4,y+r*.1),0,180,fill=INK,width=1)
    dx = math.sin(t*TAU)*6
    d.arc((x+r*.6,y-r*.1,x+r*2+dx,y+r),210,380,fill=fill,width=max(2,int(7*scale)))


def whale(d, x, y, scale=1, t=0):
    w, h = 75*scale, 35*scale
    d.ellipse((x-w,y-h,x+w,y+h), fill="#5f91db", outline=INK,width=2)
    d.ellipse((x-w*.6,y,x+w*.75,y+h*.8),fill="#b8e0f3")
    d.polygon([(x+w*.85,y),(x+w*1.5,y-h*.8),(x+w*1.3,y),(x+w*1.5,y+h*.7)],fill="#5f91db",outline=INK)
    d.ellipse((x-w*.55,y-h*.3,x-w*.45,y-h*.1),fill=INK)
    d.arc((x-w*.55,y,x-w*.2,y+h*.4),0,170,fill=INK,width=2)


def bubble(d, x, y, text, size=15):
    box = d.textbbox((0,0),text,font=font(size))
    w = box[2]-box[0]+22
    d.rounded_rectangle((x-w/2,y-18,x+w/2,y+16),radius=12,fill=CREAM,outline=INK,width=2)
    d.polygon([(x-8,y+15),(x-3,y+25),(x+6,y+15)],fill=CREAM,outline=INK)
    d.text((x,y-2),text,fill=INK,font=font(size),anchor="mm")


FOODS = {"rice","snacks","tokens","breakfast","bento","dinner","icecream","crabfood","tanghulu",
         "noodles","watermelon","hotpot","mooncake","zongzi","ricecake","qingtuan","porridge",
         "osmanthus","tangyuan","dumplings","cookie"}
BEHIND = {"music","hearts","bubbles","speed","whale","animals","kite","butterflies","leaves",
          "fireworks","christmastree","swing","confetti","ghost","splash"}


def food(d, kind, t):
    x, y = 320, 247
    chew = math.sin(t*TAU*2)
    if kind in {"rice","noodles","porridge","tangyuan","dumplings","hotpot"}:
        color = "#6d7585" if kind == "hotpot" else "#fcfbf0"
        d.pieslice((x-44,y-15,x+44,y+45),0,180,fill=color,outline=INK,width=2)
        d.ellipse((x-44,y-15,x+44,y+11),fill="#f1dfb3" if kind=="porridge" else "#f9f4e5",outline=INK,width=2)
        if kind == "rice":
            d.ellipse((x-35,y-27,x+35,y+2),fill="#fffefa",outline=INK,width=2)
            for i in range(12):
                px=x-27+(i*17)%56; py=y-19+(i*11)%16
                d.arc((px,py,px+6,py+3),0,160,fill="#c8c4bb",width=1)
        elif kind == "noodles":
            for i in range(7):
                px=x-25+i*8
                d.arc((px,y-9,px+13,y+4),180,360,fill=ORANGE,width=2)
                if i<3:
                    d.line([(px,y-9),(px+3,y-40-8*chew)],fill=ORANGE,width=2)
        elif kind == "hotpot":
            d.ellipse((x-36,y-10,x+36,y+5),fill="#d77e58")
            for i in range(7):
                d.ellipse((x-30+i*9,y-7+(i%2)*5,x-24+i*9,y-1+(i%2)*5),fill="#91b98c")
            for side in (-1,1):
                d.arc((x+side*44-10,y-3,x+side*44+10,y+15),-90,90,fill=INK,width=4)
            d.arc((x-20,y+25,x+20,y+55),190,350,fill=ORANGE,width=4)
        elif kind in {"tangyuan","dumplings"}:
            for i in range(5):
                px=x-28+i*13
                d.ellipse((px,y-10+(i%2)*5,px+15,y+1+(i%2)*5),fill="#fffdf5",outline="#b4b1aa",width=1)
                if kind == "dumplings":
                    d.line((px+2,y-7+(i%2)*5,px+12,y-5+(i%2)*5),fill="#b4b1aa",width=1)
        else:
            for i in range(10):
                px=x-30+i*6; py=y-9+(i*13)%13
                d.ellipse((px,py,px+4,py+3),fill="#945e5a" if i%2 else "#d8b579")
        spoon_y = y-25-21*max(0,chew)
        d.line((x+20,y-10,x+43,spoon_y-8),fill=ORANGE,width=3)
        d.ellipse((x+29,spoon_y-16,x+45,spoon_y-7),fill="#f8f6ef",outline=INK,width=1)
        for i in range(3):
            px=x-25+i*24; py=y-52-(t*25+i*12)%25
            d.arc((px,py,px+9,py+18),100,260,fill="#b1bec8",width=2)
    elif kind == "watermelon":
        d.pieslice((x-46,y-52,x+46,y+32),0,180,fill="#73a86e",outline=INK,width=2)
        d.pieslice((x-39,y-45,x+39,y+23),0,180,fill="#f1979f",outline=INK,width=2)
        for i in range(5):
            d.ellipse((x-25+i*12,y+2-(i%2)*6,x-22+i*12,y+7-(i%2)*6),fill=INK)
    elif kind == "icecream":
        d.polygon([(x-19,y-3),(x+19,y-3),(x,y+43)],fill="#e5b777",outline=INK,width=2)
        for dy in (7,17,27): d.line((x-14+dy*.25,y+dy,x+14-dy*.25,y+dy),fill="#bc895d",width=1)
        d.ellipse((x-25,y-43,x+25,y+3),fill=PINK,outline=INK,width=2)
        drip=(t*28)%29
        d.rounded_rectangle((x+11,y-2,x+18,y+drip),radius=3,fill=PINK)
    elif kind == "tanghulu":
        d.line((x,y+40,x,y-45),fill="#b7875e",width=3)
        for i in range(4):
            d.ellipse((x-12,y-42+i*20,x+12,y-18+i*20),fill="#d66a64",outline=INK,width=2)
            d.ellipse((x-7,y-38+i*20,x-3,y-31+i*20),fill="#ffdfb7")
    elif kind == "zongzi":
        d.polygon([(x,y-45),(x-40,y+22),(x+39,y+22)],fill="#74a681",outline=INK,width=2)
        d.line([(x,y-39),(x-4,y+19),(x+34,y+17)],fill="#c9d5a2",width=3)
        d.line((x-26,y+1,x+21,y-10),fill="#e7c99a",width=3)
    elif kind == "tokens":
        for i in range(5):
            px=x-35+i*17; py=y-18+(i%2)*13
            d.ellipse((px-12,py-12,px+12,py+12),fill="#edbc66",outline=INK,width=2)
            d.text((px,py),"T",font=font(13),fill=INK,anchor="mm")
        d.ellipse((x+25,y-46-10*chew,x+48,y-23-10*chew),fill="#edbc66",outline=INK,width=2)
    elif kind == "crabfood":
        d.ellipse((x-28,y-17,x+28,y+17),fill="#e69769",outline=INK,width=2)
        for side in (-1,1):
            for i in range(3):
                d.line([(x+side*23,y-6+i*9),(x+side*44,y-17+i*17)],fill="#d77b55",width=4)
            d.ellipse((x+side*36-10,y-35,x+side*36+10,y-12),fill="#e69769",outline=INK,width=2)
            d.ellipse((x+side*12-3,y-22,x+side*12+3,y-14),fill=INK)
    elif kind in {"mooncake","cookie","snacks","ricecake","osmanthus","qingtuan"}:
        if kind=="mooncake":
            d.ellipse((405,45,465,105),fill="#f6d98e",outline="#d2ad6b",width=2)
        colors={"mooncake":"#d9a360","cookie":"#d7aa73","snacks":"#deb98a","ricecake":"#fff1df","osmanthus":"#e9c985","qingtuan":"#83ad72"}
        for i in range(3):
            px=x-37+i*27; py=y-13+(i%2)*7
            if kind in {"ricecake","osmanthus"}: d.rounded_rectangle((px-12,py-13,px+15,py+14),radius=4,fill=colors[kind],outline=INK,width=2)
            else: d.ellipse((px-16,py-16,px+16,py+16),fill=colors[kind],outline=INK,width=2)
            for j in range(4):
                star(d,px-8+j*5,py-5+(j%2)*8,2,"#ab7b4c")
        if kind=="mooncake": d.text((x,y-10),"月",font=font(14),fill="#916635",anchor="mm")
    else:
        d.rounded_rectangle((x-47,y-20,x+47,y+25),radius=8,fill="#bb8d6c",outline=INK,width=2)
        d.rounded_rectangle((x-42,y-15,x+42,y+20),radius=4,fill="#f4dfb4",outline=INK)
        if kind=="breakfast":
            d.rounded_rectangle((x-32,y-12,x-1,y+16),radius=5,fill="#dcae72",outline=INK,width=1)
            d.ellipse((x+2,y-10,x+32,y+16),fill="#fffdf5",outline=INK,width=1)
            d.ellipse((x+11,y-5,x+24,y+8),fill="#e9bd63")
        elif kind=="bento":
            d.line((x,y-15,x,y+20),fill=INK,width=2)
            d.rounded_rectangle((x-37,y-11,x-5,y+16),radius=3,fill="#fffdf5")
            for i in range(3): d.ellipse((x+7+i*8,y-5,x+18+i*8,y+9),fill="#81ad7e" if i%2 else "#df927a")
        elif kind=="dinner":
            d.ellipse((x-30,y-10,x+24,y+14),fill="#b77b58",outline=INK,width=2)
            d.line((x+22,y,x+38,y+5),fill="#f8efe0",width=5)


def draw_prop(image, kind, t, behind=False):
    if (kind in BEHIND) != behind:
        return
    if kind == "none": return
    d = ImageDraw.Draw(image)
    s = math.sin(t*TAU); c = math.cos(t*TAU)
    if kind=="breakstar":
        if t<.55: star(d,320,54,20)
        else:
            for i in range(7):
                a=i*TAU/7; r=20+(t-.55)*100
                star(d,320+r*math.cos(a),54+r*.6*math.sin(a),5)
        return
    if kind in FOODS:
        food(d,kind,t); return
    if kind in {"music","hearts","confetti","sparkles","laugh","blush","anger","surprise","stretch","squat","yawn","alarm","sweat","speed","splash"}:
        if kind=="music":
            for i in range(4): d.text((215+i*68,100+20*math.sin(t*TAU+i)),"♪",font=font(22),fill=ORANGE)
        elif kind=="hearts":
            for i in range(4): heart(d,225+i*63,96-(t*40+i*8)%55,8,PINK)
        elif kind in {"sparkles","stretch","confetti"}:
            for i in range(12 if kind=="confetti" else 5):
                x=215+(i*47)%220; y=40+(i*29+t*30)%150
                star(d,x,y,4+(i%3),[ORANGE,PINK,BLUE][i%3])
        elif kind=="blush":
            for side in (-1,1): heart(d,320+side*98,142+s*4,10)
        elif kind=="anger":
            d.arc((405,80,428,102),180,270,fill="#d37268",width=4)
            d.arc((416,80,439,102),270,360,fill="#d37268",width=4)
            d.arc((405,91,428,113),90,180,fill="#d37268",width=4)
        elif kind in {"surprise","alarm"}:
            bubble(d,435,105,"!" if kind=="surprise" else "醒！",19)
            if kind=="alarm":
                d.ellipse((215,275,252,312),fill=ORANGE,outline=INK,width=2)
                d.line((234,282,234,295,242,300),fill=INK,width=2)
        elif kind=="yawn": bubble(d,427,110,"Zz",17)
        elif kind=="laugh": bubble(d,430,104,"嘿嘿",15)
        elif kind=="sweat":
            for i in range(3):
                x=395+i*13; y=95+(t*35+i*12)%52
                d.polygon([(x,y-8),(x-4,y),(x+4,y)],fill=BLUE)
                d.ellipse((x-4,y-4,x+4,y+4),fill=BLUE,outline=INK)
        elif kind=="speed":
            for i in range(4): d.line((415,210+i*22,460+(i%2)*15,210+i*22),fill=BLUE,width=3)
        elif kind=="splash":
            for i in range(7):
                x=395+(i-3)*10; y=327-abs(math.sin(t*TAU+i))*28
                d.ellipse((x-3,y-4,x+3,y+3),fill=BLUE,outline=INK)
        elif kind=="squat": d.arc((270,316,370,344),0,180,fill=ORANGE,width=3)
        return
    if kind in {"desk","wipedesk","notebook","fu","laptop","terminal","screenchat","folder","gomoku","needle"}:
        d.rounded_rectangle((246,266,413,278),radius=5,fill="#e5c5a0",outline=INK,width=2)
        if kind in {"desk","wipedesk"}:
            if kind=="wipedesk":
                x=315+s*40
                d.rounded_rectangle((x-20,255,x+20,266),radius=5,fill=BLUE,outline=INK,width=1)
                star(d,385,243,5)
            else:
                for i in range(2): star(d,299+i*45,252-4*abs(s),3)
        elif kind in {"laptop","terminal","screenchat"}:
            d.rounded_rectangle((270,213,382,263),radius=5,fill="#7d99b9",outline=INK,width=2)
            d.rounded_rectangle((275,218,377,258),radius=3,fill="#263c53")
            for i in range(4):
                d.line((282,225+i*7,311+((i+int(t*8))%3)*16,225+i*7),fill="#9dd8be",width=2)
            d.polygon([(264,263),(388,263),(399,271),(255,271)],fill="#a8bdce",outline=INK)
            if kind=="screenchat": bubble(d,435,180,"聊两句",13)
            if kind=="terminal": d.text((325,235),">_",font=font(20),fill="#c7e8bd",anchor="mm")
        elif kind in {"notebook","fu"}:
            d.polygon([(281,223),(367,226),(381,266),(270,266)],fill="#d77c68" if kind=="fu" else "#fff9e9",outline=INK,width=2)
            if kind=="fu": d.text((326,246),"福",font=font(28),fill="#f4d58e",anchor="mm")
            else:
                d.line((324,226,325,263),fill="#c3b9a6",width=1)
                for i in range(int(t*5)%5+1): d.line((286,236+i*5,315,237+i*5),fill=BLUE,width=1)
            d.line((350+s*8,238,364+s*8,207),fill=INK,width=3)
        elif kind=="folder":
            for i in range(4): d.rounded_rectangle((279+i*6,255-i*8,365+i*6,270-i*8),radius=3,fill=["#e9bb72","#8fb9c6"][i%2],outline=INK,width=1)
            d.rectangle((318+s*9,203,353+s*9,241),fill=CREAM,outline=INK,width=2)
            for i in range(3): d.line((324+s*9,214+i*6,345+s*9,214+i*6),fill=BLUE,width=1)
        elif kind=="gomoku":
            d.rectangle((268,218,385,269),fill="#deb67d",outline=INK,width=2)
            for i in range(8):
                d.line((275+i*14,221,275+i*14,265),fill="#a77f55",width=1)
                d.line((272,222+i*6,382,222+i*6),fill="#a77f55",width=1)
            for i in range(3+int(t*6)%6):
                x=286+(i*28)%84; y=228+(i*12)%30
                d.ellipse((x-4,y-3,x+4,y+3),fill=INK if i%2 else CREAM,outline=INK)
        elif kind=="needle":
            d.ellipse((294,230,348,263),fill="#f0d7d6",outline=INK,width=2)
            d.arc((307,215,366,262),20,320,fill=PINK,width=3)
            d.line((320+s*12,223,341+s*12,244),fill="#6b8096",width=2)
        return
    if kind in {"fan","toothbrush","mirror","palette","cube","console","watergun","violin","flute","cards","top","gift","redpacket","pumpkin","balls","shuttlecock","car","rockinghorse"}:
        if kind=="fan":
            x,y=382+s*8,210
            d.pieslice((x-42,y-42,x+42,y+42),195,345,fill="#b2d0e0",outline=INK,width=2)
            for angle in (205,230,255,280,305,335):
                a=math.radians(angle); d.line((x,y,x+40*math.cos(a),y+40*math.sin(a)),fill=INK,width=1)
            d.line((x,y,x-5,y+30),fill=ORANGE,width=3)
        elif kind=="toothbrush":
            x=342+s*9
            d.line((x,179,x+30,197),fill=BLUE,width=5)
            d.rounded_rectangle((x-8,173,x+10,181),radius=3,fill=CREAM,outline=INK)
            for i in range(5): d.ellipse((319+i*6,177+(i%2)*5,328+i*6,185+(i%2)*5),fill="#f9fbfd",outline="#c7d7e5")
        elif kind=="mirror":
            d.ellipse((386,154,432,215),fill="#c0dcea",outline=ORANGE,width=5)
            d.line((408,213,411,246),fill=ORANGE,width=7)
            d.line((396,170,417,193),fill=CREAM,width=3)
        elif kind=="palette":
            d.ellipse((389,211,436,246),fill="#e3bd91",outline=INK,width=2)
            for i,color in enumerate((BLUE,PINK,ORANGE,"#91bd91")): d.ellipse((397+i*8,218,404+i*8,226),fill=color,outline=INK)
            d.line((385,242,409,208),fill=INK,width=3)
        elif kind=="cube":
            x,y=297+s*3,219
            colors=["#df8b85","#8ebbd9","#ebc776","#97bf92","#f3ece3","#c1a4cf"]
            for row in range(3):
                for col in range(3):
                    d.rectangle((x+col*16,y+row*15,x+col*16+15,y+row*15+14),fill=colors[(row+col+int(t*4))%6],outline=INK,width=1)
        elif kind=="console":
            d.rounded_rectangle((276,226,370,262),radius=10,fill="#8bb6cc",outline=INK,width=2)
            d.rectangle((299,233,347,256),fill="#354c62",outline=INK)
            d.line((287,236,287,252),fill=INK,width=3); d.line((280,244,294,244),fill=INK,width=3)
            d.ellipse((354,235,360,241),fill=PINK); d.ellipse((361,246,367,252),fill=ORANGE)
            if s>.2: bubble(d,430,153,"!!",16)
        elif kind=="watergun":
            d.rounded_rectangle((355,209,430,232),radius=7,fill=BLUE,outline=INK,width=2)
            d.polygon([(376,230),(394,230),(390,255),(377,251)],fill=ORANGE,outline=INK)
            d.ellipse((368,197,405,219),fill="#b9e1e1",outline=INK,width=2)
            d.line((428,217,478+20*s,207-8*s),fill="#8bd1ed",width=3)
            for i in range(3): d.ellipse((476+i*8,204+i*4,481+i*8,209+i*4),fill=BLUE)
        elif kind=="violin":
            d.ellipse((309,211,348,241),fill="#c78d5a",outline=INK,width=2)
            d.ellipse((315,232,346,260),fill="#c78d5a",outline=INK,width=2)
            d.line((334,222,356,183),fill="#9c694f",width=6)
            d.line((326,247,351,192),fill=INK,width=1)
            d.line((284+s*16,225,369+s*16,250),fill="#77594c",width=3)
        elif kind=="flute":
            d.line((306,179,414,201),fill="#c6a267",width=9)
            for i in range(6): d.ellipse((325+i*13,181+i*2.7,329+i*13,185+i*2.7),fill=INK)
            d.text((424,178+s*5),"♪",font=font(20),fill=ORANGE)
        elif kind=="cards":
            for i in range(5):
                x=277+i*17; y=223+abs(i-2)*4
                d.rounded_rectangle((x,y,x+25,y+34),radius=3,fill=CREAM,outline=INK,width=1)
                heart(d,x+12,y+14,5,"#cd797e" if i%2 else INK)
            star(d,397,191+s*10,9)
        elif kind=="top":
            x=419+s*7
            d.ellipse((x-19,306,x+19,318),fill=BLUE,outline=INK,width=2)
            d.polygon([(x-18,313),(x+18,313),(x,341)],fill=ORANGE,outline=INK,width=2)
            d.line((x,297,x,311),fill=INK,width=3)
            d.arc((390,305,449,335),int(t*360),int(t*360)+230,fill=BLUE,width=2)
            d.line((369,240,395+s*18,293),fill="#ad865d",width=2)
        elif kind in {"gift","redpacket","pumpkin"}:
            if kind=="gift":
                d.rounded_rectangle((287,244,363,297),radius=5,fill="#a5c7cd",outline=INK,width=2)
                d.rectangle((319,243,330,297),fill=ORANGE)
                y=231-18*max(0,s)
                d.rounded_rectangle((281,y,369,y+16),radius=4,fill=PINK,outline=INK,width=2)
                d.line((325,y,325,y+15),fill=ORANGE,width=8)
                for i in range(4): star(d,291+i*23,218-abs(s)*20,4)
            elif kind=="redpacket":
                d.rounded_rectangle((291,221,357,290),radius=6,fill="#d88072",outline=INK,width=2)
                d.arc((291,206,357,252),0,180,fill="#efcd84",width=3)
                d.text((324,260),"福",font=font(23),fill="#f5d789",anchor="mm")
                for i in range(4): star(d,275+i*32,204-(t*30+i*8)%60,4)
            else:
                d.ellipse((279,235,370,294),fill="#e5a15d",outline=INK,width=2)
                for i in range(3): d.arc((286+i*20,235,317+i*20,294),-80,80,fill="#bc7d46",width=1)
                d.rectangle((319,226,329,238),fill="#87a478",outline=INK)
                d.polygon([(300,251),(292,263),(309,262)],fill="#6d5559")
                d.polygon([(347,251),(338,263),(355,262)],fill="#6d5559")
                d.arc((301,260,350,283),0,180,fill="#6d5559",width=4)
        elif kind=="balls":
            for i,color in enumerate((PINK,BLUE,ORANGE)):
                a=t*TAU+i*TAU/3; x=320+65*math.cos(a); y=178-75*abs(math.sin(a))
                d.ellipse((x-11,y-11,x+11,y+11),fill=color,outline=INK,width=2)
        elif kind=="shuttlecock":
            x=382+15*s; y=285-70*abs(s)
            d.ellipse((x-8,y+5,x+8,y+14),fill=ORANGE,outline=INK,width=2)
            for i,color in enumerate((PINK,BLUE,CREAM)):
                d.polygon([(x,y+7),(x-19+i*16,y-20),(x-10+i*11,y-23)],fill=color,outline=INK)
        elif kind=="car":
            x=387+24*s
            d.rounded_rectangle((x-35,310,x+35,331),radius=7,fill=BLUE,outline=INK,width=2)
            d.polygon([(x-23,310),(x-9,293),(x+14,293),(x+27,310)],fill="#bddde5",outline=INK)
            for side in (-1,1):
                d.ellipse((x+side*20-9,321,x+side*20+9,339),fill=INK)
                d.line((x+side*20,325,x+side*20+5*c,330+5*s),fill=CREAM,width=2)
        elif kind=="rockinghorse":
            d.arc((256,285+s*4,398,351+s*4),5,175,fill="#a67553",width=8)
            d.rounded_rectangle((276,273,372,310),radius=17,fill="#d6ae7e",outline=INK,width=2)
            d.polygon([(362,281),(371,236),(393,234),(406,256),(389,266),(386,299)],fill="#d6ae7e",outline=INK,width=2)
            d.ellipse((384,242,388,246),fill=INK)
            d.polygon([(370,239),(376,222),(382,237)],fill="#d6ae7e",outline=INK)
        return
    if kind in {"pillow","hello","chat","foodquestion","thought","clock","ribbon","balloon","dove","cat","animals","flower","butterflies","chrysanthemum","kite","bubbles","whale","leaves","snowman","fireworks","lotus","lion","ghost","christmastree","skylantern","swing"} or kind.startswith("money"):
        if kind=="pillow":
            d.rounded_rectangle((242,301,411,345),radius=17,fill="#a8c5df",outline=INK,width=2)
            d.text((414,230-15*t),"Zzz",font=font(25),fill=BLUE)
        elif kind in {"hello","chat","foodquestion","thought","clock"}:
            if kind=="clock":
                d.ellipse((413,137,461,185),fill=CREAM,outline=INK,width=2)
                d.line((437,145,437,161,437+12*s,161-12*c),fill=INK,width=2)
            else:
                text={"hello":"Hi~","chat":"嗯…","foodquestion":"是啊，吃什么","thought":"…"}[kind]
                bubble(d,440 if kind!="foodquestion" else 320,110 if kind!="foodquestion" else 52,text,15)
                if kind=="thought":
                    for i in range(2): d.ellipse((391-i*8,143+i*10,399-i*8,151+i*10),fill=CREAM,outline=INK)
        elif kind=="ribbon":
            points=[(210+i*13,198+30*math.sin(i*.5+t*TAU)) for i in range(18)]
            d.line(points,fill=PINK,width=5)
        elif kind=="balloon":
            r=22+12*(.5+.5*s); x=415; y=173-r*.5
            d.line((370,236,x,y+r+15),fill=INK,width=1)
            d.ellipse((x-r,y-r*1.2,x+r,y+r),fill=PINK,outline=INK,width=2)
            d.polygon([(x,y+r-1),(x-5,y+r+8),(x+5,y+r+8)],fill=PINK,outline=INK)
        elif kind=="dove":
            x=416+15*s; y=142-28*abs(s)
            d.ellipse((x-22,y-10,x+19,y+13),fill=CREAM,outline=INK,width=2)
            d.polygon([(x,y),(x-17,y-26-12*s),(x+13,y-18-12*s)],fill="#e3ebed",outline=INK)
            d.polygon([(x+18,y-3),(x+28,y),(x+17,y+4)],fill=ORANGE)
            d.ellipse((x+11,y-6,x+14,y-3),fill=INK)
        elif kind in {"cat","animals"}:
            if kind=="cat": cat(d,407,309,1.1,t)
            else:
                for i in range(3):
                    a=t*TAU+i*TAU/3
                    cat(d,320+132*math.cos(a),219+95*math.sin(a),.55,t,["#a6b6ce","#d5b799","#e5ddcc"][i])
        elif kind in {"flower","butterflies","chrysanthemum"}:
            if kind=="flower":
                d.polygon([(391,278),(430,278),(423,314),(399,314)],fill="#d6a384",outline=INK,width=2)
                d.line((411,278,410,230-15*max(0,s)),fill="#7a9e77",width=4)
                flower(d,410,224-15*max(0,s),17)
            elif kind=="chrysanthemum":
                for i in range(3):
                    d.line((398+i*15,307,395+i*16,259+i*5),fill="#7d9b70",width=3)
                    flower(d,395+i*16,252+i*5,13,"#edc87e")
                d.polygon([(401,246),(420,230),(424,248),(413,252)],fill="#a2b17c",outline=INK)
            else:
                flower(d,320,35,12)
                for i in range(3):
                    a=t*TAU+i*TAU/3; x=320+116*math.cos(a); y=124+65*math.sin(a)
                    d.ellipse((x-14,y-11,x,y+7),fill=PINK,outline=INK)
                    d.ellipse((x,y-11,x+14,y+7),fill=BLUE,outline=INK)
                    d.line((x,y-6,x,y+9),fill=INK,width=2)
        elif kind=="kite":
            x=436+24*s; y=58+8*c
            d.line((359,225,x,y+25),fill="#b8a58a",width=1)
            d.polygon([(x,y-28),(x+24,y),(x,y+32),(x-24,y)],fill=PINK,outline=INK,width=2)
            d.line((x,y-28,x,y+32),fill=INK,width=1); d.line((x-24,y,x+24,y),fill=INK,width=1)
            d.line([(x,y+32),(x+7,y+45),(x-3,y+57),(x+10,y+68)],fill=BLUE,width=2)
        elif kind=="bubbles":
            for i in range(8):
                x=225+(i*67)%220+5*math.sin(t*TAU+i); y=300-(t*100+i*32)%265; r=6+i%4*3
                d.ellipse((x-r,y-r,x+r,y+r),outline="#8ebfd9",width=2)
                d.arc((x-r+3,y-r+3,x+r-3,y+r-3),185,265,fill=CREAM,width=2)
        elif kind=="whale": whale(d,359+10*s,180,1.8,t)
        elif kind=="leaves":
            for i in range(20):
                x=210+(i*37)%230+10*math.sin(t*TAU+i); y=10+(t*120+i*23)%310
                d.ellipse((x-7,y-3,x+7,y+3),fill=[ORANGE,"#c29a6c","#c3b476"][i%3],outline=INK)
            for i in range(int(14*t)+4):
                x=240+(i*23)%160; y=339-(i%3)*5
                d.ellipse((x-12,y-5,x+12,y+5),fill=ORANGE,outline=INK)
        elif kind=="snowman":
            d.ellipse((390,281,464,343),fill="#f4f8f9",outline=INK,width=2)
            d.ellipse((400,239,455,289),fill="#f4f8f9",outline=INK,width=2)
            for x in (414,439): d.ellipse((x-2,254,x+2,258),fill=INK)
            d.polygon([(427,262),(444,265),(427,269)],fill=ORANGE,outline=INK)
            d.line((402,285,454,287),fill=PINK,width=7)
            for i in range(8): d.ellipse((230+i*29,10+(i*53+t*40)%310,233+i*29,13+(i*53+t*40)%310),fill="#dcebf2")
        elif kind=="fireworks":
            for j in range(3):
                x=225+j*95; y=75+(j%2)*35; radius=10+30*((t+j*.3)%1)
                for i in range(10):
                    a=i*TAU/10
                    d.line((x+radius*.6*math.cos(a),y+radius*.6*math.sin(a),x+radius*math.cos(a),y+radius*math.sin(a)),fill=[ORANGE,PINK,BLUE][j],width=3)
        elif kind=="lotus":
            x=403+15*s; y=316
            d.arc((365,314,471,346),0,175,fill=BLUE,width=2)
            for i in (-1,0,1): d.ellipse((x+i*15-13,y-18-abs(i)*4,x+i*15+13,y+10),fill=PINK,outline=INK,width=1)
            d.ellipse((x-6,y-18,x+6,y-3),fill="#f1ce7d",outline=INK)
        elif kind=="lion":
            d.rounded_rectangle((247,97+s*5,391,190+s*5),radius=25,fill=ORANGE,outline=INK,width=3)
            for x in (281,356):
                d.ellipse((x-24,107+s*5,x+24,153+s*5),fill=CREAM,outline=INK,width=2)
                d.ellipse((x-9,123+s*5,x+9,141+s*5),fill=INK)
            d.rounded_rectangle((285,154+s*5,354,181+s*5),radius=9,fill=CREAM,outline=INK,width=2)
            for x in range(296,349,13): d.line((x,155+s*5,x,180+s*5),fill=INK,width=1)
            flower(d,320,103+s*5,12,"#d87866")
        elif kind=="ghost":
            d.ellipse((228,40+s*8,412,245+s*8),fill=(245,248,250,100),outline="#aec2d5",width=2)
            for i in range(3): d.arc((232+i*57,205+s*8,293+i*57,263+s*8),0,180,fill="#aec2d5",width=2)
        elif kind=="christmastree":
            x=450
            d.rectangle((x-7,293,x+7,335),fill="#a67d58",outline=INK)
            for i in range(3):
                y=167+i*44; w=38+i*12
                d.polygon([(x,y-30),(x-w,y+40),(x+w,y+40)],fill="#7aa38e",outline=INK,width=2)
            star(d,x,136,12)
            for i in range(8):
                x1=x-30+(i*19)%60; y=185+(i*23)%108
                d.ellipse((x1-4,y-4,x1+4,y+4),fill=PINK if (i+int(t*4))%2 else ORANGE,outline=INK)
        elif kind=="skylantern":
            x=425+8*s; y=185-105*t
            d.rounded_rectangle((x-28,y-33,x+28,y+28),radius=10,fill="#edb376",outline=INK,width=2)
            d.ellipse((x-23,y+19,x+23,y+32),fill="#f5d598",outline=INK)
            d.polygon([(x,y+12),(x-5,y+26),(x+5,y+26)],fill="#df895d")
        elif kind=="swing":
            for x in (258,383): d.line((x,23,x+15*s,296),fill="#ad916e",width=3)
            d.rounded_rectangle((249+15*s,295,394+15*s,307),radius=4,fill="#d1ac7e",outline=INK,width=2)
        elif kind.startswith("money"):
            level=int(kind[-1]); fill=max(0,6-level)
            d.polygon([(293,233),(351,233),(366,281),(355,305),(291,305),(280,281)],fill="#ddb97c",outline=INK,width=2)
            d.line((290,235,354,235),fill="#a57854",width=4)
            d.text((323,276),"T",font=font(25),fill="#9b7647",anchor="mm")
            for i in range(fill):
                x=286+i*13; y=220-abs(math.sin(t*TAU+i))*12
                d.ellipse((x-8,y-6,x+8,y+6),fill="#f3cf7a",outline=INK,width=1)
            if level==5: bubble(d,435,152,"空了…",14)
        return
    raise ValueError(f"未实现的道具：{kind}")
