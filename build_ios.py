"""Build the iPhone home-screen version of the game into ios/.

aura-farm.html stays the single source (it is also what the artifact publishes);
this wraps it in a full document with iPhone meta tags, a manifest and icons.

Usage: python3 build_ios.py [path/to/boss-photo.png]
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "aura-farm.html"
OUT = ROOT / "ios"
APP_NAME = "Додеп"
BACKGROUND = "#3A1C6B"
ICON_SIZES = (180, 512)

HEAD = f"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no, viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="{APP_NAME}">
<meta name="theme-color" content="{BACKGROUND}">
<title>{APP_NAME}</title>
<link rel="manifest" href="manifest.webmanifest">
<link rel="apple-touch-icon" href="icon-180.png">
<style>
  /* Full-screen app shell: no rubber-band scroll, no text selection or tap flashes,
     content kept clear of the notch and the home indicator. */
  html, body {{ height: 100%; margin: 0; overscroll-behavior: none; }}
  body {{
    position: fixed;
    inset: 0;
    box-sizing: border-box;
    padding-top: env(safe-area-inset-top, 0px);
    padding-bottom: env(safe-area-inset-bottom, 0px);
    -webkit-user-select: none;
    user-select: none;
    -webkit-touch-callout: none;
    -webkit-tap-highlight-color: transparent;
    -webkit-text-size-adjust: 100%;
  }}
</style>
</head>
<body>
"""

TAIL = "\n</body>\n</html>\n"


def strip_artifact_head(game_html: str) -> str:
    """Drop the lines that only make sense inside the artifact viewer."""
    skip = ("<title>", '<meta name="claude:viewport-fit-sides"')
    return "\n".join(line for line in game_html.splitlines() if not line.startswith(skip))


def sips(*args: str) -> str:
    return subprocess.run(["sips", *args], check=True, capture_output=True, text=True).stdout


def make_icons(photo: Path) -> None:
    if not photo.exists():
        sys.exit(f"Icon photo not found: {photo}")
    if not shutil.which("sips"):
        sys.exit("sips (macOS) is needed to make the icons")
    for size in ICON_SIZES:
        target = str(OUT / f"icon-{size}.png")
        sips("-s", "format", "png", str(photo), "--out", target)
        width = int(sips("-g", "pixelWidth", target).split()[-1])
        height = int(sips("-g", "pixelHeight", target).split()[-1])
        side = min(width, height)
        sips("-c", str(side), str(side), target)
        sips("-z", str(size), str(size), target)


def write_manifest() -> None:
    manifest = {
        "name": APP_NAME,
        "short_name": APP_NAME,
        "lang": "ru",
        "start_url": "./",
        "display": "standalone",
        "orientation": "portrait",
        "background_color": BACKGROUND,
        "theme_color": BACKGROUND,
        "icons": [{"src": f"icon-{size}.png", "sizes": f"{size}x{size}", "type": "image/png"} for size in ICON_SIZES],
    }
    (OUT / "manifest.webmanifest").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    if not SOURCE.exists():
        sys.exit(f"Game file not found: {SOURCE}")
    OUT.mkdir(exist_ok=True)
    game = strip_artifact_head(SOURCE.read_text(encoding="utf-8"))
    (OUT / "index.html").write_text(HEAD + game + TAIL, encoding="utf-8")
    write_manifest()
    if len(sys.argv) > 1:
        make_icons(Path(sys.argv[1]))
    elif not (OUT / "icon-180.png").exists():
        print("No icon yet: pass a square-ish photo, e.g. python3 build_ios.py boss.png")
    print(f"Built {OUT / 'index.html'}")


if __name__ == "__main__":
    main()
