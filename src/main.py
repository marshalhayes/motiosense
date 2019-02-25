#! /usr/bin/motiosense/bin/python

from slackclient import SlackClient

import os
import re
import sys
import time
import socket
import logging

# instantiate Slack client
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))
# motiosense's user ID in Slack: value is assigned after the bot starts up
motiosense_id = None

host = ''  # listen on all addresses (i.e. 0.0.0.0)
port = 52431
sensor_status = "Undetermined"

logging_file = "/tmp/motiosense.log"
FORMAT = "%(asctime)-15s %(message)s"

# constants
RTM_READ_DELAY = 1  # 1 second delay between reading from RTM
COMMANDS = {
    "available?",
    "occupied?",
    "last occupied?",
    "status?"
}
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"


def parse_bot_commands(slack_events):
    """
        Parses a list of events coming from the Slack RTM API to find bot commands.
        If a bot command is found, this function returns a tuple of command and channel.
        If its not found, then this function returns None, None.
    """
    for event in slack_events:
        if event["type"] == "message" and not "subtype" in event:
            user_id, message = parse_direct_mention(event["text"])
            if user_id == motiosense_id:
                return message, event["channel"]
    return None, None


def parse_direct_mention(message_text):
    """
        Finds a direct mention (a mention that is at the beginning) in message text
        and returns the user ID which was mentioned. If there is no direct mention, returns None
    """
    matches = re.search(MENTION_REGEX, message_text)
    # the first group contains the username, the second group contains the remaining message
    return (matches.group(1), matches.group(2).strip()) if matches else (None, None)


def handle_command(command, channel):
    """
        Executes bot command if the command is known
    """
    # Default response is help text for the user
    response = "Not sure what you mean. Try one of these: {}.".format(
        list(COMMANDS))

    # Ensures a valid command was used and fills in the response accordingly
    if command in COMMANDS:
        # a valid command was used
        if command == "available?" or command == "occupied?":
            response = "Sensor status is _%s_" % sensor_status.upper()
        elif command == "last occupied?":
            response = "Not implemented yet. Sensor status is currently _%s_" % sensor_status.upper()
        elif command == "status?":
            # TODO: respond with all known information (last occupied, available/occupied)
            response = "Sensor status is _%s_" % sensor_status.upper()

    # Sends the response back to the channel
    slack_client.api_call(
        "chat.postMessage",
        channel=channel,
        text=response
    )


if __name__ == "__main__":
    logging.basicConfig(filename=logging_file, format=FORMAT, level="DEBUG")

    try:
        # Setup a socket to listen for status from the sensor
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        sock.bind((host, port))
        sock.listen(1)
    except socket.error as e:
        logging.error(e)
        sys.exit(1)

    if slack_client.rtm_connect(with_team_state=False):
        logging.info("Motiosense connected and running!")
        # Read bot's user ID by calling Web API method `auth.test`
        motiosense_id = slack_client.api_call("auth.test")["user_id"]

        while True:
            try:
                conn, addr = sock.accept()
                try:
                    while True:
                        # receive the sensor status from the buffer
                        data = conn.recv(16)
                        if data:
                            # update the sensor_status
                            sensor_status = data.decode()
                        else:
                            break
                finally:
                    conn.close()
            except socket.timeout as e:
                continue
            except socket.error as e:
                logging.error(e)
                continue
            finally:
                command, channel = parse_bot_commands(slack_client.rtm_read())
                if command:
                    handle_command(command, channel)
                time.sleep(RTM_READ_DELAY)
    else:
        logging.debug(
            "Slack RTM connect failed.")
        sys.exit(1)
