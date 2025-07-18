"""MQTT subscriber module for Power Plug status monitoring."""

import secrets
from typing import Any

from paho.mqtt import client as mqtt_client

broker = "localhost"
port = 1883
topic = "zigbee2mqtt/Power Plug"
client_id = f"subscribe-{secrets.randbelow(1000)}"


def connect_mqtt() -> mqtt_client.Client:
    """Connect to the MQTT broker and return the client."""

    def on_connect(
        _client: mqtt_client.Client, _userdata: Any, _flags: dict[str, Any], rc: int
    ) -> None:
        """Handle connection result."""
        if rc == 0:
            # Connected successfully
            pass
        else:
            # Connection failed
            pass

    client = mqtt_client.Client(client_id=client_id)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


def subscribe(client: mqtt_client.Client) -> None:
    """Subscribe to the MQTT topic."""

    def on_message(
        _client: mqtt_client.Client, _userdata: Any, msg: mqtt_client.MQTTMessage
    ) -> None:
        """Handle incoming message."""
        _ = msg.payload.decode(), msg.topic  # Use or log as needed

    client.subscribe(topic)
    client.on_message = on_message


def run() -> None:
    """Start the MQTT subscriber loop."""
    client = connect_mqtt()
    subscribe(client)
    client.loop_forever()


if __name__ == "__main__":
    run()
