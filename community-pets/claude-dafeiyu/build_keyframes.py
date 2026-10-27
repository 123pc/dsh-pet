"""Build whole-character drafts; the installable pack stays static until visual approval.

No rig, limb compositing, mesh deformation, optical flow, blending or invented props.
Only whole-image placement/resampling and video encoding are allowed here.
"""
import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
SIZE = (640, 360)
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
VERSION = "0.4.0-review"


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    # Match Git's LF policy so cloning the pack preserves manifest hashes on every OS.
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def encode(frames, path, fps=8, repeats=1):
    assert 24 % fps == 0
    path.parent.mkdir(parents=True, exist_ok=True)
    args = [FFMPEG, "-y", "-v", "error", "-f", "rawvideo", "-pixel_format", "rgba",
            "-video_size", "640x360", "-framerate", "24", "-i", "pipe:0", "-an",
            "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-auto-alt-ref", "0",
            "-b:v", "0", "-crf", "22", str(path)]
    subprocess.run(args, input=b"".join(f.tobytes() * (24 // fps) for f in frames) * repeats, check=True)


def freeze_pack():
    """Withdraw the rejected rig from every active trigger, retaining files for audit."""
    registry=ROOT/'sources/action-library/actions.json'
    if registry.exists() and json.loads(registry.read_text(encoding='utf-8')).get('walk',{}).get('status')=='user-approved':
        raise RuntimeError('Walking is user-approved. Use build.py --pack; the old static-withdrawal entry is retired.')
    archive = ROOT / "sources" / "rejected-v0.3"
    archive.mkdir(parents=True, exist_ok=True)
    files = []
    for stem, folder, source in (("claude-dafeiyu", "animation", "idle"),
                                  ("claude-dafeiyu-lean", "lean-animation", "lean")):
        config_path = ROOT / (stem + "-config.json")
        config = json.loads(config_path.read_text(encoding="utf-8"))
        saved = archive / config_path.name
        if not saved.exists():
            shutil.copyfile(config_path, saved)
        # Reuse one existing WHOLE illustration, not the rejected puppet.
        raw = subprocess.run([FFMPEG, "-v", "error", "-c:v", "libvpx-vp9", "-i",
                              str(ROOT / folder / (source + ".webm")), "-frames:v", "1",
                              "-f", "rawvideo", "-pix_fmt", "rgba", "pipe:1"],
                             capture_output=True, check=True).stdout
        still = Image.frombytes("RGBA", SIZE, raw)
        neutral = ROOT / folder / "reviewIdle.webm"
        encode([still] * 16, neutral)
        for name in ("reviewTurn", "reviewDrag", "reviewClick", "reviewEvent"):
            shutil.copyfile(neutral, ROOT / folder / (name + ".webm"))
        config["animations"] = {
            "idle": ["reviewIdle"], "turn": ["reviewTurn"],
            "drag": ["reviewDrag"], "clicks": ["reviewClick"],
            "moves": {"default": {"leadSec": .5, "tailSec": .5, "minDist": 140, "maxDist": 260, "margin": 20}, "actions": []},
            "categories": [],
            "events": {"balance": ["reviewEvent"] * 6, "whisper": ["reviewEvent"], "workStatus": ["reviewEvent"] * 6},
        }
        config["animationWeights"] = {"idle": 100, "turn": 0, "move": 0}
        write_json(config_path, config)
        for path in [config_path, *sorted((ROOT / folder).glob("review*.webm"))]:
            dest = path.name if path.suffix == ".json" else stem + "-animation/" + path.name
            files.append({"source": path.relative_to(ROOT).as_posix(), "target": dest,
                          "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    write_json(ROOT / "manifest.json", {"version": VERSION, "files": files})
    write_json(ROOT / "sources" / "review-status.json", {
        "version": VERSION, "visualApproval": "pending", "approvedActions": [],
        "withdrawn": {"version": "0.3.0", "actions": 107, "reason": "Unnatural layered-puppet animation; rejected by user."},
        "installMode": "static-whole-illustrations", "draftsInstalled": False,
        "remainingUpstreamActions": 106,
        "drafts": {"v4": {"visualApproval": "rejected", "reason": "Arm swing too small and unnatural."},
                   "v5": {"visualApproval": "pending", "focus": "Full forward/back arm swing and natural passing poses."}},
    })
    print("Withdrawn 107 rig actions. Pack contains static whole illustrations only; draft videos excluded.")


def build_draft(revision="v5"):
    draft = ROOT / "sources" / ("keyframes-" + revision) / "walk"
    spec = json.loads((draft / "frames.json").read_text(encoding="utf-8"))
    frames = []
    for item in spec["frames"]:
        src = Image.open(draft / item["file"]).convert("RGBA")
        assert src.getchannel("A").getextrema()[0] == 0, item["file"]
        # Registration acts on each complete illustration. Never crop limbs or redraw content.
        scale = item["scale"]
        image = src.resize((round(src.width * scale), round(src.height * scale)), Image.Resampling.LANCZOS)
        canvas = Image.new("RGBA", SIZE)
        canvas.alpha_composite(image, tuple(item["offset"]))
        frames.append(canvas)
    preview = ROOT / "preview" / ("keyframes-" + revision)
    preview.mkdir(parents=True, exist_ok=True)
    for i, frame in enumerate(frames):
        frame.save(preview / f"frame-{i+1:02}.png")
    encode(frames, preview / "walk-cycle.webm", fps=spec["fps"], repeats=4)
    backgrounds = []
    for frame in frames:
        bg = Image.new("RGB", SIZE, "#e9ece8")
        bg.paste(frame, mask=frame.getchannel("A"))
        backgrounds.append(bg)
    backgrounds[0].save(preview / "walk-cycle.gif", save_all=True, append_images=backgrounds[1:],
                        duration=1000 // spec["fps"], loop=0)
    cols = 4
    contact = Image.new("RGB", (cols * 320, ((len(frames) + cols - 1) // cols) * 440), "#e9ece8")
    draw = ImageDraw.Draw(contact)
    font_path = Path("C:/Windows/Fonts/msyh.ttc")
    font = ImageFont.truetype(str(font_path), 17) if font_path.exists() else ImageFont.load_default()
    bounds = [f.getchannel("A").getbbox() for f in frames]
    crop = (min(b[0] for b in bounds)-3, min(b[1] for b in bounds)-3,
            max(b[2] for b in bounds)+3, max(b[3] for b in bounds)+3)
    for i, frame in enumerate(frames):
        thumb = frame.crop(crop)
        thumb.thumbnail((300, 400), Image.Resampling.LANCZOS)
        xy = ((i % cols) * 320, (i // cols) * 440)
        contact.paste(thumb, (xy[0] + (320-thumb.width)//2, xy[1] + 35), thumb.getchannel("A"))
        draw.text((xy[0] + 12, xy[1] + 8), f'{i+1:02} / {spec["frames"][i]["phase"]}', fill="#344658", font=font)
    contact.save(preview / "contact.png")
    write_json(preview / "frames.json", {"fps": spec["fps"], "status": spec.get("visualApproval", "pending"),
                                          "frames": [{"file": f"frame-{i+1:02}.png", "phase": f["phase"]} for i, f in enumerate(spec["frames"])]})
    print(f"Built whole-character draft: {len(frames)} drawings at {spec['fps']}fps. Not installed.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--draft-only", action="store_true")
    parser.add_argument("--withdraw-only", action="store_true")
    parser.add_argument("--revision", choices=("v4", "v5"), default="v5")
    args = parser.parse_args()
    if not args.draft_only:
        freeze_pack()
    if not args.withdraw_only:
        build_draft(args.revision)


if __name__ == "__main__":
    main()
