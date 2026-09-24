import asyncio
import json
import subprocess
import os
import config
from DeviceChecker import DeviceChecker
from utils import Data, downloadCore, updateIndex, terminatePipe
from Board import Board
from multiprocessing import Queue
import logging
from websockets.exceptions import ConnectionClosedOK, ConnectionClosed
import websockets
import websockets.legacy.server  # annotation icin yan yukleme (websockets.legacy)
from LibraryDownloader import searchLibrary, installLibrary

class aobject(object):
    """
    Inheriting this class allows you to define an async __init__.

    So you can create objects by doing something like `await MyClass(params)`

    credit:https://stackoverflow.com/questions/33128325/how-to-set-class-attribute-with-await-in-init
    """
    async def __new__(cls, *a, **kw):
        instance = super().__new__(cls)
        await instance.__init__(*a, **kw)
        return instance

    async def __init__(self):
        pass


class Websocket(aobject):
    """
    For main communication between front-end and agent, for every front-end connection, one object is created
    """

    async def __init__(self, websocket: websockets.legacy.server.WebSocketServerProtocol, path=None):
        """
        :param websocket: websocket connection to front-end
        :type websocket: websockets.legacy.server.WebSocketServerProtocol

        :param path: need for websockets library to work. not used in this project
        :type path: str
        """

        logging.info(f"Websocket object is created")
        Data.websockets.append(self)
        self.websocket = websocket
        self.queue = Queue()
        self.current_pipe = None  # suren derleme/yukleme; baglanti koparsa oldurulur

        self.deviceChecker = DeviceChecker(self.queue)
        self.deviceChecker.start()

        await self.mainLoop()

    async def _sendSafe(self, bodyToSend: str) -> bool:
        """Kapali sokete yazmayi denerse False don (baglanti kopmus)."""
        try:
            await self.websocket.send(bodyToSend)
            return True
        except ConnectionClosed:
            return False

    async def readAndSend(self, pipe: subprocess.Popen) -> None:
        """
        reads subporcess.Popen live and sends it to front-end to be written to console

        :param pipe: subprocess that will be readed. name is pipe, but its not pipe. my bad.
        :type pipe: subprocess.Popen
        """

        async def heartbeat():
            # uzun derlemelerde konsol sessiz kalmasin: kullanici "takildi" sanip
            # sayfayi yenilemesin diye periyodik canlilik mesaji gonder
            elapsed = 0
            try:
                while True:
                    await asyncio.sleep(20)
                    elapsed += 20
                    alive = {"command": "consoleLog",
                             "log": f"[agent] islem suruyor ({elapsed} sn)...\n"}
                    if not await self._sendSafe(json.dumps(alive)):
                        break
            except asyncio.CancelledError:
                pass

        hb = asyncio.ensure_future(heartbeat())
        try:
            allText = ""
            t = ""
            for c in iter(lambda: pipe.stdout.readline(), b''):
                t = c.decode("utf-8")
                allText += t
                bodyToSend = {"command": "consoleLog", "log": t}
                bodyToSend = json.dumps(bodyToSend)
                if not await self._sendSafe(bodyToSend):
                    return
                await asyncio.sleep(0)

            if pipe.communicate()[1]:
                t = pipe.communicate()[1].decode("utf-8")
                allText += t

            bodyToSend = {"command": "consoleLog", "log": t}
            bodyToSend = json.dumps(bodyToSend)
            logging.info(f"Pipe output {allText}")
            await self._sendSafe(bodyToSend)
        finally:
            hb.cancel()

    async def commandParser(self, body: dict) -> None:
        """
        message send from front-end is first comes to here to redirect appropriate function
        messages related to main communication comes to this class. other messages goes to SerialMonitor class.
        upload message is sent both this class and SerialMonitor class. when new code is uploading serial monitor has to be closed.

        :param body: data that sent from front-end. %100 has 'command' other keys are depended on command
        :type body: dict
        """
        command = body['command']

        if command == None:
            return
        else:
            await self.sendResponse()

        if command == "upload":
            fqbn = self.fixFqbn(body['board'])
            await self.upload(fqbn, body['port'], body["code"], body['uploadOptions'])
        elif command == "compile":
            fqbn = self.fixFqbn(body['board'])
            await self.compile(fqbn, body["code"], body['uploadOptions'])
        elif command == "getBoards":
            await self.getBoards()
        elif command == "getVersion":
            await self.getVersion()
        elif command == "changeVersion":
            await self.changeVersion(body['version'])
        elif command == "getExampleNames":
            await self.getExampleNames()
        elif command == "getExample":
            await self.getExample(body['lib'], body['example'])
        elif command == "searchLibrary":
            await self.searchLibrary(body['searchTerm'])
        elif command == "downloadLibrary":
            await self.downloadLibrary(body['libName'], body['libVersion'])
        elif command == "getCoreVersion":
            await self.getCoreVersion()

    def fixFqbn(self, fqbn:str, prefix :str = "deneyap:esp32:") -> str:
        """
        In case prefix is not in fqbn adds it.

        :param fqbn: fully qualified board name
        :type fqbn: str

        :param prefix: prefix that going to be checked
        :type prefix: str
        """

        return fqbn if fqbn.startswith(prefix) else prefix+fqbn

    async def downloadLibrary(self, libName:str, libVersion:str)->None:
        """
        :param libName: full name of the library
        :type libName: str

        :param libVersion: version of the library, like 1.3.12
        :type libVersion: str
        """

        updateError = updateIndex()
        if updateError:
            logging.error("Error while updating index")
            logging.error(updateError)

        logging.info(f"Installling Library: {libName}:{libVersion}")
        result = installLibrary(libName, libVersion)
        bodyToSend = {
            "command": "downloadLibraryResult",
            "result": result
        }
        logging.info(f"Result: {result}")
        bodyToSend = json.dumps(bodyToSend)
        await self.websocket.send(bodyToSend)


    async def searchLibrary(self, searchTerm)->None:
        """
        for searching libraries using arduino-cli

        :param searchTerm: string that typed to front-end. will be search using arduino-cli
        :type searchTerm: str

        :return: returns string but in json format, will be converted to json on front-end
        :rtype: str
        """

        logging.info(f"Searching Library: {searchTerm}")
        libraries = searchLibrary(searchTerm)
        bodyToSend = {
            "command" : "searchLibraryResult",
            "libraries": libraries
        }
        bodyToSend = json.dumps(bodyToSend)
        await self.websocket.send(bodyToSend)

    async def changeVersion(self, version:str)->None:
        """
        for chaning deneyap core version. LIB_PATH, DENEYAP_VERSION varibles in config file will also change accordingly


        :param version: version of core that will be installed
        :type version: str
        """

        logging.info(f"Changing version to {version}")
        bodyToSend = {"command":"versionChangeStatus", "success":True}
        updateError = updateIndex()
        if updateError:
            logging.error("Error while updating index")
            logging.error(updateError)
            bodyToSend["success"] = False
            bodyToSend = json.dumps(bodyToSend)
            await self.websocket.send(bodyToSend)
        else:
            error = downloadCore(version)
            if error:
                logging.error("Version cant be downloaded")
                logging.error(error)
                bodyToSend["success"] = False
            else:
                logging.info("version changed successfully, writing new version to config file")
                Data.config['LIB_PATH'] = Data.config['LIB_PATH'].replace(Data.config['DENEYAP_VERSION'], version)
                Data.config['DENEYAP_VERSION'] = version
                Data.updateConfig()

            bodyToSend = json.dumps(bodyToSend)
            await self.websocket.send(bodyToSend)

    async def sendResponse(self) -> None:
        """
        send message back to front-end to say that message is received succesfully if this message is not send, front-end send message again.
        """
        logging.info(f"Main Websocket sending response back")
        bodyToSend = {"command": "response"}
        bodyToSend = json.dumps(bodyToSend)
        await self.websocket.send(bodyToSend)


    async def upload(self, fqbn:str, port:str, code:str, uploadOptions:str) -> None:
        """
        Compiles and uploads code to board

        :param fqbn: fully qualified board name, board name that recognized by arduino-cli
            dydk_mpv10 for Deneyap Kart
            dym_mpv10 for Deneyap Mini
            dydk1a_mpv10 for Deneyap Kart 1A
            dyg_mpv10 for Deneyap Kart G
            dym_mpv20 for Deneyap Mini v2
            dydk1a_mpv20 for Deneyap Kart 1A v2

        :type fqbn: str

        :param port: port that device is on like COM4
        :type port: str

        :param code: code that sent by front-end
        :type code: str

        :param uploadOptions: upload options for board. it is board spesific and sent by front-end as parsed.
        :type uploadOptions: str
        """

        board = Data.boards[port]
        pipe = board.uploadCode(code, fqbn, uploadOptions)
        self.current_pipe = pipe

        try:
            bodyToSend = {"command": "cleanConsoleLog", "log": ""}
            bodyToSend = json.dumps(bodyToSend)
            await self.websocket.send(bodyToSend)
            await self.readAndSend(pipe)
        finally:
            self.current_pipe = None
            terminatePipe(pipe)

    async def getVersion(self) -> None:
        """
        Sends agent version to front-end.
        it notifies user that new version is exists.
        """
        bodyToSend = {"command": "returnVersion", "version": Data.config["AGENT_VERSION"]}
        bodyToSend = json.dumps(bodyToSend)
        await self.websocket.send(bodyToSend)

    async def getCoreVersion(self) -> None:
        """
        Sends deneyap core version to front-end.
        """

        logging.info(f"Sending core version to front-end: {Data.config['DENEYAP_VERSION']}")
        bodyToSend = {"command": "returnCoreVersion", "version": Data.config["DENEYAP_VERSION"]}
        bodyToSend = json.dumps(bodyToSend)
        await asyncio.sleep(1)
        await self.websocket.send(bodyToSend)

    async def compile(self, fqbn:str, code:str, uploadOptions:str) -> None:
        """
        compiles code

        :param fqbn: fully qualified board name, board name that recognized by arduino-cli
            dydk_mpv10 for Deneyap Kart
            dym_mpv10 for Deneyap Mini
            dydk1a_mpv10 for Deneyap Kart 1A
            dyg_mpv10 for Deneyap Kart G
            dym_mpv20 for Deneyap Mini v2
            dydk1a_mpv20 for Deneyap Kart 1A v2

        :type fqbn: str
        :param code: code that sent by front-end
        :type code: str

        :param uploadOptions: upload options for board. it is board spesific and sent by front-end as parsed.
        :type uploadOptions: str
        """

        pipe = Board.compileCode(code, fqbn, uploadOptions)
        self.current_pipe = pipe

        try:
            bodyToSend = {"command": "cleanConsoleLog", "log": "Compling Code...\n"}
            bodyToSend = json.dumps(bodyToSend)
            await self.websocket.send(bodyToSend)
            await self.readAndSend(pipe)
        finally:
            self.current_pipe = None
            terminatePipe(pipe)

    async def getBoards(self) -> None:
        """
        Sends devices that are connected to front-end
        """

        Board.refreshBoards()
        await Board.sendBoardInfo(self.websocket)

    def closeSocket(self) -> None:
        """
        closes device checker process
        """

        logging.info("Closing DeviceChecker")
        self.deviceChecker.terminate()
        self.deviceChecker.process.join()
        logging.info("DeviceChecker Closed")

    async def mainLoop(self) -> None:
        """
        main loop for main communication. checks if there is a message send my front-end if there is sends it to commandParser function.
        takes commands to queue then processes them.
        """
        try:
            while True:
                body = {"command":None}

                try:
                    message=await asyncio.wait_for(self.websocket.recv(), timeout=0.1)
                    logging.info(f"Main Websocket received {message}")
                    body = json.loads(message)
                except (asyncio.TimeoutError, ConnectionRefusedError):
                    if not self.queue.empty():
                        body = self.queue.get()
                except Exception:
                    logging.exception("Main Websocket recv error: ")
                    await self.websocket.close()
                    logging.info("Websocket is closed")
                    break

                await self.commandParser(body)
        except:
            logging.exception("Websocket Mainloop: ")
        finally:
            # baglanti koptuysa yarim kalan derleme/yukleme portu kilitlemesin
            terminatePipe(self.current_pipe)
            self.current_pipe = None
            self.deviceChecker.terminate()
            self.deviceChecker.process.join()
