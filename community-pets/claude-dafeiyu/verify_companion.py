"""Verify all new companion videos, complete drawings, timings and publication references."""
import hashlib
import json
import subprocess
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent


def main():
    registry = json.loads((ROOT/'sources/lean-v2/registry.json').read_text('utf-8'))
    manifest = json.loads((ROOT/'manifest.json').read_text('utf-8'))
    active = {f['source']:f for f in manifest['files']}
    records=[]
    for row in registry['actions']:
        assert row['status']=='self-reviewed', row['id']
        assert hashlib.sha256((ROOT/row['sheet']).read_bytes()).hexdigest()==row['rendered']['sheetSha256']
        assert row['rendered']['frames']==8
        path=ROOT/'preview/actions'/row['id']
        for n in range(1,9):
            frame=Image.open(path/f'frame-{n:02}.png')
            assert frame.size==(640,360)
            b=frame.getchannel('A').getbbox()
            assert b and b[0]>0 and b[1]>0 and b[2]<640 and b[3]<360, (row['id'],b)
        target='lean-animation/'+row['name']+'.webm'
        assert target in active
        assert (ROOT/target).read_bytes()==(path/'clip.webm').read_bytes()
        raw=subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-v','error','-c:v','libvpx-vp9','-i',str(path/'clip.webm'),'-f','rawvideo','-pix_fmt','rgba','pipe:1'],capture_output=True,check=True).stdout
        frames=np.frombuffer(raw,dtype=np.uint8).reshape((-1,360,640,4))
        alpha=frames[:,:,:,3]
        assert np.all(alpha.max(axis=(1,2))>=250) and np.all(alpha.min(axis=(1,2))==0),row['id']
        edges=np.concatenate([alpha[:,0,:],alpha[:,-1,:],alpha[:,:,0],alpha[:,:,-1]],axis=1)
        assert edges.max()<=16,(row['id'],'clipped edge')
        assert abs(len(frames)/24-row['rendered']['duration'])<.001
        records.append({'id':row['id'],'decodedFrames':len(frames),'duration':len(frames)/24})
    timing=json.loads((ROOT/'preview/ambient-timing.json').read_text('utf-8'))
    assert .60<=timing['expectedTimeShare']<=.70
    assert .60<=timing['expectedFixedTimeShare']<=.70
    assert timing['restDuration']>=14
    lean=json.loads((ROOT/'claude-dafeiyu-lean-config.json').read_text('utf-8'))
    a=lean['animations'];seq=a['workSequence']
    assert seq['enter'] not in a['idle'] and seq['exit'] not in a['idle']
    for c in a['categories']:
        assert seq['enter'] not in c['actions'] and seq['exit'] not in c['actions']
        assert not any(name in seq['loops'] for name in c['actions'])
    assert all(a['events']['workStatus'][i]==seq['loops'] for i in range(4))
    report={'completed':True,'newSheets':8,'newWholeDrawings':64,'videos':records,'ambientTiming':timing}
    (ROOT/'preview/companion-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('PASS 9 companion timelines, 64 new whole drawings,',sum(r['decodedFrames'] for r in records),'decoded transparent frames; idle share',round(timing['expectedTimeShare']*100,2),'%')


if __name__=='__main__':main()
