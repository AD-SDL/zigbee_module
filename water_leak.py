"""Module for monitoring water leak sensor via MQTT."""

import json
import secrets
import time
from typing import Any

from paho.mqtt import client as mqtt_client


class WaterLeakMonitor:
    """Monitors water leak sensor using MQTT."""

    def __init__(self) -> None:
        """Initialize MQTT broker info and sensor state."""
        self.broker = "localhost"
        self.port = 1883
        self.status_topic = "zigbee2mqtt/Water Leak Detector"
        self.get_topic = "zigbee2mqtt/Water Leak Detector/get"
        self.client_id = f"leak-sensor-{secrets.randbelow(1000)}"
        self.last_state: str | None = None
        self.state_received = False

    def connect_mqtt(self) -> mqtt_client.Client:
        """Connect to the MQTT broker and return the configured client."""

        def on_connect(
            client: mqtt_client.Client, _userdata: Any, _flags: dict[str, Any], rc: int
        ) -> None:
            """Callback for MQTT connection status."""
            if rc == 0:
                client.subscribe(self.status_topic)
                client.publish(self.get_topic, json.dumps({"state": ""}))
            # else: handle error with logging if needed

        client = mqtt_client.Client(
            client_id=self.client_id, protocol=mqtt_client.MQTTv311
        )
        client.on_connect = on_connect
        client.on_message = self.on_message
        client.connect(self.broker, self.port)
        return client

    def on_message(
        self, _client: mqtt_client.Client, _userdata: Any, msg: mqtt_client.MQTTMessage
    ) -> None:
        """Process incoming MQTT messages for water leak status."""
        payload = msg.payload.decode()
        try:
            data = json.loads(payload)
            state = data.get("water_leak", data.get("water"))
            if state is not None:
                current_state = "LEAK DETECTED" if state else "Dry"
                if not self.state_received:
                    self.last_state = current_state
                    self.state_received = True
                    # Log or store the initial state
                elif current_state != self.last_state:
                    self.last_state = current_state
                    # Log or handle state change
        except json.JSONDecodeError:
            # Handle invalid JSON message
            pass

    def run(self) -> None:
        """Run the MQTT client and monitor loop."""
        client = self.connect_mqtt()
        client.loop_start()

        for _ in range(10):
            if self.state_received:
                break
            time.sleep(0.5)

        if not self.state_received:
            # Log a warning about the missing state
            pass

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            client.loop_stop()
            # Handle graceful shutdown


if __name__ == "__main__":
    monitor = WaterLeakMonitor()
    monitor.run()
