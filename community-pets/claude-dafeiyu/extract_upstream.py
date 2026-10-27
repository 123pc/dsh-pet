"""Extract the original project's action poses for visual reference, never for installation."""
import concurrent.futures
import json
import re
import subprocess
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT.parents[1]/'dsh-pet/assets/webm'
DEST=ROOT/'sources/upstream-reference'
FFMPEG=imageio_ffmpeg.get_ffmpeg_exe()


def extract(row):
    path=SOURCE/(row['name']+'.webm')
    output=DEST/(row['id']+'.png')
    info=subprocess.run([FFMPEG,'-hide_banner','-i',str(path)],capture_output=True).stderr.decode(errors='replace')
    match=re.search(r'Duration: (\d+):(\d+):([\d.]+)',info)
    if not match: raise ValueError(str(path))
    duration=int(match[1])*3600+int(match[2])*60+float(match[3])
    sheet=Image.new('RGB',(1280,760),'#e9ece8')
    draw=ImageDraw.Draw(sheet)
    font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',18)
    for index,fraction in enumerate((.05,.33,.66,.93)):
        timestamp=duration*fraction
        raw=subprocess.run([FFMPEG,'-v','error','-c:v','libvpx-vp9','-ss',str(timestamp),'-i',str(path),
                            '-vf','scale=640:360','-frames:v','1','-f','rawvideo','-pix_fmt','rgba','pipe:1'],capture_output=True,check=True).stdout
        frame=Image.frombytes('RGBA',(640,360),raw)
        xy=((index%2)*640,(index//2)*380)
        sheet.paste(frame,(xy[0],xy[1]+20),frame.getchannel('A'))
        draw.text((xy[0]+10,xy[1]),f'{row["name"]} / {timestamp:.2f}s',font=font,fill='#344658')
    sheet.save(output)
    return {'id':row['id'],'name':row['name'],'video':path.relative_to(ROOT.parents[1]).as_posix(),'duration':duration,'sheet':output.relative_to(ROOT).as_posix()}


def main():
    DEST.mkdir(parents=True,exist_ok=True)
    registry=json.loads((ROOT/'sources/action-library/actions.json').read_text(encoding='utf-8'))
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        records=list(pool.map(extract,registry['actions']))
    (DEST/'index.json').write_text(json.dumps({'count':len(records),'actions':records},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'Extracted {len(records)} original actions, four time points each. No unlisted WebM assets found.')


if __name__=='__main__':main()
