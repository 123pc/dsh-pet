"""Check whole-character keyframes and every decoded output frame, independently of packing."""
import hashlib
import json
import subprocess
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parent


def main():
    registry=json.loads((ROOT/'sources/action-library/actions.json').read_text(encoding='utf-8'))
    assert len(registry['actions'])==106
    assert len({r['name'] for r in registry['actions']})==106
    upstream=json.loads((ROOT/'sources/upstream-reference/index.json').read_text(encoding='utf-8'))
    assert upstream['count']==106
    assert {a['name'] for a in upstream['actions']}=={a['name'] for a in registry['actions']}
    ffmpeg=imageio_ffmpeg.get_ffmpeg_exe()
    videos=0;drawings=0;decoded_count=0;records=[]
    for row in registry['actions']:
        if row['status'] not in {'self-reviewed','user-approved'}:continue
        directory=ROOT/'preview/actions'/row['id']
        spec=json.loads((directory/'frames.json').read_text(encoding='utf-8'))
        assert len(spec['frames'])==row['frameCount']==row['rendered']['frames'],row['id']
        assert set(spec['sequence'])==set(range(row['frameCount'])),row['id']
        assert len(spec['sequence'])==len(spec['holds'])
        assert hashlib.sha256((ROOT/row['sheet']).read_bytes()).hexdigest()==row['rendered']['sheetSha256']
        hashes=set()
        for filename in spec['frames']:
            frame=Image.open(directory/filename).convert('RGBA')
            assert frame.size==(640,360)
            box=frame.getchannel('A').getbbox()
            assert box and box[0]>0 and box[1]>0 and box[2]<640 and box[3]<360,(row['id'],filename,box)
            hashes.add(hashlib.sha256(frame.tobytes()).hexdigest())
        assert len(hashes)==row['frameCount'],('Repeated whole drawing',row['id'])
        raw=subprocess.run([ffmpeg,'-v','error','-c:v','libvpx-vp9','-i',str(directory/'clip.webm'),
                            '-f','rawvideo','-pix_fmt','rgba','pipe:1'],capture_output=True,check=True).stdout
        assert len(raw)%(640*360*4)==0,row['id']
        pixels=np.frombuffer(raw,dtype=np.uint8).reshape((-1,360,640,4))
        alpha=pixels[:,:,:,3]
        assert np.all(alpha.max(axis=(1,2))==255),('Empty/partial frame',row['id'])
        assert np.all(alpha.min(axis=(1,2))==0),('Opaque frame',row['id'])
        border=np.concatenate((alpha[:,0,:],alpha[:,-1,:],alpha[:,:,0],alpha[:,:,-1]),axis=1)
        assert border.max()<=16,('Encoded border clipping',row['id'],int(border.max()))
        assert abs(len(pixels)/24-row['rendered']['duration'])<.001,row['id']
        drawings+=len(hashes);decoded_count+=len(pixels);videos+=1
        records.append({'id':row['id'],'name':row['name'],'drawings':len(hashes),'decodedFrames':len(pixels),'alpha':True,'unclipped':True})
    report={'reviewedActions':videos,'wholeDrawings':drawings,'decodedFrames':decoded_count,'results':records}
    (ROOT/'preview/library-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'PASS {videos} reviewed actions, {drawings} distinct whole drawings, {decoded_count} decoded frames: alpha and bounds checked.')


if __name__=='__main__':main()
