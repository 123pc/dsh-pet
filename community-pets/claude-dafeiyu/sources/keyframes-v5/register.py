"""Register COMPLETE drawings by the orange hair clip, never by changing anatomy."""
import json
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent
ORDER = [('A', '近侧脚落地'), ('E', '落地缓冲'), ('B', '近侧脚支撑'), ('F', '远侧脚向前摆'),
         ('C', '远侧脚落地'), ('G', '换脚缓冲'), ('D', '远侧脚支撑'), ('H', '近侧脚向前摆')]


def anchor(path):
    a = np.asarray(Image.open(path).convert('RGBA'))
    rgb = a[200:390, 280:510, :3].astype(float)
    mask = (rgb[:, :, 0] > 190) & (rgb[:, :, 1] > 90) & (rgb[:, :, 1] < 210) & (rgb[:, :, 2] < 165)
    yy, xx = np.where(mask)
    if len(xx) < 300:
        raise ValueError('Hair clip anchor missing: ' + str(path))
    return (float(xx.mean() + 280), float(yy.mean() + 200))


def main():
    target = anchor(ROOT / 'walk/A.png')
    rows = []
    for key, phase in ORDER:
        source = ROOT / 'walk' / (key + '.png')
        pt = anchor(source)
        scale = .21
        offset = [round(212 + (target[0] - pt[0]) * scale), round(28 + (target[1] - pt[1]) * scale)]
        rows.append({'file': key + '.png', 'phase': phase, 'scale': scale, 'offset': offset,
                     'anchor': list(pt), 'wholeImageOnly': True})
    spec = {'fps': 8, 'visualApproval': 'user-approved', 'approval': {'date': '2026-10-27', 'quote': '走路动作没问题了，继续去做其它剩余的动作'}, 'method': 'whole-character-keyframes',
            'registration': 'translation of complete drawing; identical .21 scale for all frames', 'frames': rows}
    (ROOT / 'walk/frames.json').write_text(json.dumps(spec, indent=2) + '\n', encoding='utf-8')
    print('Registered whole drawings:', [(row['file'], row['offset']) for row in rows])


if __name__ == '__main__':
    main()
