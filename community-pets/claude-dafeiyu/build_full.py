"""构建完整上游动作覆盖与可移动步态；构建不触碰已安装的 DSH。"""
import argparse
import hashlib
import json
import shutil
import subprocess
import time
from pathlib import Path
from PIL import Image, ImageDraw
from build import write_json, ROOT, SIZE
from catalogue import catalogue, write_catalogue
from puppet import Puppet
from props import font

VERSION="0.3.0"
FPS=24
KEY_FPS=12


def encode_frames(frames,path,ffmpeg):
    args=[ffmpeg,"-y","-v","error","-f","rawvideo","-pixel_format","rgba","-video_size","640x360",
          "-framerate","24","-i","pipe:0","-an","-c:v","libvpx-vp9","-pix_fmt","yuva420p",
          "-auto-alt-ref","0","-b:v","0","-crf","29","-deadline","good","-cpu-used","3",str(path)]
    payload=b"".join(frame.tobytes()*2 for frame in frames)
    subprocess.run(args,input=payload,check=True)


def contact(puppet,rows):
    examples=["待机呼吸休闲","超大伸懒腰","吃白饭","写代码","小提琴演奏","工作状态-雀跃庆祝",
              "玩水枪","荡秋千","吃西瓜","舞狮头","原地小憩沉眠","三球抛接"]
    preview=ROOT/"preview"
    preview.mkdir(exist_ok=True)
    sheet=Image.new("RGB",(1280,660),"#edf0f0")
    d=ImageDraw.Draw(sheet)
    for i,name in enumerate(examples):
        spec=next(r for r in rows if r["name"]==name)
        frame=puppet.render(spec["pose"],spec["prop"],.38)
        frame=frame.resize((320,180),Image.Resampling.LANCZOS)
        x=(i%4)*320; y=(i//4)*220
        sheet.paste(frame,(x,y+15),frame)
        d.text((x+160,y+204),name,font=font(16),fill="#33415f",anchor="mm")
    sheet.save(preview/"full-contact.png")
    walk_frames=[]
    for i in range(60):
        frame=puppet.walk(i/12)
        bg=Image.new("RGB",SIZE,"#e8e9e5")
        # 预览位移，视频素材仍保持原地；位移仅由宿主负责。
        x=round(130-260*max(0,min(1,(i/12-.5)/4)))
        bg.paste(frame,(x,0),frame)
        walk_frames.append(bg)
    walk_frames[0].save(preview/"walk-moving.gif",save_all=True,append_images=walk_frames[1:],duration=83,loop=0)


def configure(upstream):
    standing=json.loads((ROOT/"claude-dafeiyu-config.json").read_text(encoding="utf-8"))
    standing["animations"]=json.loads(json.dumps(upstream["animations"]))
    standing["animations"]["moves"]={
        "default":{"minDist":140,"maxDist":260,"margin":20,"leadSec":.5,"tailSec":.5},
        "actions":[{"name":"自然走路"},{"name":"螃蟹走路","params":{"minDist":80,"maxDist":150}},
                   {"name":"原地漂浮踏步","params":{"minDist":60,"maxDist":125}},
                   {"name":"原地左转奔跑","params":{"minDist":220,"maxDist":360}}]}
    standing["animationWeights"]=upstream["animationWeights"]
    standing["workStatusTexts"]=[
        ["工牌戴好了，让我想想。","大肥鱼正在深度思考…"],
        ["Claude 工装开工啦。","敲敲键盘，继续干活。"],
        ["这一页归档好了。","检查结果，接着来。"],
        ["这里等你点个头。","轮到你决定啦。"],
        ["搞定！奖励一碗白饭。","下班下班，摸鱼去。"],
        ["卡了一下，先看看原因。","工牌没掉，问题再找找。"]]
    standing["whisperPrompt"]="你是戴着Claude工牌的DeepSeek大肥鱼，蓝发鲸耳，穿奶油白卫衣。慵懒、爱干饭、偶尔吐槽但会认真陪用户工作。自然地说一句二十字以内的话，不解释系统或模型。"
    write_json(ROOT/"claude-dafeiyu-config.json",standing)
    lean=json.loads((ROOT/"claude-dafeiyu-lean-config.json").read_text(encoding="utf-8"))
    lean["workStatusTexts"]=standing["workStatusTexts"]
    lean["whisperPrompt"]=standing["whisperPrompt"]
    # 托腮仍是固定姿态；完整动作与漫游由站立形态承担。
    write_json(ROOT/"claude-dafeiyu-lean-config.json",lean)
    files=[]
    for config,directory,target in (("claude-dafeiyu","animation","claude-dafeiyu-animation"),
                                    ("claude-dafeiyu-lean","lean-animation","claude-dafeiyu-lean-animation")):
        for source in [ROOT/(config+"-config.json"),*sorted((ROOT/directory).glob("*.webm"))]:
            dest=source.name if source.suffix==".json" else target+"/"+source.name
            files.append({"source":source.relative_to(ROOT).as_posix(),"target":dest,
                          "sha256":hashlib.sha256(source.read_bytes()).hexdigest()})
    write_json(ROOT/"manifest.json",{"version":VERSION,"files":files})


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contact-only",action="store_true")
    parser.add_argument("--only",nargs="*",help="只重建选中的动作（仍检查完整清单）")
    parser.add_argument("--resume",action="store_true",help="跳过已经构建的中文动作文件")
    args=parser.parse_args()
    upstream,rows=catalogue()
    write_catalogue()
    puppet=Puppet()
    for row in rows: puppet.render(row["pose"],row["prop"],.4)
    contact(puppet,rows)
    if args.contact_only: return
    import imageio_ffmpeg
    ffmpeg=imageio_ffmpeg.get_ffmpeg_exe()
    all_rows=[{"name":"自然走路","group":"moves","pose":"walk","prop":"none","duration":5,"technique":"two-joint-IK"},*rows]
    started=time.monotonic()
    for index,row in enumerate(all_rows):
        if args.only and row["name"] not in args.only: continue
        if args.resume and (ROOT/"animation"/(row["name"]+".webm")).exists(): continue
        n=KEY_FPS*row["duration"]
        if row["pose"]=="walk" or row["pose"]=="run":
            frames=[puppet.walk(i/KEY_FPS,row["pose"]=="run") for i in range(n)]
        else:
            frames=[puppet.render(row["pose"],row["prop"],i/n) for i in range(n)]
        path=ROOT/"animation"/(row["name"]+".webm")
        encode_frames(frames,path,ffmpeg)
        print(f"[{index+1}/{len(all_rows)}] {row['name']} ({time.monotonic()-started:.1f}s)",flush=True)
    # 保留旧预览引用的英文素材名；动作接口与移动池使用中文语义名称。
    shutil.copyfile(ROOT/"animation"/"自然走路.webm",ROOT/"animation"/"walk.webm")
    configure(upstream)
    print("Built",VERSION,flush=True)


if __name__=="__main__":
    raise SystemExit("WITHDRAWN: layered-puppet v0.3 failed visual review. Use build.py for whole-character keyframe drafts.")
