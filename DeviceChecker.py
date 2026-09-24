import multiprocessing
from multiprocessing import Process, Queue
from serial.tools import list_ports
import time
import logging

class DeviceChecker:
    """
    Checks devices that are plugged or on plugged, works on a diffrent process.

    queue(Manager.Queue): Ana process'e veri göndermek için

    startStopQueue(Manager.Queue): Dışarıdan gelen veriyi almak
    """
    def __init__(self, queue: multiprocessing.Queue):
        """
        :param queue: queue for communicationg between Websocket class and DeviceChecker
        :type queue: multiprocessing.Queue
        """

        self.queue = queue
        self.startStopQueue = Queue()
        self.process = Process(target=self.queuer, args=(self.queue, self.startStopQueue))
        logging.info(f"Starting process for DeviceChekcer with PID:{self.process.pid}")

        self.process.start()

    def queuer(self, queue: multiprocessing.Queue, startStopQueue: multiprocessing.Queue) -> None:
        """
        send signal to Websocket class when a new device is found. checks if new device added or any device removed
        every second.

        :param queue: queue for getting orders from Websocket class
        :type queue: multiprocessing.Queue

        :param startStopQueue: queue for stoping, starting and terminating deviceChecker
        :type startStopQueue: multiprocessing.Queue
        """

        logging.info(f"Process Started Succesfully")
        runner = False
        old_devices = self.enumerate_serial_devices()

        while True:
            if not startStopQueue.empty():
                command = startStopQueue.get()['command']
                if command == 'startDeviceChecker':
                    logging.info(f"Device checker Started")
                    runner = True
                elif command == 'stopDeviceChecker':
                    logging.info(f"Device checker Stoped")
                    runner = False
                elif command == 'terminateDeviceChecker':
                    logging.info(f"Device checker Terminated")
                    break

            if runner:
                old_devices, changed = self.check_new_devices(old_devices)
                if changed:
                    logging.info(f"Change on devices")
                    queue.put({"sender":"deviceChecker", "command":"getBoards"})

            time.sleep(1)
    def start(self) -> None:
        """
        Allows querer to run 'if runner' block in querer while loop
        """
        self.startStopQueue.put({"command":"startDeviceChecker"})
        logging.info(f"Starting device checker")

    def stop(self) -> None:
        """
        Stops 'if runner' block in querer while loop
        """

        self.startStopQueue.put({"command": "stopDeviceChecker"})
        logging.info(f"Stoping device checker")

    def terminate(self) -> None:
        """
        makes querer break while loop causing process to end
        """
        self.startStopQueue.put({"command": "terminateDeviceChecker"})
        logging.info(f"Termitating device checker")

    def enumerate_serial_devices(self) -> set:
        """
        takes set of plugged devices

        :return: returns a set of devices
        :rtype: set
        """
        return set([item for item in list_ports.comports()])

    def check_new_devices(self, old_devices: set) -> (set, bool):
        """
        checks if any device is added or removed

        :param old_devices: old detected devices, comes from previous loop. can be emtpty
        :type old_devices: set

        :return: returns a tuple, first element is all devices second element is whetever it is diffrent from previous loop or not
        :rtype: (set, bool)
        """
        devices = self.enumerate_serial_devices()
        added = devices.difference(old_devices)
        removed = old_devices.difference(devices)
        changed = True if added or removed else False
        return devices, changed