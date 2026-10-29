"""验证发布清单、引用和实际 WebM 解码后的透明通道；不访问 DSH。"""
import hashlib
import json
import subprocess
import re
from pathlib import Path

import imageio_ffmpeg
from PIL import Image

ROOT = Path(__file__).resolve().parent


def main():
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    config=json.loads((ROOT/'claude-dafeiyu-config.json').read_text(encoding='utf-8'))
    moves=config['animations']['moves']
    move_names={m['name']:{**moves['default'],**m.get('params',{})} for m in moves['actions']}
    videos = 0
    for entry in manifest["files"]:
        path = ROOT / entry["source"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == entry["sha256"], path
        if path.suffix != ".webm":
            continue
        info = subprocess.run([ffmpeg, "-hide_banner", "-i", str(path)], capture_output=True).stderr.decode(errors="replace")
        assert "640x360" in info and "24 fps" in info, (path, info)
        if path.stem in move_names:
            match=re.search(r'Duration: (\d+):(\d+):([\d.]+)',info)
            assert match, path
            duration=int(match[1])*3600+int(match[2])*60+float(match[3])
            params=move_names[path.stem]
            assert duration-params['leadSec']-params['tailSec']>=3.9, (path,duration)
        decoded = subprocess.run([ffmpeg, "-v", "error", "-c:v", "libvpx-vp9", "-i", str(path),
                                  "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgba", "pipe:1"],
                                 capture_output=True, check=True).stdout
        frame = Image.frombytes("RGBA", (640, 360), decoded)
        assert frame.getchannel("A").getextrema() == (0, 255), path
        assert frame.getchannel("A").getbbox(), path
        videos += 1
    print(f"PASS {len(manifest['files'])} SHA256 checks; {videos} VP9 videos decoded at 640x360/24fps with real alpha.")


if __name__ == "__main__":
    main()
