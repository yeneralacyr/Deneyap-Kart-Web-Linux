#!/usr/bin/env python3
"""Linux build script (Windows'taki build.py + script.iss yerine).

Kullanim:
    python build_linux.py
    # veya tek dosya: python build_linux.py --onefile

Cikti: dist/deneyap-web-agent/
PyInstaller yoksa once: pip install pyinstaller
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

ONEFILE = "--onefile" in sys.argv

if (HERE / "build").exists() or (HERE / "dist").exists():
    print("Eski build/dist var, siliniyor...")
    shutil.rmtree(HERE / "build", ignore_errors=True)
    shutil.rmtree(HERE / "dist", ignore_errors=True)

cmd = [
    sys.executable, "-m", "PyInstaller",
    "--noconsole",
    "--name", "deneyap-web-agent",
]
if (HERE / "icon.ico").exists():
    cmd += ["--icon", str(HERE / "icon.ico")]
# proje ici arduino-cli varsa pakete gom
for extra in ("arduino-cli", "bin/arduino-cli"):
    p = HERE / extra
    if p.exists():
        cmd += ["--add-binary", f"{p}:."]
        break
if not ONEFILE:
    cmd += ["--onedir"]
cmd += [str(HERE / "main.py")]

print("Calistiriliyor:", " ".join(cmd))
r = subprocess.run(cmd, cwd=str(HERE))
if r.returncode != 0:
    sys.exit(r.returncode)

# ikonu dist'e kopyala (tray fallback icin)
for out in ((HERE / "dist" / "deneyap-web-agent"), (HERE / "dist",)):
    try:
        if out.exists() and (HERE / "icon.ico").exists():
            shutil.copy(HERE / "icon.ico", out / "icon.ico")
    except Exception:
        pass

print("OK -> dist/deneyap-web-agent/")
print("Otomatik baslatma icin: cp deneyap-web.desktop ~/.config/autostart/")
