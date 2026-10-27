"""Build quiet companionship and laptop sequences from complete imagegen drawings."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

from PIL import Image
from action_frames import render_drawings, sample_timeline, save_previews
from build_keyframes import encode, write_json

ROOT = Path(__file__).resolve().parent
REGISTRY = ROOT / 'sources/lean-v2/registry.json'


def initialize():
    requests = json.loads((ROOT / 'sources/lean-v2/requests.json').read_text(encoding='utf-8'))
    rows = []
    for row in requests['actions']:
        ident = row['id']
        revision = ROOT / f'sources/lean-v2/{ident}-v2.png'
        rows.append({'id': ident, 'name': row['name'], 'sheet': revision.relative_to(ROOT).as_posix()
                     if revision.exists() else f'sources/lean-v2/{ident}.png',
                     'settings': {'cols': 4, 'rows': 2, 'height': 290, 'baseline':325,
                                  'verticalOffsets': ([0,18,0,0,0,0,0,0] if ident=='laptop-open' else
                                                      [0,0,0,0,8,20,0,0] if ident=='laptop-close' else [0]*8)}, 'status': 'pending'})
    rows.insert(0, {'id': 'lean-rest', 'name': '托腮·安静陪伴',
                   'sheet': 'sources/lean-v2/lean-tail.png',
                   'settings': {'cols': 4, 'rows': 2, 'height': 290, 'baseline':325}, 'status': 'pending'})
    write_json(REGISTRY, {'mode': 'builtin-imagegen', 'actions': rows})


def timeline_spec(ident):
    if ident == 'lean-rest':
        return [0, 4, 0, 4, 0], [3, .125, 4, .125, 6.75]
    if ident == 'lean-tail':
        return list(range(8)), [1, .375, .5, .375, .125, .5, .375, .75]
    if ident in ('laptop-open', 'laptop-close'):
        return list(range(8)), [.5, .375, .375, .5, .375, .375, .375, .625]
    if ident == 'laptop-type':
        return list(range(8)) * 3, [.625, .25, .25, .25, .125, .25, .25, .5] * 3
    if ident == 'laptop-think':
        return list(range(8)), [.75, .375, .5, 1.5, 1, .75, .375, .75]
    return list(range(8)), [.75, .375, .5, .625, .625, .5, .375, .75]


def render(registry):
    for row in registry['actions']:
        source = ROOT / row['sheet']
        frames = render_drawings(source, row['settings'])
        sequence, holds = timeline_spec(row['id'])
        timeline = sample_timeline(frames, sequence, holds)
        path = ROOT / 'preview/actions' / row['id']
        save_previews(frames, timeline, path)
        encode(timeline, path / 'clip.webm', fps=24)
        row['rendered'] = {'preview': f'actions/{row["id"]}/clip.webm',
                           'gif': f'actions/{row["id"]}/clip.gif',
                           'contact': f'actions/{row["id"]}/contact.png',
                           'frames': len(frames), 'duration': len(timeline) / 24,
                           'sheetSha256': hashlib.sha256(source.read_bytes()).hexdigest()}
        write_json(path / 'frames.json', {'name': row['name'], 'sequence': sequence, 'holds': holds,
                   'status': row['status'], 'frames': [f'frame-{i+1:02}.png' for i in range(len(frames))]})
        print('Rendered companion', row['id'], row['rendered']['duration'], flush=True)
    write_json(REGISTRY, registry)


def install_assets(registry):
    """Prepare package files; deployment is still handled by the existing installer."""
    for row in registry['actions']:
        if row['status'] != 'self-reviewed':
            raise ValueError('Companion artwork has not been reviewed: ' + row['id'])
        if hashlib.sha256((ROOT / row['sheet']).read_bytes()).hexdigest() != row['rendered']['sheetSha256']:
            raise ValueError('Companion source changed: ' + row['id'])
        shutil.copyfile(ROOT / 'preview' / row['rendered']['preview'], ROOT / 'lean-animation' / (row['name'] + '.webm'))
    names = {r['id']: r['name'] for r in registry['actions']}
    response = '托腮·轻声回应'
    shutil.copyfile(ROOT / 'lean-animation' / (names['lean-hum'] + '.webm'), ROOT / 'lean-animation' / (response + '.webm'))
    path = ROOT / 'claude-dafeiyu-lean-config.json'
    config = json.loads(path.read_text(encoding='utf-8'))
    loops = [names[i] for i in ('laptop-type', 'laptop-think', 'laptop-stretch')]
    config['animations'] = {
        'idle': [names['lean-rest']], 'turn': [names['lean-hum']],
        'drag': [names['lean-tail']], 'clicks': [names['lean-hair'], names['lean-hum']],
        'moves': {'default': {'leadSec': .5, 'tailSec': .5, 'minDist': 140, 'maxDist': 260, 'margin': 20}, 'actions': []},
        'categories': [{'id': '托腮小动作', 'weight': 100, 'actions': [names[i] for i in ('lean-tail', 'lean-hair', 'lean-hum')]}],
        'events': {'balance': [response] * 6, 'whisper': [response],
                   'workStatus': [loops, loops, loops, loops, response, response],
                   'workTransition': [names['laptop-open'], names['laptop-close']]},
        'workSequence': {'enter': names['laptop-open'], 'loops': loops, 'exit': names['laptop-close']}}
    # 14 seconds of quiet company, with occasional 4–5 second small gestures.
    config['animationWeights'] = {'idle': 45, 'turn': 0, 'move': 0}
    write_json(path, config)


def standing_rest(standing, upstream, registry):
    """Calibrate time share using durations, rather than treating 65% of draws as 65% of time."""
    frames = [Image.open(ROOT / f'preview/actions/idle/frame-{i:02}.png').convert('RGBA') for i in range(1, 5)]
    timeline = sample_timeline(frames, [0, 1, 2, 1, 3, 0] * 4, [1.5, .125, .125, .125, .625, 1.5] * 4)
    name = '安静站立·眨眼呼吸'
    dest = ROOT / 'preview/actions/standing-rest'
    save_previews(frames, timeline, dest)
    encode(timeline, dest / 'clip.webm', fps=24)
    shutil.copyfile(dest / 'clip.webm', ROOT / 'animation' / (name + '.webm'))
    standing['animations']['idle'] = [name]
    # Preserve the original short idle in the optional activity menu/pool.
    standing['animations']['categories'].append({'id': '日常短待机', 'weight': 2, 'actions': upstream['idle']})
    durations = {r['name']: r['rendered']['duration'] for r in registry['actions']}
    durations['自然走路'] = 5
    a = standing['animations']
    def mean(names): return sum(durations[n] for n in names) / len(names)
    mean_action = sum(c['weight'] * mean(c['actions']) for c in a['categories']) / sum(c['weight'] for c in a['categories'])
    mean_turn = mean(a['turn'])
    mean_move = mean([r['name'] for r in a['moves']['actions']])
    duration = len(timeline) / 24
    share, turn, move = .65, .03, .04
    probability = share * (turn * mean_turn + move * mean_move + (1-turn-move) * mean_action) / (duration * (1-share) + share * mean_action)
    standing['animationWeights'] = {'idle': round(probability * 100, 2), 'turn': 3, 'move': 4}
    def actual(fixed=False):
        p = standing['animationWeights']['idle'] / 100
        t, m = (0, 0) if fixed else (turn, move)
        return p * duration / (p * duration + t * mean_turn + m * mean_move + (1-p-t-m) * mean_action)
    write_json(ROOT / 'preview/ambient-timing.json', {'targetTimeShare': share, 'restDuration': duration,
               'weights': standing['animationWeights'], 'meanOtherActionDuration': mean_action,
               'expectedTimeShare': actual(), 'expectedFixedTimeShare': actual(True),
               'scope': 'Uninterrupted autonomous animation; explicit work, clicks and other events take priority.'})
    row = {'id': 'standing-rest', 'name': name, 'group': 'quiet', 'status': 'self-reviewed',
           'preview': 'actions/standing-rest/clip.webm', 'gif': 'actions/standing-rest/clip.gif',
           'contact': 'actions/standing-rest/contact.png', 'frames': 4, 'duration': duration,
           'sheetSha256': hashlib.sha256(b''.join(f.tobytes() for f in frames)).hexdigest(), 'reference': None}
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--init', action='store_true')
    parser.add_argument('--render', action='store_true')
    args = parser.parse_args()
    if args.init: initialize()
    if args.render: render(json.loads(REGISTRY.read_text(encoding='utf-8')))


if __name__ == '__main__': main()
