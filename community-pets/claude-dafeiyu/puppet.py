"""将同一角色的独立部件按关键姿势与双关节步态渲染为透明视频帧。"""
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance
from build import isolate_cell
from props import draw_prop, font, INK

ROOT = Path(__file__).resolve().parent
TAU = math.tau
SIZE = (640, 360)


def crop_alpha(image):
    image = isolate_cell(image.convert("RGBA"))
    bbox = image.getchannel("A").getbbox()
    if not bbox:
        raise ValueError("角色部件为空")
    return image.crop(bbox)


def scale_height(image, height):
    return image.resize((max(1,round(image.width*height/image.height)), round(height)), Image.Resampling.LANCZOS)


def put(image, sprite, anchor, pivot=(.5,.5), angle=0):
    if image.height==440:
        anchor=(anchor[0],anchor[1]+40)
    px, py = sprite.width*pivot[0], sprite.height*pivot[1]
    if abs(angle) < .05:
        image.alpha_composite(sprite,(round(anchor[0]-px),round(anchor[1]-py)))
        return
    radius = math.ceil(max(px,py,sprite.width-px,sprite.height-py))+3
    layer = Image.new("RGBA",(radius*2,radius*2))
    layer.alpha_composite(sprite,(round(radius-px),round(radius-py)))
    layer = layer.rotate(angle,resample=Image.Resampling.BICUBIC)
    image.alpha_composite(layer,(round(anchor[0]-radius),round(anchor[1]-radius)))


def knee_chain(image, thigh, shin, hip, foot, bend=-1):
    """双关节逆运动学：支撑期脚底固定，摆动期脚尖沿弧线抬起。"""
    dx, dy = foot[0]-hip[0], foot[1]-hip[1]
    l1, l2 = thigh.height-1, shin.height-1
    distance = min(math.hypot(dx,dy),l1+l2-.01)
    distance = max(distance,abs(l2-l1)+.01)
    axis = math.atan2(dx,dy)
    beta = math.acos(max(-1,min(1,(l1*l1+distance*distance-l2*l2)/(2*l1*distance))))
    a1 = axis + bend*beta
    knee = (hip[0]+math.sin(a1)*l1,hip[1]+math.cos(a1)*l1)
    a2 = math.atan2(foot[0]-knee[0],foot[1]-knee[1])
    put(image,thigh,hip,(.5,0),math.degrees(a1))
    put(image,shin,knee,(.5,0),math.degrees(a2))


class Puppet:
    def __init__(self):
        atlas=Image.open(ROOT/"sources"/"puppet-atlas.png").convert("RGBA")
        # 生成 atlas 并非严格等格；边界由原图目视确认，不能按 4×2 强切。
        boxes={"head":(0,0,.278,.562),"armL":(.552,.07,.699,.471),"armR":(.812,.07,.957,.471),
               "legL":(.08,.563,.205,.966),"legR":(.32,.558,.445,.966),
               "tail":(.492,.593,.737,.918),"closed":(.739,.493,1,1)}
        parts={}
        for name,box in boxes.items():
            bounds=tuple(round(v*(atlas.width if i%2==0 else atlas.height)) for i,v in enumerate(box))
            parts[name]=crop_alpha(atlas.crop(bounds))
        parts["body"]=crop_alpha(Image.open(ROOT/"sources"/"torso.png"))
        for name,height in {"head":225,"closed":225,"body":121,"armL":86,"armR":86,"legL":74,"legR":74,"tail":86}.items():
            parts[name]=scale_height(parts[name],height)
        parts["closed"]=parts["closed"].resize(parts["head"].size,Image.Resampling.LANCZOS)
        self.parts=parts
        self.profile=scale_height(crop_alpha(Image.open(ROOT/"sources"/"profile.png")),258)
        self.legs={}
        for side in ("L","R"):
            leg=parts["leg"+side]
            split=26
            self.legs[side]=(leg.crop((0,0,leg.width,split+2)),leg.crop((0,split,leg.width,leg.height)))
        output=ROOT/"sources"/"rig"
        output.mkdir(exist_ok=True)
        for name,part in {**parts,"profile":self.profile}.items(): part.save(output/(name+".png"))

    def walk(self,t,run=False):
        """基准素材向左；向右由宿主统一镜像，视频本身不平移。"""
        image=Image.new("RGBA",SIZE)
        active=max(0,min(4,t-.5))
        walking=.5 < t < 4.5
        phase=active*(1.6 if run else 1.0)
        body_y=277-(2 if run else 1.2)*math.cos(phase*TAU*2) if walking else 276
        foot_states=[]
        for side,offset in (("R",.5),("L",0)):
            p=(phase+offset)%1
            if not walking: dx, lift=(-10 if side=="R" else 10),0
            elif p < .5: dx,lift=-23+92*p,0
            else:
                u=(p-.5)*2
                dx=23*math.cos(math.pi*u)
                lift=(26 if run else 18)*math.sin(math.pi*u)
            foot_states.append((side,(320+dx,347-lift)))
        far=Image.new("RGBA",SIZE)
        knee_chain(far,*self.legs["R"],(324,body_y),foot_states[0][1])
        far=ImageEnhance.Brightness(far).enhance(.83)
        image.alpha_composite(far)
        arm_phase=math.sin(phase*TAU) if walking else 0
        put(image,self.parts["armR"],(309,214+body_y-277),(.1,.02),-18*arm_phase)
        knee_chain(image,*self.legs["L"],(317,body_y),foot_states[1][1])
        put(image,self.profile,(320,body_y+4),(.28,.905),3 if run else 0)
        d=ImageDraw.Draw(image)
        d.line((315,214,320,235,332,216),fill="#bb8c52",width=2)
        d.rounded_rectangle((306,234,334,247),radius=2,fill="#f5dfbd",outline=INK,width=1)
        d.text((320,240),"Claude",font=font(6),fill=INK,anchor="mm")
        put(image,self.parts["armL"],(341,213+body_y-277),(.88,.02),18*arm_phase)
        return image

    def render(self,pose,prop,t):
        image=Image.new("RGBA",SIZE)
        draw_prop(image,prop,t,behind=True)
        s=math.sin(t*TAU); c=math.cos(t*TAU); hit=math.sin(math.pi*t)
        arm_l,arm_r,leg_l,leg_r=0,0,0,0
        dy,tilt,head,tail,dx,closed=0,0,0,7*s,0,False
        if pose=="idle": dy=-1.2*s; head=.8*s
        elif pose=="look": head=7*s; tilt=2*s
        elif pose=="drag": arm_l=-28; arm_r=28; leg_l=-12-8*s; leg_r=17+6*s; dy=-20; tilt=8*s
        elif pose=="jump": dy=-35*hit; arm_l=-135*hit; arm_r=135*hit; leg_l=-15*hit; leg_r=15*hit; closed=True
        elif pose=="shy": arm_l=145*hit; arm_r=-145*hit; head=-9*hit; closed=hit>.55
        elif pose=="angry": arm_l=-35; arm_r=35; tilt=3*math.sin(t*TAU*3); head=-3
        elif pose=="laugh": arm_l=55; arm_r=-55; dy=-3*abs(math.sin(t*TAU*2)); tilt=3*s; closed=True
        elif pose=="wave": arm_l=-138+18*math.sin(t*TAU*2); arm_r=-26; head=-3
        elif pose=="crab": leg_l=13*s; leg_r=-13*s; arm_l=-35+8*c; arm_r=35+8*c; dy=-3*abs(c)
        elif pose=="float": dy=-18-7*s; arm_l=-28+7*c; arm_r=28-7*c; leg_l=12*s; leg_r=-12*s
        elif pose=="run": return self.walk(t*5,True)
        elif pose=="sway": tilt=4*s; arm_l=-10-10*s; arm_r=10-10*s
        elif pose=="stretch": arm_l=-125*hit; arm_r=125*hit; dy=-9*hit; head=-4*hit; closed=True
        elif pose=="tap": arm_l=58+8*math.sin(t*TAU*3); arm_r=-62-8*math.cos(t*TAU*3)
        elif pose=="squat": dy=26*hit; leg_l=-20*hit; leg_r=20*hit; arm_l=20*hit; arm_r=-20*hit
        elif pose=="yawn": arm_r=-142*hit; head=-5*hit; closed=True
        elif pose=="sleep": arm_l=75; arm_r=-75; leg_l=-12; leg_r=22; closed=True
        elif pose=="curtsy": dy=17*hit; tilt=7*hit; arm_l=30; arm_r=-30; leg_l=-12*hit; leg_r=12*hit; closed=hit>.5
        elif pose=="startle": arm_l=-80*hit; arm_r=80*hit; dy=-23*hit; leg_l=-12*hit; leg_r=12*hit
        elif pose=="spin": tilt=2*s; arm_l=-45; arm_r=45; head=-8*s
        elif pose=="guilty": arm_l=69; arm_r=-130+12*s; head=8*s
        elif pose=="tail": tail=34*math.sin(t*TAU*3); head=3*s; arm_l=-12; arm_r=12
        elif pose=="wake":
            closed=t<.5; head=10*s; dy=12 if t<.5 else -18*math.sin((t-.5)*math.pi*2); arm_l=-60 if t>.5 else 35; arm_r=-arm_l
        elif pose=="mirror": arm_r=-84; head=-6+4*s
        elif pose=="dress": arm_l=-32; arm_r=32; head=4*s
        elif pose=="write": arm_l=55; arm_r=-73-9*math.sin(t*TAU*3); head=4
        elif pose=="type": arm_l=64+5*math.sin(t*TAU*4); arm_r=-64+5*math.cos(t*TAU*4); head=1.5*s
        elif pose=="fan": arm_r=-85+22*math.sin(t*TAU*3); arm_l=15; head=-3
        elif pose=="brush": arm_r=-135+5*math.sin(t*TAU*5); arm_l=15; head=2*s
        elif pose=="cube": arm_l=72+9*s; arm_r=-75+9*c; head=-4*s
        elif pose=="toy": dy=27; arm_r=-45+14*s; arm_l=15; head=5
        elif pose=="blow": arm_l=90; arm_r=-110; head=-3; dy=-2*s
        elif pose=="reach": dy=-28*hit; arm_r=160*hit; arm_l=-125*hit; leg_l=-18*hit; leg_r=18*hit
        elif pose=="game": arm_l=65+7*math.sin(t*TAU*3); arm_r=-65; head=3*math.sin(t*TAU*2); tilt=2*s
        elif pose=="shoot": arm_r=-85; arm_l=65; tilt=-4; head=-3
        elif pose=="violin": arm_l=62+13*s; arm_r=-124; head=-8
        elif pose=="summon": arm_l=-110*hit; arm_r=110*hit; dy=-5*hit
        elif pose=="ballet": arm_l=-100-30*s; arm_r=100+30*s; leg_l=18*s; leg_r=-18*s; tilt=7*s; dy=-5*abs(s)
        elif pose=="dance": arm_l=-60-45*s; arm_r=60-45*s; leg_l=15*s; leg_r=-15*s; tilt=8*s; dx=6*s
        elif pose=="idol": arm_l=-135+30*s; arm_r=135+30*c; leg_l=17*s; leg_r=-17*s; dy=-7*abs(s); head=4*s
        elif pose=="pet": arm_r=-60+10*s; arm_l=15; head=5*s; dy=5
        elif pose=="kite": arm_r=-70+6*s; arm_l=10; head=-6
        elif pose=="gift": arm_l=65; arm_r=-65-15*max(0,s); head=3*s
        elif pose=="magic": arm_l=-55-25*s; arm_r=-75+20*c; head=-6*s
        elif pose=="whip": arm_r=-75+38*math.sin(t*TAU*2); arm_l=15; tilt=4*s
        elif pose=="flute": arm_l=115; arm_r=-122; head=-3*s
        elif pose=="garden": arm_l=-50*hit; arm_r=50*hit; head=5*s
        elif pose=="ride": dy=14+3*s; leg_l=-40; leg_r=40; arm_l=65; arm_r=-65; tilt=4*s
        elif pose=="juggle": arm_l=85+25*s; arm_r=-85+25*s; head=-3*c
        elif pose=="kick": leg_r=35*max(0,s); leg_l=-5; arm_l=-25; arm_r=40; tilt=-4*max(0,s)
        elif pose=="board": arm_l=55; arm_r=-67+12*s; head=5
        elif pose=="swing": dy=8+5*c; dx=15*s; tilt=4*s; arm_l=-140; arm_r=140; leg_l=17*s; leg_r=-17*s
        elif pose=="eat": arm_l=65; arm_r=-80-47*max(0,math.sin(t*TAU*2)); head=-2*s
        elif pose=="lick": arm_l=85; arm_r=-95-23*max(0,s); head=2*s
        elif pose=="noodles": arm_l=65; arm_r=-120+10*s; head=3
        elif pose=="hotpot": arm_l=65; arm_r=-75-23*s; head=3*s
        elif pose=="leaves": arm_l=-30-15*s; arm_r=30+15*s; dy=4*t; head=4*s
        elif pose=="build": dy=12; arm_l=30; arm_r=-50+20*s; head=5
        elif pose=="celebrate": arm_l=-116+12*s; arm_r=116-12*s; dy=-12*abs(s); closed=True
        elif pose=="thread": arm_l=78+5*s; arm_r=-83-5*s; head=5
        elif pose=="lion": arm_l=-147; arm_r=147; leg_l=12*s; leg_r=-12*s; dy=-4*abs(s)
        elif pose=="lantern": arm_l=70*hit; arm_r=-70*hit; head=-5*hit
        elif pose=="ghost": arm_l=-75+12*s; arm_r=75-12*s; dy=-10-5*s; head=4*s
        elif pose=="tree": arm_r=115+15*s; arm_l=10; head=-3
        elif pose=="shrug": arm_l=-80; arm_r=80; head=7*s
        elif pose=="think": arm_r=-142+4*s; arm_l=45; head=-6
        elif pose=="money": arm_l=65; arm_r=-65+5*s; head=2*s
        elif pose=="count": arm_l=65; arm_r=-80+12*math.sin(t*TAU*3); head=5
        elif pose=="sad": head=10; tilt=2*s; arm_l=10; arm_r=-10; dy=7; tail=-15
        elif pose=="wipe": arm_l=58; arm_r=-68+20*s; head=2*s
        elif pose=="file": arm_l=65; arm_r=-85-25*max(0,s); head=3*s
        elif pose=="wait": leg_l=8*s; leg_r=-8*s; head=8*s; arm_l=10; arm_r=-10
        else: raise ValueError(f"未实现的姿势：{pose}")
        actor=Image.new("RGBA",(640,440))
        p=self.parts
        put(actor,p["tail"],(362+dx,277+dy),(.1,.65),tail)
        for side,angle,x in (("R",leg_r,335),("L",leg_l,305)):
            thigh,shin=self.legs[side]
            a=math.radians(angle)
            hip=(x+dx,277+dy*.32)
            if pose in {"squat","toy","curtsy"}:
                knee_chain(actor,thigh,shin,(x+dx,277+dy*.8),(x+dx,347),-1 if side=="L" else 1)
                continue
            put(actor,thigh,hip,(.5,0),angle)
            knee=(hip[0]+math.sin(a)*(thigh.height-1),hip[1]+math.cos(a)*(thigh.height-1))
            put(actor,shin,knee,(.5,0),angle*.7)
        put(actor,p["closed"] if closed else p["head"],(320+dx,24+dy),(.5,0),head)
        body=p["body"]
        if pose=="dress":
            body=body.copy()
            tint=Image.new("RGBA",body.size,["#ffd4ae","#d3e7f3","#ecd6ee"][min(2,int(t*3))])
            body=Image.blend(body,tint,.12)
            body.putalpha(p["body"].getchannel("A"))
        put(actor,body,(320+dx,175+dy),(.5,0),tilt*.35)
        put(actor,p["armL"],(291+dx,188+dy),(.88,.02),arm_l+tilt)
        put(actor,p["armR"],(349+dx,188+dy),(.1,.02),arm_r+tilt)
        if pose=="sleep":
            box=actor.getchannel("A").getbbox()
            sleeping=actor.crop(box).rotate(78+1.5*s,resample=Image.Resampling.BICUBIC,expand=True)
            sleeping.thumbnail((330,175),Image.Resampling.LANCZOS)
            actor=Image.new("RGBA",SIZE)
            actor.alpha_composite(sleeping,((640-sleeping.width)//2,329-sleeping.height))
        elif pose=="spin":
            box=actor.getchannel("A").getbbox()
            turning=actor.crop(box)
            width=max(20,round(turning.width*abs(math.cos(t*TAU))))
            turning=turning.resize((width,turning.height),Image.Resampling.BICUBIC)
            if .25<t<.75: turning=turning.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            actor=Image.new("RGBA",SIZE)
            actor.alpha_composite(turning,((640-width)//2,348-turning.height))
        else:
            actor=actor.resize((576,396),Image.Resampling.LANCZOS)
            fitted=Image.new("RGBA",SIZE)
            fitted.alpha_composite(actor,(32,-1))
            actor=fitted
        image.alpha_composite(actor)
        draw_prop(image,prop,t,behind=False)
        return image
