import json
import os
import shlex
import shutil
import subprocess
import config as InitialConfig
from pathlib import Path
import logging
from DownloadGUI import startGUI
from multiprocessing import Process

ARDUINO_BOARD_URL = "https://raw.githubusercontent.com/deneyapkart/deneyapkart-arduino-core/master/package_deneyapkart_index.json"


def get_arduino_cli() -> str:
    """arduino-cli binary'sini coz: env -> PATH -> ./arduino-cli -> ./bin/arduino-cli."""
    env_path = os.environ.get(getattr(InitialConfig, "ARDUINO_CLI_ENV", "DENEYAP_ARDUINO_CLI"), "")
    if env_path:
        return env_path
    found = shutil.which("arduino-cli")
    if found:
        return found
    here = Path(__file__).resolve().parent
    for candidate in (here / "arduino-cli", here / "bin" / "arduino-cli"):
        if candidate.exists():
            return str(candidate)
    return "arduino-cli"


def _quote_cli_arg(value: str) -> str:
    return shlex.quote(value)

class Data:
    """
    keeps data on runtime
    """
    boards  = {}
    threads = []
    config = {}
    websockets = []
    processes = []

    @staticmethod
    def updateConfig():
        """
        update config files to make changes permenant.
        """
        logging.info("config file is changing, new file: %s", Data.config)
        configFileDataString = json.dumps(Data.config)
        with open(os.path.join(Data.config['CONFIG_PATH'], "config.json"), "w") as configFile:
            configFile.write(configFileDataString)
        logging.info("config file changed successfully.")

def executeCli(command:str) -> str:
    """
    runs command for arduino-cli, waits until arduino-cli returns then returns its output.

    :param command: command that will run, basicly executeCli("config init") --> runs "arduino-cli config init" on cmd
    :type command: str

    :return: output from arduino-cli, depended of command.
    :rtype: str
    """

    cli = get_arduino_cli()
    logging.info(f"Executing command {cli} {command}")
    returnString = subprocess.check_output(f"{cli} {command}", shell=True)
    return returnString.decode("utf-8")

def executeCliPipe(command:str) -> subprocess.Popen:
    """
    runs command for arduino-cli, does not wait for response instead returns subprocess.

    :param command: command that will run, basicly executeCliPipe("config init") --> runs "arduino-cli config init" on cmd
    :type command: str

    :return: subprocess of command that run for accessing output live.
    :rtype: subprocess.Popen
    """
    cli = get_arduino_cli()
    logging.info(f"Executing pipe command {cli} {command}")
    pipe = subprocess.Popen(f"{cli} {command}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return pipe


def executeCli2Pipe(command:str) -> subprocess.Popen:
    """
    runs command for arduino-cli, does not wait for response instead returns subprocess.

    :param command: command that will run, basicly executeCliPipe("config init") --> runs "arduino-cli config init" on cmd
    :type command: str

    :return: subprocess of command that run for accessing output and error live.
    :rtype: subprocess.Popen
    """
    cli = get_arduino_cli()
    logging.info(f"Executing pipe command {cli} {command}")
    pipe = subprocess.Popen(f"{cli} {command}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return pipe

def createFolder(fileDir:str) -> None:
    """
    creates new folder, if it exist does not do anything

    :param fileDir: directory and name of the folder that will be created
    :type fileDir: str
    """

    logging.info(f"Creating folder {fileDir}")
    Path(fileDir).mkdir(parents=True, exist_ok=True)

def createInoFile(code:str) -> None:
    """
    creates .ino file for arduino-cli to compile and upload code.

    :param code: code that will be written to file. send by front-end
    :type code: str
    """

    tempPath = Data.config["TEMP_PATH"]
    logging.info(f"Creating Ino file at {tempPath}")
    createFolder(tempPath)
    createFolder(os.path.join(tempPath, "tempCode"))
    with open(os.path.join(tempPath, "tempCode", "tempCode.ino"), "w", encoding="utf-8") as inoFile:
        inoFile.writelines(code)
        logging.info(f"File created")


def updateIndex() -> str:
    """
    updates arduino-cli index. in order to renew libraries

    :return: result of 'arduino-cli update' command
    :rtype: str
    """
    logging.info("updating index")
    pipe = executeCli2Pipe(f"update")
    return pipe.communicate()[1].decode("utf-8")

def downloadCore(version:str)->str:
    """
    :param version: version of deneyapkart core that will be downloaded.
    :type version: str

    :return: output of 'arduino-cli core install'
    :rtype: str
    """
    logging.info(f"installing deneyap:esp32@{version}")
    pipe = executeCli2Pipe(f"core install deneyap:esp32@{version}")
    return pipe.communicate()[1].decode("utf-8")

def setupDeneyap() -> (bool, str):
    """
    runs when program first downloaded or updated.
    configures deneyap kart to arduino-cli
    downloads some libraries

    :return: first element is whetever setup was success or not, second element is error message.
    :rtype: (bool, str)
    """

    process = Process(target=startGUI)
    process.start()

    try:
        executeCli("config init")
    except:
        logging.info(f"Init file does exist skipping this step")
    else:
        logging.info(f"Init file created")

    string = executeCli("config dump")
    if not ("deneyapkart" in string):
        logging.info("package_deneyapkart_index.json is not found on config, adding it")
        executeCli(f"config add board_manager.additional_urls {ARDUINO_BOARD_URL}")
        logging.info("added package_deneyapkart_index.json to config")
    if not ("DeneyapKartWeb" in string):
        logging.info("directories is not set, setting it.")
        data_dir = Data.config['CONFIG_PATH']
        staging_dir = os.path.join(Data.config['CONFIG_PATH'], "staging")
        user_dir = os.path.join(
            Data.config['CONFIG_PATH'], "packages", "deneyap",
            "hardware", "esp32", Data.config['DENEYAP_VERSION'],
            "ArduinoLibraries",
        )
        executeCli(f"config set directories.data {_quote_cli_arg(data_dir)}")
        executeCli(f"config set directories.downloads {_quote_cli_arg(staging_dir)}")
        executeCli(f"config set directories.user {_quote_cli_arg(user_dir)}")
        logging.info("directories are changed")
    else:
        logging.info("package_deneyapkart_index.json is found on config skipping this step")

    t = updateIndex()
    if t:
        logging.critical(t)
        process.terminate()
        return False,t

    t = downloadCore(Data.config['DENEYAP_VERSION'])
    if t:
        logging.critical(t)
        process.terminate()
        return False,t

    #TODO this part will be added as default to core + adafruit color thingy.
    pipe = executeCli2Pipe("lib install Stepper IRremote")
    t = pipe.communicate()[1].decode("utf-8")
    if t:
        logging.critical(t)
        process.terminate()
        return False,t

    Data.config['runSetup'] = False
    Data.config['AGENT_VERSION'] = InitialConfig.AGENT_VERSION
    configDataString = json.dumps(Data.config)
    with open(os.path.join(Data.config['CONFIG_PATH'], "config.json"), 'w') as configFile:
        logging.info(f"Config File Changed")
        configFile.write(configDataString)

    process.terminate()
    return True,1
