"""Whole-character sheet extraction and registration; no anatomy or prop compositing."""
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

SIZE=(640,360)


def extract_drawings(path, cols=None, rows=None):
    """Find connected figures globally, preserving complete ahoges crossing nominal cell lines.

    Small detached props are assigned by their center to the same sheet cell. This is
    segmentation of complete illustrations, never assembly of limbs from different poses.
    """
    sheet=Image.open(path).convert('RGBA')
    if sheet.getchannel('A').getextrema()[0]!=0: raise ValueError(f'No alpha: {path}')
    w,h=sheet.size
    small=sheet.getchannel('A').resize((w//2,h//2),Image.Resampling.BILINEAR)
    sw,sh=small.size
    mask=bytearray((np.asarray(small)>32).astype(np.uint8).tobytes())
    components=[]
    membership=np.zeros((sh,sw),dtype=np.int32)
    for seed in np.flatnonzero(np.frombuffer(mask,dtype=np.uint8)):
        seed=int(seed)
        if not mask[seed]: continue
        queue=deque([seed]);mask[seed]=0
        count=0;sx=0;sy=0;left=sw;top=sh;right=0;bottom=0;pixels=[]
        while queue:
            i=queue.popleft();y,x=divmod(i,sw)
            count+=1;sx+=x;sy+=y
            pixels.append(i)
            left=min(left,x);top=min(top,y);right=max(right,x);bottom=max(bottom,y)
            for j in (i-1 if x else -1,i+1 if x+1<sw else -1,i-sw if y else -1,i+sw if y+1<sh else -1):
                if j>=0 and mask[j]: mask[j]=0;queue.append(j)
        if count<8: continue  # isolated export noise, not a meaningful drawing/prop
        area=(right-left+1)*(bottom-top+1)
        if ((bottom-top<=2 and right-left>sw*.1) or
                (right-left<=2 and bottom-top>sh*.1)):
            continue  # disconnected thin layout dividers, never anatomy or held props
        if (right-left>sw*.8 or bottom-top>sh*.8) and count/max(1,area)<.015:
            continue  # isolated sheet divider lines, never part of the character
        components.append((left*2,top*2,min(w,(right+1)*2),min(h,(bottom+1)*2),count,sx/count,sy/count,len(components)+1))
        membership.flat[pixels]=len(components)
    if cols is None or rows is None:
        main=sorted(components,key=lambda part:part[4],reverse=True)[:4]
        if len(main)<4:raise ValueError(f'Four separate figures required: {path}')
        cols,rows=(2,2) if max(p[6] for p in main)-min(p[6] for p in main)>sh*.28 else (4,1)
    regions=[[] for _ in range(cols*rows)]
    for part in components:
        col=min(cols-1,int(part[5]*cols/sw));row=min(rows-1,int(part[6]*rows/sh))
        regions[row*cols+col].append(part)
    drawings=[]
    for index,parts in enumerate(regions):
        if not parts or max(p[4] for p in parts)<1000: raise ValueError(f'Empty figure {index}: {path}')
        box=(max(0,min(p[0] for p in parts)-3),max(0,min(p[1] for p in parts)-3),
             min(w,max(p[2] for p in parts)+3),min(h,max(p[3] for p in parts)+3))
        # A bounding rectangle can overlap the neighbouring drawing on a tightly
        # spaced sheet. Keep only this figure's connected components, including
        # its own disconnected props; never import a neighbour's hair or tail.
        keep=np.isin(membership,[p[7] for p in parts]).astype(np.uint8)*255
        matte=Image.fromarray(keep).resize((w,h),Image.Resampling.NEAREST).filter(ImageFilter.MaxFilter(5))
        isolated=sheet.copy();isolated.putalpha(ImageChops.multiply(sheet.getchannel('A'),matte))
        drawings.append({'image':isolated.crop(box),'box':box,'cellCenterX':(index%cols+.5)*w/cols})
    return drawings


def render_drawings(path, settings=None):
    settings=settings or {}
    drawings=extract_drawings(path,settings.get('cols'),settings.get('rows'))
    max_height=max(d['image'].height for d in drawings)
    max_width=max(d['image'].width for d in drawings)
    scale=min(settings.get('height',320)/max_height,560/max_width)
    offsets=settings.get('verticalOffsets',[0]*len(drawings))
    frames=[]
    for i,item in enumerate(drawings):
        sprite=item['image'].resize((round(item['image'].width*scale),round(item['image'].height*scale)),Image.Resampling.LANCZOS)
        frame=Image.new('RGBA',SIZE)
        x=round(320+(item['box'][0]-item['cellCenterX'])*scale)
        y=round(settings.get('baseline',345)-sprite.height+offsets[i])
        frame.alpha_composite(sprite,(x,y))
        alpha=frame.getchannel('A');box=alpha.getbbox()
        if not box or box[0]<=0 or box[1]<=0 or box[2]>=640 or box[3]>=360: raise ValueError(f'Clipped render {path} frame {i}')
        frames.append(frame)
    return frames


def timing(row):
    settings=row.get('settings',{})
    if 'sequence' in settings:
        return settings['sequence'],settings['holds']
    ident=row['id']
    if ident=='idle':return [0,1,2,1,3,0],[1.5,.125,.125,.125,.625,1.5]
    if ident=='wave':return [0,1,2,3,2,3,1,0],[.25,.25,.375,.375,.375,.375,.25,.5]
    if ident=='rice':return [0,1,2,3,0,1,2,3],[.5,.375,.375,.75]*2
    if ident=='sleep':return [0,1,2,3,2,1,0],[.75,.625,.625,.75,.625,.625,.5]
    return [0,1,2,3],[.5,.625,.75,.625]


def sample_timeline(frames,sequence,holds):
    if len(sequence)!=len(holds): raise ValueError('Timing mismatch')
    output=[]
    for index,seconds in zip(sequence,holds):output.extend([frames[index]]*max(1,round(seconds*24)))
    return output


def save_previews(frames,timeline,path,labels=None):
    path=Path(path);path.mkdir(parents=True,exist_ok=True)
    for i,frame in enumerate(frames):frame.save(path/f'frame-{i+1:02}.png')
    bounds=[f.getchannel('A').getbbox() for f in frames]
    crop=(max(0,min(b[0] for b in bounds)-3),max(0,min(b[1] for b in bounds)-3),
          min(640,max(b[2] for b in bounds)+3),min(360,max(b[3] for b in bounds)+3))
    contact=Image.new('RGB',(4*300,390*((len(frames)+3)//4)),'#e9ece8');draw=ImageDraw.Draw(contact)
    font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',16)
    for i,frame in enumerate(frames):
        thumb=frame.crop(crop);thumb.thumbnail((280,345),Image.Resampling.LANCZOS)
        xy=((i%4)*300+(300-thumb.width)//2,(i//4)*390+35)
        contact.paste(thumb,xy,thumb.getchannel('A'))
        draw.text(((i%4)*300+12,(i//4)*390+8),str(i+1)+((' · '+labels[i]) if labels else ''),font=font,fill='#344658')
    contact.save(path/'contact.png')
    # Each PNG is held, never blended, so the animation has no ghost limbs.
    gif=[]
    for frame in timeline[::3]:
        bg=Image.new('RGB',SIZE,'#e9ece8');bg.paste(frame,mask=frame.getchannel('A'));gif.append(bg)
    gif[0].save(path/'clip.gif',save_all=True,append_images=gif[1:],duration=125,loop=0)
