# Motiosense

Find out quickly if a room is occupied

## Description

Motiosense is a [Slack](https://slack.com) bot written in Python. There are two modes that `motiosense` can run in: `server` and `client`. Both modes are implemented as Python scripts and run as `systemd` services.

**Server Mode**

The Server mode handles the command parsing and responses. See [main.py](src/main.py).

**Client Mode**

The Client mode alerts the `server` of the status of the motion sensor. It can run on any system that has `Python` installed. See [sensor.py](src/sensor.py).

## References

- [How to Build Your First Slack Bot with Python](https://www.fullstackpython.com/blog/build-first-slack-bot-python.html)
