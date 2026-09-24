import asyncio
import json
import traceback
from utils import Data
import serial
import logging
import config
import websockets
import websockets.legacy.server  # annotation icin yan yukleme (websockets.legacy)

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


class SerialMonitorWebsocket(aobject):
    """
    For serial monitor communication, for every front-end connection, one object is created
    """

    async def __init__(self, websocket:websockets.legacy.server.WebSocketServerProtocol, path=None):
        """
        :param websocket: websocket connection to front-end
        :type websocket: websockets.legacy.server.WebSocketServerProtocol

        :param path: need for websockets library to work. not used in this project
        :type path: str
        """

        logging.info(f"SerialMonitorWebsocket is object created")

        self.websocket = websocket
        self.serialOpen = False
        self.ser = None
        await self.mainLoop()

    async def commandParser(self, body:dict) -> None:
        """
        message send from front-end is first comes to here to redirect appropriate function
        messages related to serial monitor comes to this class. other messages goes to Websocket class.
        upload message is sent both this class and Websocket class. when new code is uploading serial monitor has to be closed.

        :param body: data that sent from front-end. %100 has 'command' other keys are depended on command
        :type body: dict
        """

        command = body['command']

        if command == None:
            return
        else:
            await self.sendResponse()

        if command == "upload":
            await self.closeSerialMonitor()
        elif command == "openSerialMonitor":
            self.openSerialMontor(body["port"], body["baudRate"])
        elif command == "closeSerialMonitor":
            await self.closeSerialMonitor()
        elif command == "serialWrite":
            self.serialWrite(body["text"])


    def serialWrite(self, text:str) -> None:
        """
        simulates arduino's serial write function

        :param text: string that will be send to Deneyap kart/mini.
        :type text: str
        """

        if self.serialOpen:
            logging.info(f"Writing to serial, data:{text}")
            self.ser.write(text.encode("utf-8"))

    def openSerialMontor(self, port:str, baudRate:int) -> None:
        """
        opens serial monitor to communicate with deneyap kart/mini

        :param port: port that board is on, like COM4
        :type port: str

        :param baudRate: baud rate that serial monitor will be opened 9600, 115200 etc.
        :type baudRate: int
        """

        logging.info(f"Opening serial monitor")
        if not self.serialOpen:
            self.serialOpen = True

            self.ser = serial.Serial()
            self.ser.baudrate = baudRate
            self.ser.port = port

            # Data.boards[port] bir Board objesidir; orijinal kod string ile
            # karsilastiriyordu (hic eslesmiyordu). fqbn uzerinden bak.
            board = Data.boards.get(port) if isinstance(Data.boards, dict) else None
            fqbn = getattr(board, "fqbn", "") or ""
            # deneyap:esp32:dydk_mpv10 -> dydk_mpv10
            short = fqbn.split(":")[-1] if fqbn else ""

            if short in (config.deneyapKart, config.deneyapKart1A):
                self.ser.setDTR(False)
                self.ser.setRTS(False)
                self.ser.open()

            elif short == config.deneyapKartG:
                self.ser.setDTR(True)
                self.ser.setRTS(True)
                self.ser.open()

            else:
                 self.ser.setDTR(True)
                 self.ser.setRTS(True)
                 self.ser.open()

    async def sendResponse(self) -> None:
        """
        send message back to front-end to say that message is received succesfully if this message is not send, front-end send message again.
        """

        bodyToSend = {"command": "response"}
        bodyToSend = json.dumps(bodyToSend)
        logging.info(f"SerialMonitorWebsocket sending response back")
        await self.websocket.send(bodyToSend)

    async def closeSerialMonitor(self) -> None:
        """
        closes serial monitor.
        """
        logging.info(f"Closing serial monitor")
        if self.serialOpen and self.ser != None:
            self.ser.close()
            bodyToSend = {"command":"closeSerialMonitor"}
            bodyToSend = json.dumps(bodyToSend)
            await self.websocket.send(bodyToSend)

        self.serialOpen = False

    async def serialLog(self) -> None:
        """
        Reads whatever serial monitor has and sends to front-end
        if there is no delay at code, front-end fails to keep up lags
        """
        if self.serialOpen and self.ser != None:
            try:
                waiting = self.ser.in_waiting
                line = self.ser.read(waiting).decode("utf-8")
            except serial.SerialException:
                await self.closeSerialMonitor()
                return
            except:
                return
            if line == "":
                return
            bodyToSend = {"command":"serialLog", "log":line}
            bodyToSend = json.dumps(bodyToSend)
            await self.websocket.send(bodyToSend)

    async def mainLoop(self) -> None:
        """
        main loop for serial monitor. checks if there is a message send my front-end if there is sends it to commandParser function.
        priorities commands over serial read from board.
        if there is no command, then it reads serial, if it is opened.
        """
        while True:
            try:
                if not self.serialOpen:
                    await asyncio.sleep(.3)

                body = {"command":None}

                try:
                    message= await asyncio.wait_for(self.websocket.recv(), timeout=0.000001)
                    logging.info(f"SerialMonitorWebsocket received {message}")
                    body = json.loads(message)

                except (asyncio.TimeoutError, ConnectionRefusedError):
                    if self.serialOpen:
                        await self.serialLog()

                await self.commandParser(body)

            except Exception as e:
                logging.exception("Serial Monitor Error: ")
                bodyToSend = {"command": "serialLog", "log": str(e)+"\n"}
                bodyToSend = json.dumps(bodyToSend)
                await self.websocket.send(bodyToSend)
