#! /usr/bin/motiosense/bin/python

from datetime import datetime

import RPi.GPIO as GPIO

import os
import sys
import time
import socket
import logging

host = "mluofm.memphis.edu"
port = 52431

logging_file = "/tmp/motiosense.log"
FORMAT = "%(asctime)-15s %(message)s"

STATUSES = {
    "ACTIVE",
    "UNDETERMINED",
    "OCCUPIED"
}


class Sensor(object):
    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.status = "Undetermined"
        self.history = None

    def shrink_history(self, threshold=7, dateformat="%Y-%m-%d %H:%M"):
        """
            Shrinks a history file based on if an entry is < threshold
        """
        with open("./history.log", "r+") as f:
            contents = f.readlines()  # read the history
            now = datetime.now()  # get the current date
            # iterate over the history from least recent to most recent (i.e. bottom to top)
            i = len(contents) - 1
            for line in reversed(contents):
                date, time, _ = line.split()
                date = datetime.strptime(
                    "%s %s" % (date, time), dateformat)
                if (now - date).days > threshold:
                    contents.pop(i)  # delete the old entry
                i -= 1

            f.seek(0)  # reset the pointer to the top of the file
            # overwrite the file with contents
            f.write(''.join(map(str, contents)))
            f.truncate()
        return contents

    def update_history(self, entry=None, dateformat="%Y-%m-%d %H:%M"):
        with open("./history.log", "r+") as f:
            contents = f.readlines()  # read the history
            f.seek(0)  # reset the pointer

            if entry is not None:
                if isinstance(entry, str):
                    f.write(entry)
                elif isinstance(entry, list):
                    f.write(''.join(entry))
                else:
                    raise TypeError(
                        "entry must be an instance of %s or %s" % ("list", "str"))
            else:
                # write new information
                now = datetime.now().strftime(dateformat)
                entry = "%s %s\n" % (now, self.status.upper())
                f.write(entry)

            f.write(''.join(map(str, contents)))

    def is_status(self, status="active"):
        assert status.upper() in STATUSES, "%s is not a valid status. Use one of [%s]" % (
            status, ', '.join(map(str, STATUSES)))
        return self.status.upper().strip() == status

    def get_status(self):
        return self.status

    def set_status(self, status):
        self.status = status


if __name__ == "__main__":
    logging.basicConfig(filename=logging_file, format=FORMAT, level="DEBUG")

    # setup the sensor connected on pin 23
    pir_sensor = 23
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(pir_sensor, GPIO.IN)
    # initally set the sensor status to 0 (not active)
    current_state = 0

    s = Sensor(0, "DH 206")

    try:
        while True:
            time.sleep(10)
            current_state = GPIO.input(pir_sensor)
            if current_state == 1:
                # state of sensor is active, update status
                s.set_status("ACTIVE")
            else:
                # state is not active, update status
                s.set_status("UNDETERMINED")

            # open a socket to send the status to the server
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sensor_status = s.get_status()
                try:
                    # try to send the status to the server
                    sock.connect((host, port))
                    sock.sendall(sensor_status.encode())
                except socket.error as e:
                    # if sending fails for some reason, try again in 10 seconds (i.e. time.sleep(10))
                    logging.error(e)
                    continue
    except KeyboardInterrupt:
        # for testing
        pass
    finally:
        GPIO.cleanup()
