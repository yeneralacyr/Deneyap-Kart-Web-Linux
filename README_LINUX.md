# Deneyap Kart Web Agent — Linux portu

Windows orijinali: `../Deneyap-Kart-Web/` (arduino-cli.exe + Inno Setup).
Bu klasor ayni protokolu (ws://localhost:49182 + 49183) Linux'ta calistirir.
Test edildi: antiX/Debian.

## Hizli baslangic (Debian/Ubuntu/antiX)

```bash
sudo apt install -y python3-venv python3-pip python3-tk python3-serial xdg-utils curl
curl -fsSL https://downloads.arduino.cc/arduino-cli/arduino-cli_0.35.3_Linux_64bit.tar.gz -o /tmp/arduino-cli.tgz
sudo tar xzf /tmp/arduino-cli.tgz -C /usr/local/bin arduino-cli
python3 -m venv venv && ./venv/bin/pip install -r requirements.txt
./venv/bin/python main.py --no-tray
# tarayicida deneyap blok sayfasini ac
```

Bayraklar:
- `--no-tray` : system tray'i kapat (Wayland/traysiz masaustuler icin)
- `--no-setup`: arduino core kurulumunu atla

Env:
- `DENEYAP_ARDUINO_CLI=/ozel/yol/arduino-cli` ile farkli binary kullanilabilir.

## Windows'tan farklar

- `os.startfile()` -> `xdg-open` (`open_path()`), `main.py`
- Tum `\` path birlestirmeler `os.path.join` oldu (`config.py`, `main.py`, `utils.py`)
- `arduino-cli` cozumu: env -> PATH -> `./arduino-cli` -> `./bin/arduino-cli` (`utils.get_arduino_cli()`)
- Tray opsiyonel: pystray/AppIndicator yoksa headless devam eder
- `iconbitmap(.ico)` try/except icinde (Linux'ta patlamaz)
- Seri monitor DTR/RTS secimi fqbn'e gore duzeltildi (orijinalde Board objesi string ile karsilastiriliyordu)
- `Board.uploadCode/compileCode` runtime `Data.config["TEMP_PATH"]` kullaniyor, port/path quote'laniyor
- Paketleme: `build_linux.py` (PyInstaller) + `deneyap-web.desktop` + `99-deneyap.rules`
- `script.iss` / `arduino-cli.exe` / `build.py` bu klasorde YOK (bilerek cikarildi)

## Dogrulama

```bash
./venv/bin/python -m py_compile *.py
```

## Notlar

- Seri port izni: kullanici `dialout` grubunda olmali + `99-deneyap.rules` udev kurali.
- Otomatik baslatma: `deneyap-web.desktop` dosyasini `~/.config/autostart/` altina kopyalayin.
