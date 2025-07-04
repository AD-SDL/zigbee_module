"""
Water leak sensor MQTT node module.

This module defines a REST node that connects to an MQTT broker to monitor
a Zigbee water leak sensor and provides the leak state.
"""

import json
import secrets
from typing import Any, Optional

from madsci.common.types.action_types import ActionResult, ActionSucceeded
from madsci.common.types.node_types import NodeDefinition, RestNodeConfig
from madsci.node_module.helpers import action
from madsci.node_module.rest_node_module import RestNode
from paho.mqtt import client as mqtt_client


class WaterLeakSensorConfig(RestNodeConfig):
    """Configuration model for the water leak sensor node."""

    broker: str = "localhost"
    port: int = 1883
    status_topic: str = "zigbee2mqtt/Water Leak Detector"
    get_topic: str = "zigbee2mqtt/Water Leak Detector/get"


class WaterLeakSensorNode(RestNode):
    """REST node to monitor water leak sensor via MQTT."""

    config_model = WaterLeakSensorConfig
    config: WaterLeakSensorConfig = WaterLeakSensorConfig()
    client: Optional[mqtt_client.Client] = None
    connected: bool = False
    last_state: Optional[str] = None
    state_received: bool = False

    def __init__(self) -> None:
        """Initialize the water leak sensor node."""
        super().__init__(
            node_definition=NodeDefinition(
                node_name="zigbee_water_leak_sensor",
                module_name="water_leak_sensor_node",
            )
        )

    def startup_handler(self) -> None:
        """Start up the MQTT client and subscribe to leak sensor status."""

        def on_connect(client: mqtt_client.Client, _: Any, __: Any, rc: int) -> None:
            if rc == 0:
                self.logger.log_info("Connected to MQTT broker.")
                self.connected = True
                client.subscribe(self.config.status_topic)
                client.publish(self.config.get_topic, json.dumps({"state": ""}))
            else:
                self.logger.log_error(f"MQTT connection failed: {rc}")

        def on_message(
            _: mqtt_client.Client, __: Any, msg: mqtt_client.MQTTMessage
        ) -> None:
            try:
                payload = json.loads(msg.payload.decode())
                self.logger.log_info(f"MQTT message received: {payload}")

                if "water_leak" not in payload:
                    self.logger.log_warning("MQTT message missing 'water_leak' field.")
                    return

                water_leak = payload["water_leak"]
                current_state = "LEAK DETECTED" if water_leak else "Dry"

                if not self.state_received:
                    self.logger.log_info(f"Initial state: {current_state}")
                    self.state_received = True
                elif current_state != self.last_state:
                    self.logger.log_info(
                        f"Water leak state changed: {self.last_state} → {current_state}"
                    )

                self.last_state = current_state
                self.node_state["leak_state"] = current_state

            except Exception as e:
                self.logger.log_error(f"Failed to parse MQTT message: {e}")

        client_id = f"water-leak-sensor-{secrets.randbelow(1000)}"
        self.client = mqtt_client.Client(
            client_id=client_id, protocol=mqtt_client.MQTTv311
        )
        self.client.on_connect = on_connect
        self.client.on_message = on_message

        self.client.connect(self.config.broker, self.config.port)
        self.client.loop_start()

    def shutdown_handler(self) -> None:
        """Shut down the MQTT client and disconnect."""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            self.logger.log_info("Disconnected from MQTT broker.")

    def state_handler(self) -> None:
        """Update internal node state with current MQTT connection and leak state."""
        self.node_state["mqtt_connected"] = self.connected
        self.node_state["leak_state"] = self.last_state or "unknown"

    @action(name="get_state")
    def get_state(self) -> ActionResult:
        """Return the current water leak state."""
        return ActionSucceeded(
            data={"leak_state": self.node_state.get("leak_state", "unknown")}
        )


if __name__ == "__main__":
    WaterLeakSensorNode().start_node()
