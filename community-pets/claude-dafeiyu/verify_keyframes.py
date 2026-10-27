"""Technical checks for a draft; this does not judge anatomy or animation quality."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--revision', choices=('v4', 'v5'), default='v5')
    args = parser.parse_args()
    source = ROOT / 'sources' / ('keyframes-' + args.revision) / 'walk'
    preview = ROOT / 'preview' / ('keyframes-' + args.revision)
    spec = json.loads((source / 'frames.json').read_text(encoding='utf-8'))
    hashes = {}
    bounds = []
    for i, row in enumerate(spec['frames']):
        path = source / row['file']
        hashes[row['file']] = hashlib.sha256(path.read_bytes()).hexdigest()
        frame = Image.open(preview / f'frame-{i+1:02}.png').convert('RGBA')
        assert frame.size == (640, 360)
        alpha = frame.getchannel('A')
        assert alpha.getextrema()[0] == 0 and alpha.getextrema()[1] > 240
        box = alpha.getbbox()
        assert box and box[0] > 0 and box[1] > 0 and box[2] < 640 and box[3] < 360
        bounds.append(box)
    assert len(set(hashes.values())) == len(spec['frames']), 'Duplicate source drawings'
    video = preview / 'walk-cycle.webm'
    raw = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-v', 'error', '-c:v', 'libvpx-vp9',
                          '-i', str(video), '-f', 'rawvideo', '-pix_fmt', 'rgba', 'pipe:1'],
                         capture_output=True, check=True).stdout
    decoded = np.frombuffer(raw, dtype=np.uint8).reshape((-1, 360, 640, 4))
    expected = len(spec['frames']) * (24 // spec['fps']) * 4
    assert len(decoded) == expected, (len(decoded), expected)
    for frame in decoded:
        assert frame[:, :, 3].min() == 0 and frame[:, :, 3].max() > 240
    report = {'revision': args.revision, 'visualApproval': spec['visualApproval'],
              'technicalChecksOnly': True, 'sourceDrawings': len(hashes), 'sourceSha256': hashes,
              'renderedBounds': bounds, 'decodedFrames': len(decoded), 'encodingFps': 24,
              'realAlphaOnEveryFrame': True, 'draftInstalled': False}
    (preview / 'technical-checks.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(f"PASS: {len(hashes)} distinct whole drawings; {len(decoded)} decoded frames, real alpha and no clipping. Visual approval: {spec['visualApproval']}.")


if __name__ == '__main__':
    main()
