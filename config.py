"""
Initial configuration for new downloads and updates (Linux port).

Windows orijinalindeki `f"{...}\..."` birlestirmeleri Linux'ta patliyordu,
burada tum path'ler os.path.join ile kuruluyor.
"""
import os
import appdirs

deneyapKart = "dydk_mpv10"
deneyapMini = "dym_mpv10"
deneyapKart1A = "dydk1a_mpv10"
deneyapKartG = "dyg_mpv10"
deneyapMiniv2 = "dym_mpv20"
deneyapKart1Av2 = "dydk1a_mpv20"

AGENT_VERSION = "1.0.2"
DENEYAP_VERSION = "1.3.12"

APP_NAME = "DeneyapKartWeb"
BASE_DIR = os.path.join(appdirs.user_data_dir(), APP_NAME)
TEMP_PATH = os.path.join(BASE_DIR, "Temp")
CONFIG_PATH = BASE_DIR
LOG_PATH = BASE_DIR
LIB_PATH = os.path.join(
    BASE_DIR, "packages", "deneyap", "hardware", "esp32",
    DENEYAP_VERSION, "libraries",
)

# arduino-cli cozumu: env -> PATH -> proje ici ./arduino-cli -> ./bin/arduino-cli
ARDUINO_CLI_ENV = "DENEYAP_ARDUINO_CLI"
