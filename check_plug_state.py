"""Module to check and print the state of a Zigbee2MQTT power plug."""

import json
import logging
import secrets
import time
from typing import Any, Optional

from paho.mqtt import client as mqtt_client

# Setup logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

broker = "localhost"
port = 1883
status_topic = "zigbee2mqtt/Power Plug"
get_topic = "zigbee2mqtt/Power Plug/get"
client_id = f"check-state-{secrets.randbelow(1000)}"

device_state = {"received": False, "value": None}


def connect_mqtt() -> mqtt_client.Client:
    """Connect to MQTT broker and return the client."""

    def on_connect(_: mqtt_client.Client, __: Any, ___: Any, rc: int) -> None:
        if rc == 0:
            logger.info("Connected to MQTT Broker")
        else:
            logger.warning(f"Failed to connect, return code {rc}")

    client = mqtt_client.Client(client_id=client_id, protocol=mqtt_client.MQTTv311)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


def on_message(_: mqtt_client.Client, __: Any, msg: mqtt_client.MQTTMessage) -> None:
    """Handle incoming MQTT messages and update device state."""
    payload = msg.payload.decode()
    logger.info(f"Message from `{msg.topic}`: {payload}")
    try:
        data = json.loads(payload)
        if "state" in data:
            device_state["received"] = True
            device_state["value"] = data["state"]
    except json.JSONDecodeError:
        logger.warning("Failed to parse message as JSON")


def check_state(client: mqtt_client.Client) -> Optional[str]:
    """Subscribe to status topic, request device state, and wait for response."""
    client.subscribe(status_topic)
    client.on_message = on_message

    logger.info(f"Requesting state from `{get_topic}`...")
    client.publish(get_topic, json.dumps({"state": ""}))

    for _ in range(10):  # Wait up to 5 seconds
        if device_state["received"]:
            logger.info(f"Device state: {device_state['value']}")
            return device_state["value"]
        time.sleep(0.5)

    logger.warning("No state received. Is the device online and configured?")
    return None


def run() -> None:
    """Run the MQTT client to check the plug state."""
    client = connect_mqtt()
    client.loop_start()
    check_state(client)
    client.loop_stop()


if __name__ == "__main__":
    run()
