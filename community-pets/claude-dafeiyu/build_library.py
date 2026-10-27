"""Build only reviewed complete-character animations into the installable community pack."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

from PIL import Image

from action_frames import render_drawings, timing, sample_timeline, save_previews
from build_keyframes import encode, write_json
from catalogue import read_upstream

ROOT=Path(__file__).resolve().parent
REGISTRY=ROOT/'sources/action-library/actions.json'
READY={'self-reviewed','user-approved'}
VERSION='0.6.0-companion'


def load_registry():return json.loads(REGISTRY.read_text(encoding='utf-8'))


def render_action(row):
    source=ROOT/row['sheet']
    settings={'height':{'rice':280,'sleep':240}.get(row['id'],320),**row.get('settings',{})}
    row['settings']=settings
    frames=render_drawings(source,settings)
    sequence,holds=timing(row)
    timeline=sample_timeline(frames,sequence,holds)
    preview=ROOT/'preview/actions'/row['id']
    save_previews(frames,timeline,preview)
    encode(timeline,preview/'clip.webm',fps=24)
    row['rendered']={'preview':f'actions/{row["id"]}/clip.webm','gif':f'actions/{row["id"]}/clip.gif',
                     'contact':f'actions/{row["id"]}/contact.png','frames':len(frames),
                     'duration':len(timeline)/24,'sheetSha256':hashlib.sha256(source.read_bytes()).hexdigest()}
    write_json(preview/'frames.json',{'name':row['name'],'status':row['status'],
        'fps':24,'sequence':sequence,'holds':holds,'frames':[f'frame-{i+1:02}.png' for i in range(len(frames))]})
    print('Rendered',row['id'],row['name'],len(frames),'complete drawings',flush=True)


def build_walk(registry):
    if registry['walk']['status']!='user-approved':raise ValueError('Walking has not been approved')
    provenance=json.loads((ROOT/'sources/keyframes-v5/provenance.json').read_text(encoding='utf-8'))
    for row in provenance['finalFrames']:
        path=ROOT/'sources/keyframes-v5/walk'/row['file']
        if hashlib.sha256(path.read_bytes()).hexdigest()!=row['sha256']:raise ValueError('Approved walk drawing changed: '+str(path))
    spec=json.loads((ROOT/registry['walk']['source']).read_text(encoding='utf-8'))
    frames=[]
    for row in spec['frames']:
        original=Image.open(ROOT/'sources/keyframes-v5/walk'/row['file']).convert('RGBA')
        sprite=original.resize((round(original.width*row['scale']),round(original.height*row['scale'])),Image.Resampling.LANCZOS)
        frame=Image.new('RGBA',(640,360));frame.alpha_composite(sprite,tuple(row['offset']));frames.append(frame)
    # Preserve the approved walk drawing/timing: .5s lead, four one-second cycles, .5s tail.
    timeline=[frames[0]]*12+[f for _ in range(4) for f in frames for _ in range(3)]+[frames[-1]]*12
    target=ROOT/'animation/自然走路.webm'
    archive_previous(target)
    encode(timeline,target,fps=24)
    return target


def archive_previous(path):
    archive=ROOT/'sources/rejected-v0.3/media'/path.name
    if path.exists() and not archive.exists():
        archive.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,archive)


def referenced_names(a):
    names=set(a['idle']+a['turn']+a['drag']+a['clicks'])
    names.update(m['name'] for m in a['moves']['actions'])
    for category in a['categories']:names.update(category['actions'])
    for event in a['events'].values():
        for value in event:
            names.update(value if isinstance(value,list) else [value])
    return names


def write_index(registry,extras=None):
    ready=[r for r in registry['actions'] if r['status'] in READY]
    items=[{'id':'walk','name':'自然走路','group':'moves','status':'user-approved',
            'preview':'../animation/自然走路.webm','contact':'keyframes-v5/contact.png',
            'gif':'keyframes-v5/walk-cycle.gif','reference':None,'frames':8}]
    for row in registry['actions']:
        item={key:row[key] for key in ('id','name','group','status')}
        item.update(row.get('rendered',{}));item['reference']='../sources/upstream-reference/'+row['id']+'.png'
        items.append(item)
    if extras:items.extend(extras)
    elif (ROOT/'preview/companion-index.json').exists():items.extend(json.loads((ROOT/'preview/companion-index.json').read_text(encoding='utf-8')))
    write_json(ROOT/'preview/actions-index.json',{'upstreamTotal':106,'reviewed':len(ready),
               'pending':106-len(ready),'userApproved':['自然走路'],'actions':items})


def pack(registry):
    build_walk(registry)
    reviewed=[row for row in registry['actions'] if row['status'] in READY]
    names={row['name'] for row in reviewed}
    for row in reviewed:
        preview=ROOT/'preview/actions'/row['id']/'clip.webm'
        digest=hashlib.sha256((ROOT/row['sheet']).read_bytes()).hexdigest()
        if not preview.exists() or digest!=row.get('rendered',{}).get('sheetSha256'):
            raise ValueError('Reviewed source/render is missing or changed: '+row['id'])
        target=ROOT/'animation'/(row['name']+'.webm');archive_previous(target);shutil.copyfile(preview,target)
    upstream=read_upstream()['animations']
    config_path=ROOT/'claude-dafeiyu-config.json'
    standing=json.loads(config_path.read_text(encoding='utf-8'))
    a={slot:[name for name in upstream[slot] if name in names] or [fallback]
       for slot,fallback in (('idle','reviewIdle'),('turn','reviewTurn'),('drag','reviewDrag'),('clicks','reviewClick'))}
    a['moves']={'default':{'minDist':320,'maxDist':440,'margin':20,'leadSec':.5,'tailSec':.5},
                'actions':[{'name':'自然走路'}]+[
                    {**item,'params':{**item.get('params',{}),'leadSec':.5,'tailSec':.5}}
                    for item in upstream['moves']['actions'] if item['name'] in names]}
    a['categories']=[]
    for category in upstream['categories']:
        available=[name for name in category['actions'] if name in names]
        if available:a['categories'].append({**category,'actions':available})
    a['events']={key:[name if name in names else 'reviewEvent' for name in values] for key,values in upstream['events'].items()}
    standing['animations']=a
    standing['animationWeights']={'idle':10,'turn':5 if a['turn']!=['reviewTurn'] else 0,'move':5} if a['categories'] else {'idle':90,'turn':5 if a['turn']!=['reviewTurn'] else 0,'move':5 if a['turn']!=['reviewTurn'] else 10}
    extras=[]
    from build_companion import REGISTRY as COMPANION_REGISTRY, install_assets, standing_rest
    if COMPANION_REGISTRY.exists():
        companion=json.loads(COMPANION_REGISTRY.read_text(encoding='utf-8'))
        install_assets(companion)
        extras.append(standing_rest(standing,upstream,registry))
        extras.extend({'id':row['id'],'name':row['name'],'group':'lean','status':row['status'],
                       **row['rendered'],'reference':None} for row in companion['actions'])
        write_json(ROOT/'preview/companion-index.json',extras)
    write_json(config_path,standing)
    files=[]
    for stem,folder in (('claude-dafeiyu','animation'),('claude-dafeiyu-lean','lean-animation')):
        path=ROOT/(stem+'-config.json')
        config=json.loads(path.read_text(encoding='utf-8'))
        sources=[path]+[ROOT/folder/(name+'.webm') for name in sorted(referenced_names(config['animations']))]
        for source in sources:
            if not source.exists():raise ValueError('Missing active media: '+str(source))
            target=source.name if source.suffix=='.json' else stem+'-animation/'+source.name
            files.append({'source':source.relative_to(ROOT).as_posix(),'target':target,'sha256':hashlib.sha256(source.read_bytes()).hexdigest()})
    write_json(ROOT/'manifest.json',{'version':VERSION,'files':files})
    previous=json.loads((ROOT/'sources/review-status.json').read_text(encoding='utf-8'))
    previous.update({'version':VERSION,'visualApproval':'partial' if len(reviewed)<106 else 'self-reviewed-library',
        'approvedActions':['自然走路'],'selfReviewedActions':[row['name'] for row in reviewed],
        'installMode':'reviewed-whole-character-keyframes','draftsInstalled':False,
        'remainingUpstreamActions':106-len(reviewed)})
    write_json(ROOT/'sources/review-status.json',previous)
    write_index(registry,extras)
    print(f'Pack {VERSION}: approved walking + {len(reviewed)}/106 reviewed actions; {len(files)} install files.',flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--render',nargs='*')
    parser.add_argument('--accept',nargs='+',help='Record a completed visual review; does not mean user approval')
    parser.add_argument('--note',help='Concrete findings from visual review')
    parser.add_argument('--pack',action='store_true')
    args=parser.parse_args();registry=load_registry()
    if args.render is not None:
        for row in registry['actions']:
            if (not args.render or row['id'] in args.render) and (ROOT/row['sheet']).exists():render_action(row)
        write_json(REGISTRY,registry)
    if args.accept:
        if not args.note:raise ValueError('A concrete visual review note is required')
        found=set()
        for row in registry['actions']:
            if row['id'] in args.accept:
                if not row.get('rendered'):raise ValueError('Render before visual review: '+row['id'])
                row['status']='self-reviewed';row['review']={'by':'codex-visual-review','note':args.note};found.add(row['id'])
                metadata=ROOT/'preview/actions'/row['id']/'frames.json'
                spec=json.loads(metadata.read_text(encoding='utf-8'))
                spec.update({'status':row['status'],'review':row['review']});write_json(metadata,spec)
        if found!=set(args.accept):raise ValueError('Unknown action id')
        write_json(REGISTRY,registry)
    if args.pack or (args.render is None and not args.accept):pack(registry)
    else:write_index(registry)


if __name__=='__main__':main()
