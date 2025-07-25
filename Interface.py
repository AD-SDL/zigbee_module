"""Module for interfacing with a Zigbee2MQTT Power Plug via MQTT."""

import json
import logging
import secrets
import time
from typing import Any, Optional

from paho.mqtt import client as mqtt_client

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class Interface:
    """Interface to monitor and control a Zigbee2MQTT power plug."""

    def __init__(self) -> None:
        """Initialize the Interface with broker settings."""
        self.broker = "localhost"
        self.port = 1883
        self.status_topic = "zigbee2mqtt/Power Plug"
        self.get_topic = "zigbee2mqtt/Power Plug/get"
        self.set_topic = "zigbee2mqtt/Power Plug/set"
        self.device_state = {"received": False, "value": None}

    def connect_mqtt(self, client_id: str) -> mqtt_client.Client:
        """Connect to the MQTT broker."""

        def on_connect(_: mqtt_client.Client, __: Any, ___: Any, rc: int) -> None:
            if rc == 0:
                logger.info("Connected to MQTT Broker")
            else:
                logger.warning(f"Failed to connect, return code {rc}")

        client = mqtt_client.Client(client_id=client_id, protocol=mqtt_client.MQTTv311)
        client.on_connect = on_connect
        client.connect(self.broker, self.port)
        return client

    def get_state(self) -> Optional[str]:
        """Request and retrieve the current state of the power plug."""
        client_id = f"check-state-{secrets.randbelow(1000)}"
        client = self.connect_mqtt(client_id)

        def on_message(
            _: mqtt_client.Client, __: Any, msg: mqtt_client.MQTTMessage
        ) -> None:
            payload = msg.payload.decode()
            logger.info(f"Message from `{msg.topic}`: {payload}")
            try:
                data = json.loads(payload)
                if "state" in data:
                    self.device_state["received"] = True
                    self.device_state["value"] = data["state"]
            except json.JSONDecodeError:
                logger.warning("Failed to parse message as JSON")

        client.on_message = on_message
        client.loop_start()
        client.subscribe(self.status_topic)

        logger.info(f"Requesting state from `{self.get_topic}`...")
        client.publish(self.get_topic, json.dumps({"state": ""}))

        for _ in range(10):  # wait up to 5 seconds
            if self.device_state["received"]:
                state = self.device_state["value"]
                logger.info(f"Device state: {state}")
                client.loop_stop()
                return state
            time.sleep(0.5)

        client.loop_stop()
        logger.warning("No state received. Is the device online?")
        return None

    def turn_on(self, turn_on: bool = True) -> None:
        """Send a command to turn the power plug on or off."""
        client_id = f"plug-controller-{secrets.randbelow(1000)}"
        client = self.connect_mqtt(client_id)
        client.loop_start()

        command = "ON" if turn_on else "OFF"
        payload = json.dumps({"state": command})
        status = client.publish(self.set_topic, payload)[0]

        if status == 0:
            logger.info(f"Sent `{payload}` to `{self.set_topic}`")
        else:
            logger.warning("Failed to send command")

        time.sleep(1)
        client.loop_stop()
