"""经宿主公开接口核实实际桌面走位和播放回执；结束后恢复位置并释放临时占用。"""
import argparse
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url',required=True,help='当前 DSH Web 地址，只接受本机 HTTP 服务')
    parser.add_argument('--pet',default='claude-dafeiyu')
    parser.add_argument('--actions',nargs='+',default=['吃白饭','写代码','小提琴演奏','舞狮头','余额-分文不剩','工作状态-雀跃庆祝'])
    parser.add_argument('--movement-actions',nargs='*',default=['自然走路'])
    parser.add_argument('--playback-timeout',type=int,default=6000)
    parser.add_argument('--report',type=Path,default=Path(__file__).resolve().parent/'preview/live-validation.json')
    args=parser.parse_args()
    if not 0<=args.playback_timeout<=10000:parser.error('playback-timeout must be 0..10000 ms (host API limit)')
    base=args.base_url.rstrip('/')
    parsed=urllib.parse.urlparse(base)
    if parsed.scheme!='http' or parsed.hostname not in {'127.0.0.1','localhost'}:
        raise ValueError('验证仅面向本机 DSH')
    prefix=base+'/dsh-pet-7340/'
    query='pet='+urllib.parse.quote(args.pet)+'&surface=desktop'

    def request(path,body=None):
        req=urllib.request.Request(prefix+path,data=None if body is None else json.dumps(body,ensure_ascii=False).encode(),
                                   headers={} if body is None else {'Content-Type':'application/json'})
        with urllib.request.urlopen(req,timeout=12) as response:
            value=json.loads(response.read())
        if value.get('ok') is False: raise RuntimeError(value.get('message') or str(value))
        return value

    initial=request('pose?'+query)
    lock=request('lock?'+query,{'ttl':60000})['lockId']
    scoped=query+'&lock='+urllib.parse.quote(lock)
    report={'pet':args.pet,'movement':[],'playbacks':[],'completed':False}
    try:
        request('position?'+scoped,{'x':.6,'y':initial['y'],'mode':'instant'})
        time.sleep(.7)
        moves=[(name,facing) for name in args.movement_actions for facing in (('left','right') if name=='自然走路' else ('left',))]
        for name,facing in moves:
            # Test each action from the same interior location. Chaining left
            # moves can reach a monitor edge, where the host correctly falls
            # back to playback without travelling.
            request('position?'+scoped,{'x':.6,'y':initial['y'],'mode':'instant'})
            # Pose publishing is asynchronous (roughly 400 ms); the position
            # command's HTTP acknowledgement is not a fresh geometry snapshot.
            deadline=time.monotonic()+4
            while True:
                start=request('pose?'+query)
                if abs(start['x']-.6)<.002:break
                if time.monotonic()>deadline:raise AssertionError(('Position acknowledgement timed out',start))
                time.sleep(.12)
            cue=request('anim?'+scoped,{'name':name,'facing':facing})
            samples=[]
            for _ in range(23):
                time.sleep(.25)
                pose=request('pose?'+query)
                samples.append({'x':pose['x'],'updatedAt':pose['updatedAt']})
            record=request('playback/'+cue['playbackId']+'?wait=ended,failed,cancelled&timeout=1000')
            end=request('pose?'+query)
            delta=end['x']-start['x']
            assert record['status']=='ended',record
            assert delta<-.01 if facing=='left' else delta>.01, (facing,delta,samples)
            assert len({p['x'] for p in samples})>5, '没有观测到连续位移'
            report['movement'].append({'name':name,'facing':facing,'startX':start['x'],'endX':end['x'],'deltaX':delta,'samples':samples,'status':record['status']})
            print('PASS actual desktop move',name,facing,round(delta,4),flush=True)
        for name in args.actions:
            cue=request('anim?'+scoped,{'name':name})
            record=request('playback/'+cue['playbackId']+'?wait=ended,failed,cancelled&timeout='+str(args.playback_timeout))
            assert record['status']=='ended',record
            report['playbacks'].append({'name':name,'status':record['status']})
            print('PASS desktop playback',name,flush=True)
        report['completed']=True
    finally:
        try:
            request('position?'+scoped,{'x':initial['x'],'y':initial['y'],'mode':'instant'})
        finally:
            try:
                request('lock/release?'+query,{'lockId':lock})
            finally:
                path=args.report
                path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
                print('Saved',path,flush=True)


if __name__=='__main__': main()
