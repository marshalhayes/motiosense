#! /usr/bin/python

import RPi.GPIO as GPIO
import time


def main():
    pass


if __name__ == "__main__":
    pir_sensor = 23

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(pir_sensor, GPIO.IN)
    current_state = 0

    try:
        while True:
            time.sleep(0.5)
            current_state = GPIO.input(pir_sensor)
            print(current_state)
            # if current_state == 1:
            #     print("GPIO pin %s is %s" % (pir_sensor, current_state))
    except KeyboardInterrupt:
        pass
    finally:
        GPIO.cleanup()
