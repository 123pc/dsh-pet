"""从透明动作表构建社区角色包；只写包目录，不安装或修改 DSH profile。"""
import argparse
import hashlib
import json
import shutil
import subprocess
from collections import deque
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent
SIZE = (640, 360)
VERSION = "0.2.0"


def isolate_cell(cell):
    """切格时只保留角色连通区域，避免相邻格的零散像素进入当前帧。"""
    alpha = cell.getchannel("A")
    width, height = cell.size
    mask = bytearray(alpha.point(lambda a: 255 if a > 8 else 0).tobytes())
    largest = []
    for seed in range(len(mask)):
        if not mask[seed]:
            continue
        queue = deque([seed])
        component = []
        mask[seed] = 0
        while queue:
            i = queue.popleft()
            component.append(i)
            x, y = i % width, i // width
            for j in (i - 1 if x else -1, i + 1 if x + 1 < width else -1,
                      i - width if y else -1, i + width if y + 1 < height else -1):
                if j >= 0 and mask[j]:
                    mask[j] = 0
                    queue.append(j)
        if len(component) > len(largest):
            largest = component
    retained = bytearray(width * height)
    original = alpha.tobytes()
    for i in largest:
        retained[i] = original[i]
    cell.putalpha(Image.frombytes("L", cell.size, bytes(retained)))
    return cell


def split_sheet(path):
    """按 4×2 切帧；所有帧使用同一缩放比，保留绘制出的相对大小。"""
    sheet = Image.open(path).convert("RGBA")
    frames = []
    for row in range(2):
        for col in range(4):
            cell = sheet.crop((round(col * sheet.width / 4), round(row * sheet.height / 2),
                               round((col + 1) * sheet.width / 4), round((row + 1) * sheet.height / 2)))
            if cell.getchannel("A").getextrema()[0] == 255:
                raise ValueError(f"动作表缺少透明通道：{path}")
            cell = isolate_cell(cell)
            bbox = cell.getchannel("A").point(lambda a: 255 if a > 24 else 0).getbbox()
            if not bbox:
                raise ValueError(f"动作表中有空帧：{path}")
            frames.append(cell.crop(bbox))
    scale = min(320 / max(f.height for f in frames), 570 / max(f.width for f in frames))
    output = []
    for frame in frames:
        sprite = frame.resize((round(frame.width * scale), round(frame.height * scale)), Image.Resampling.LANCZOS)
        canvas = Image.new("RGBA", SIZE)
        canvas.alpha_composite(sprite, ((SIZE[0] - sprite.width) // 2, 348 - sprite.height))
        output.append(canvas)
    return output


def encode(frames, path, ffmpeg, fps=8, repeats=1):
    """将绘制的关键帧重复采样为 24fps，保留 VP9 alpha，禁止跨姿势淡化。"""
    # 关键帧直接保持三帧，避免 Image.blend 造成四肢重影。
    args = [ffmpeg, "-y", "-v", "error", "-f", "rawvideo", "-pixel_format", "rgba",
            "-video_size", "640x360", "-framerate", "24", "-i", "pipe:0", "-an",
            "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-auto-alt-ref", "0",
            "-b:v", "0", "-crf", "26", str(path)]
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = b"".join(f.tobytes() * (24 // fps) for f in frames) * repeats
    subprocess.run(args, input=payload, check=True)


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ffmpeg", help="ffmpeg 可执行文件；未指定时使用 PATH 或 imageio-ffmpeg")
    args = parser.parse_args()
    ffmpeg = args.ffmpeg or shutil.which("ffmpeg")
    if not ffmpeg:
        import imageio_ffmpeg
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

    standing = json.loads((ROOT / "claude-dafeiyu-config.json").read_text(encoding="utf-8"))
    frames_by_name = {name: split_sheet(ROOT / "sources" / f"{name}-sheet.png") for name in ("lean", "walk", "wave")}
    for name, frames in frames_by_name.items():
        filename = {"lean": "lean", "walk": "walk", "wave": "click"}[name]
        encode(frames, ROOT / "animation" / f"{filename}.webm", ffmpeg, repeats=2 if name == "walk" else 1)
    encode(frames_by_name["lean"], ROOT / "animation" / "leanSway.webm", ffmpeg, fps=6, repeats=2)
    # 事件池与随机池必须使用不同名称，否则 onEnded 会把普通 idle 当作事件动画循环。
    shutil.copyfile(ROOT / "animation" / "idle.webm", ROOT / "animation" / "eventIdle.webm")
    shutil.copyfile(ROOT / "animation" / "idle.webm", ROOT / "animation" / "turn.webm")
    standing["animations"]["turn"] = ["turn"]
    standing["animations"]["events"] = {"balance": ["eventIdle"], "whisper": ["eventIdle"], "workStatus": ["eventIdle"] * 6}
    write_json(ROOT / "claude-dafeiyu-config.json", standing)

    lean = json.loads(json.dumps(standing))
    lean["pets"] = [{**standing["pets"][0], "id": "claude-dafeiyu-lean", "name": "Claude·托腮",
                     "fixedEnabled": True, "display": "none"}]
    lean["animations"] = {
        "idle": ["lean"], "turn": ["turn"], "drag": ["drag"], "clicks": ["click"],
        "moves": {"default": standing["animations"]["moves"]["default"], "actions": [{"name": "leanSway"}]},
        "categories": [{"id": "托腮", "weight": 80, "actions": ["lean", "leanSway"], "noMirror": True}],
        "events": {"balance": ["eventIdle"], "whisper": ["eventIdle"], "workStatus": ["eventIdle"] * 6},
    }
    lean["animationWeights"] = {"idle": 20, "turn": 0, "move": 0}
    write_json(ROOT / "claude-dafeiyu-lean-config.json", lean)
    lean_dir = ROOT / "lean-animation"
    lean_dir.mkdir(exist_ok=True)
    for name in ("lean", "leanSway"):
        shutil.copyfile(ROOT / "animation" / f"{name}.webm", lean_dir / f"{name}.webm")
    shutil.copyfile(ROOT / "animation" / "lean.webm", lean_dir / "eventIdle.webm")
    for alias, source in (("turn", "lean"), ("drag", "lean"), ("click", "leanSway")):
        shutil.copyfile(lean_dir / f"{source}.webm", lean_dir / f"{alias}.webm")

    preview = ROOT / "preview"
    preview.mkdir(exist_ok=True)
    for name, frames in frames_by_name.items():
        rendered = []
        for frame in frames:
            bg = Image.new("RGB", SIZE, "#e8e9e5")
            bg.paste(frame, mask=frame.getchannel("A"))
            rendered.append(bg)
        rendered[0].save(preview / f"{name}.gif", save_all=True, append_images=rendered[1:], duration=125, loop=0)
    contact = Image.new("RGB", (640, 360), "#e8e9e5")
    for i, frame in enumerate(frames_by_name["lean"]):
        thumb = frame.resize((160, 90), Image.Resampling.LANCZOS)
        contact.paste(thumb, ((i % 4) * 160, (i // 4) * 180 + 55), thumb)
    contact.save(preview / "lean-contact.png")

    files = []
    for config, directory, target in (("claude-dafeiyu", "animation", "claude-dafeiyu-animation"),
                                      ("claude-dafeiyu-lean", "lean-animation", "claude-dafeiyu-lean-animation")):
        for source in [ROOT / f"{config}-config.json", *sorted((ROOT / directory).glob("*.webm"))]:
            dest = source.name if source.suffix == ".json" else f"{target}/{source.name}"
            files.append({"source": source.relative_to(ROOT).as_posix(), "target": dest,
                          "sha256": hashlib.sha256(source.read_bytes()).hexdigest()})
    write_json(ROOT / "manifest.json", {"version": VERSION, "files": files})
    print(f"Built {VERSION}: {len(files)} files; installation is a separate step.")


if __name__ == "__main__":
    from build_library import main as reviewed_build
    reviewed_build()
