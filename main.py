import asyncio

import websockets

import config
from utils import Data
from Websocket import Websocket
from SerialMonitorWebsocket import SerialMonitorWebsocket
from pathlib import Path
import multiprocessing
import logging
import threading
import _thread
import config as InitialConfig
from utils import createFolder, setupDeneyap
import os
import appdirs
import json
import sys
import subprocess
import platform
import argparse
from ErrorGUI import showError
import webbrowser


def open_path(path: str) -> None:
    """Windows'taki os.startfile() yerine Linux/macOS uyumlu acici."""
    try:
        if sys.platform.startswith("linux"):
            subprocess.Popen(["xdg-open", path])
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        elif hasattr(os, "startfile"):
            os.startfile(path)  # type: ignore[attr-defined]
        else:
            webbrowser.open(f"file://{path}")
    except Exception:
        logging.exception("open_path failed for %s", path)


def load_tray_modules():
    """pystray/Pillow yoksa veya tray calismazsa None don (traysiz moda dus)."""
    try:
        from pystray import MenuItem, Icon
        from PIL import Image
        return MenuItem, Icon, Image
    except Exception as e:
        logging.warning("Tray modules not available: %s", e)
        return None, None, None


def find_icon() -> "str | None":
    here = Path(__file__).resolve().parent
    for name in ("icon.png", "icon.ico", "icon.jpg"):
        p = here / name
        if p.exists():
            return str(p)
    return None

def sysIconThread() -> None:
    """
    Function for threading.
    Creates system tray gui. Linux'ta AppIndicator yoksa sessizce cikar.
    """
    MenuItem, Icon, Image = load_tray_modules()
    if MenuItem is None:
        logging.info("Tray disabled, running headless.")
        return

    def stop(icon_obj=None):
        logging.info("Exiting through icon")
        try:
            if icon_obj is not None:
                icon_obj.stop()
        finally:
            _thread.interrupt_main()

    menu = (MenuItem(f'Deneyap Kart Web Versiyonu: {Data.config["AGENT_VERSION"]}', lambda x: x, enabled=False),
            MenuItem(f'Deneyap Kütüphane Versiyonu: {Data.config["DENEYAP_VERSION"]}', lambda x: x, enabled=False),
            MenuItem('Siteye Git', goToWebsite),
            MenuItem('Kütüphanelere Git', goToLib),
            MenuItem('Log Dosyasını Aç', goToLogFile),
            MenuItem('Çıkış', stop), )
    icon_path = find_icon()
    try:
        image = Image.open(icon_path) if icon_path else Image.new("RGB", (64, 64), color=(20, 120, 200))
    except Exception as e:
        logging.warning("Icon load failed (%s), using fallback: %s", icon_path, e)
        image = Image.new("RGB", (64, 64), color=(20, 120, 200))
    icon = Icon("Deneyap Kart", image, "Deneyap Kart", menu)
    icon.run()

def goToWebsite() -> None:
    webbrowser.open("https://deneyapkart.org/deneyapkart/deneyapblok/")

def goToLib() -> None:
    open_path(Data.config['LIB_PATH'])

def goToLogFile():
    open_path(f"{Data.config['LOG_PATH']}")


def parse_args():
    p = argparse.ArgumentParser(description="Deneyap Kart Web Agent (Linux)")
    p.add_argument("--no-tray", action="store_true", help="system tray'i devre disi birak")
    p.add_argument("--no-setup", action="store_true", help="ilk kurulumu atla (config runSetup=false say)")
    return p.parse_args()


def main(loop, enable_tray: bool = True, skip_setup: bool = False) -> None:
    Data.config = createConfig()

    if skip_setup:
        Data.config["runSetup"] = False

    #Create system tray (opsiyonel; Artix/Wayland'da tray yoksa headless devam)
    if enable_tray:
        try:
            thread = threading.Thread(target=sysIconThread, daemon=True)
            thread.start()
        except Exception:
            logging.exception("Tray thread failed, continuing headless")
    else:
        logging.info("Tray disabled by flag")

    logFile = os.path.join(Data.config['LOG_PATH'], "deneyap.log")
    logging.basicConfig(handlers=[logging.FileHandler(filename=logFile, encoding='utf-8', mode='a+')], format='%(asctime)s-%(process)d-%(thread)d   %(levelno)d      %(message)s(%(funcName)s-%(lineno)d)', level=logging.INFO)
    logging.info(f"----------------------- Program Start Agent: v{Data.config['AGENT_VERSION']} Core: v{Data.config['DENEYAP_VERSION']}-----------------------")

    #Runs when first time installing or new version setup is run
    if Data.config['runSetup']:
        logging.info("Running Setup...")
        isSetupSuccess, message = setupDeneyap()
        if not isSetupSuccess:
            logging.critical("Setup exited with error. Exiting program")
            showError(f"Deneyap Kart kütüphaneleri indirilirken hata oluştu.\n\n{message}")
            return

    createFolder(Data.config["LOG_PATH"])
    createFolder(Data.config["TEMP_PATH"])


    try:
        #Websocket for normal communication between agent and front-end
        start_server = websockets.serve(Websocket, 'localhost', 49182)
        loop.run_until_complete(start_server)
        logging.info("Main Websocket is ready")

        #Websocket for serial monitor communication between agent and front-end
        #when serial monitor is constantly used without delay, it blocks normal communication which is more important
        start_serial_server = websockets.serve(SerialMonitorWebsocket, 'localhost', 49183)
        loop.run_until_complete(start_serial_server)
        logging.info("Serial Websocket is ready")

    except OSError:
        showError("Program Zaten Çalışıyor.")
        raise

    try:
        logging.info("Running Forever...")
        loop.run_forever()

    except Exception as e:
        logging.exception("InMain: ")
    finally:
        logging.info("Exiting Program")



def createConfig() -> dict:
    """
    Creates config file if newly installed. if it exist updates it and changes runSetup to true.

    :return: config file data, which will be passed to Data class
    :rtype: dict
    """

    Path(InitialConfig.LOG_PATH).mkdir(parents=True, exist_ok=True)

    config_json = os.path.join(InitialConfig.CONFIG_PATH, "config.json")
    isConfigExists = os.path.exists(config_json)
    configFileData = {
        "deneyapKart": "dydk_mpv10",
        "deneyapMini": "dym_mpv10",
        "deneyapKart1A": "dydk1a_mpv10",
        "deneyapKartG": "dyg_mpv10",
        "deneyapMiniv2": "dym_mpv20",
        "deneyapKart1Av2": "dydk1a_mpv20",

        "AGENT_VERSION": InitialConfig.AGENT_VERSION,
        "DENEYAP_VERSION": InitialConfig.DENEYAP_VERSION,

        "TEMP_PATH": InitialConfig.TEMP_PATH,
        "CONFIG_PATH": InitialConfig.CONFIG_PATH,
        "LOG_PATH": InitialConfig.LOG_PATH,
        "LIB_PATH": InitialConfig.LIB_PATH,

        "runSetup": True
    }

    if not isConfigExists:#if it is first install
        configFileDataString = json.dumps(configFileData)
        with open(os.path.join(configFileData['CONFIG_PATH'], "config.json"), "w") as configFile:
            configFile.write(configFileDataString)
    else:
        #loads old config file
        with open(os.path.join(configFileData['CONFIG_PATH'], "config.json"), "r") as configFile:
            configFileDataString = configFile.read()
            configFileDataOld = json.loads(configFileDataString)
            for k in configFileData.keys(): #checks if new key is added.
                if not k in configFileDataOld:
                    configFileDataOld[k] = configFileData[k]
                    if k == "AGENT_VERSION":
                        #some old version did not have old agent version, if left a sconfigFileDataOld[k] = configFileData[k]
                        #causes it to not understand version change so does not run setup
                        configFileDataOld[k] = "0.0.0"

            configFileData = configFileDataOld
            version = configFileData['AGENT_VERSION'] if "AGENT_VERSION" in configFileData else "0.0.0" #i don't know why i double checked it, leaving it just in case
            #updating config file for new version
            configFileData['DENEYAP_VERSION'] = configFileData['DENEYAP_VERSION'] if "DENEYAP_VERSION" in configFileData else InitialConfig.DENEYAP_VERSION
            configFileData['AGENT_VERSION'] = InitialConfig.AGENT_VERSION
            configFileData['LIB_PATH'] = configFileData['LIB_PATH'] if "LIB_PATH" in configFileData else InitialConfig.LIB_PATH


            if (version != InitialConfig.AGENT_VERSION): #if new version, runs setup and updates config file
                configFileData['runSetup'] = True
                configFileDataString = json.dumps(configFileData)
                with open(os.path.join(configFileData['CONFIG_PATH'], "config.json"), "w") as configFile:
                    configFile.write(configFileDataString)
    return configFileData


if __name__ == '__main__':

    multiprocessing.freeze_support() #need for pyinstaller

    args = parse_args()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        main(loop, enable_tray=(not args.no_tray), skip_setup=args.no_setup)
    except:
        logging.exception("Main Error: ")
    finally:
        for websocket in Data.websockets:
            websocket.closeSocket()
        loop.stop()

    sys.exit()
