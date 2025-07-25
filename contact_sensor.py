"""Module for monitoring a Zigbee2MQTT contact sensor via MQTT."""

import json
import secrets
from typing import Any

from paho.mqtt import client as mqtt_client


class ContactSensorMonitor:
    """Monitor for a Zigbee2MQTT contact sensor."""

    def __init__(self) -> None:
        """Initialize the MQTT contact sensor monitor."""
        self.broker = "localhost"
        self.port = 1883
        self.status_topic = "zigbee2mqtt/Contact Sensor"
        self.get_topic = "zigbee2mqtt/Contact Sensor/get"
        self.client_id = f"contact-sensor-{secrets.randbelow(1000)}"
        self.last_state = None
        self.state_received = False

    def connect_mqtt(self) -> mqtt_client.Client:
        """Connect to the MQTT broker and subscribe to topics."""

        def on_connect(client: mqtt_client.Client, _: Any, __: Any, rc: int) -> None:
            if rc == 0:
                client.subscribe(self.status_topic)
                client.publish(self.get_topic, json.dumps({"state": ""}))
            else:
                pass

        client = mqtt_client.Client(
            client_id=self.client_id, protocol=mqtt_client.MQTTv311
        )
        client.on_connect = on_connect
        client.on_message = self.on_message
        client.connect(self.broker, self.port)
        return client

    def on_message(
        self, _: mqtt_client.Client, __: Any, msg: mqtt_client.MQTTMessage
    ) -> None:
        """Handle incoming MQTT messages."""
        payload = msg.payload.decode()
        try:
            data = json.loads(payload)
            if "contact" in data:
                current_state = "Open" if data["contact"] is False else "Closed"
                if not self.state_received:
                    self.last_state = current_state
                    self.state_received = True
                elif current_state != self.last_state:
                    self.last_state = current_state
        except json.JSONDecodeError:
            pass

    def run(self) -> None:
        """Run the MQTT loop and handle graceful shutdown."""
        client = self.connect_mqtt()
        client.loop_start()

        if not self.state_received:
            pass

        try:
            while True:
                pass
        except KeyboardInterrupt:
            client.loop_stop()
