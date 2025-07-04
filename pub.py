"""Module to publish test MQTT messages to a Zigbee2MQTT topic."""

import logging
import secrets
import time
from typing import Any

from paho.mqtt import client as mqtt_client

# Setup logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

broker = "localhost"
port = 1883
topic = "zigbee2mqtt/Power Plug"
client_id = f"publish-{secrets.randbelow(1000)}"


def connect_mqtt() -> mqtt_client.Client:
    """Connect to the MQTT broker and return the client."""

    def on_connect(_: Any, __: Any, ___: Any, rc: int) -> None:
        if rc == 0:
            logger.info("Connected to MQTT Broker!")
        else:
            logger.warning(f"Failed to connect, return code {rc}")

    client = mqtt_client.Client(client_id)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


def publish(client: mqtt_client.Client) -> None:
    """Publish test messages to the MQTT topic."""
    msg_count = 1
    while msg_count <= 5:
        time.sleep(1)
        msg = f"Test message {msg_count}"
        result = client.publish(topic, msg)
        status = result[0]
        if status == 0:
            logger.info(f"Sent `{msg}` to `{topic}`")
        else:
            logger.warning(f"Failed to send message to topic {topic}")
        msg_count += 1


def run() -> None:
    """Run the MQTT client to publish messages."""
    client = connect_mqtt()
    client.loop_start()
    publish(client)
    client.loop_stop()


if __name__ == "__main__":
    run()
