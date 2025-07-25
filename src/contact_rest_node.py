"""REST-based node for Zigbee2MQTT Contact Sensor with state tracking."""

import json
import secrets
from typing import Any, Optional

from madsci.common.types.action_types import ActionResult, ActionSucceeded
from madsci.common.types.node_types import NodeDefinition, RestNodeConfig
from madsci.node_module.helpers import action
from madsci.node_module.rest_node_module import RestNode
from paho.mqtt import client as mqtt_client


class ContactSensorConfig(RestNodeConfig):
    """Configuration for MQTT Contact Sensor."""

    broker: str = "localhost"
    port: int = 1883
    status_topic: str = "zigbee2mqtt/Contact Sensor"
    get_topic: str = "zigbee2mqtt/Contact Sensor/get"


class ContactSensorNode(RestNode):
    """Node to monitor MQTT-based Contact Sensor."""

    config_model = ContactSensorConfig
    config: ContactSensorConfig = ContactSensorConfig()
    client: Optional[mqtt_client.Client] = None
    connected: bool = False
    last_state: Optional[str] = None
    state_received: bool = False

    def __init__(self) -> None:
        """Initialize the contact sensor node."""
        node_def = NodeDefinition(
            node_name="zigbee_contact_sensor", module_name="contact_sensor_node"
        )
        super().__init__(node_definition=node_def)

    def startup_handler(self) -> None:
        """Connect to MQTT broker and subscribe to status topic."""

        def on_connect(client: mqtt_client.Client, _: Any, __: Any, rc: int) -> None:
            if rc == 0:
                self.logger.log_info("Connected to MQTT broker.")
                self.connected = True
                client.subscribe(self.config.status_topic)
                client.publish(self.config.get_topic, json.dumps({"state": ""}))
            else:
                self.logger.log_error(f"Failed to connect: {rc}")

        def on_message(
            _: mqtt_client.Client, __: Any, msg: mqtt_client.MQTTMessage
        ) -> None:
            try:
                data = json.loads(msg.payload.decode())
                if "contact" in data:
                    current_state = "Closed" if data["contact"] else "Open"
                    if not self.state_received:
                        self.logger.log_info(f"Initial state: {current_state}")
                        self.last_state = current_state
                        self.state_received = True
                    elif current_state != self.last_state:
                        self.logger.log_info(
                            f"Contact state changed: {self.last_state} → {current_state}"
                        )
                        self.last_state = current_state
                    self.node_state["contact_state"] = current_state
            except Exception as e:
                self.logger.log_error(f"Failed to parse MQTT message: {e}")

        client_id = f"contact-sensor-{secrets.randbelow(1000)}"
        self.client = mqtt_client.Client(
            client_id=client_id, protocol=mqtt_client.MQTTv311
        )
        self.client.on_connect = on_connect
        self.client.on_message = on_message
        self.client.connect(self.config.broker, self.config.port)
        self.client.loop_start()

    def shutdown_handler(self) -> None:
        """Stop MQTT client and disconnect."""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            self.logger.log_info("Disconnected from MQTT broker.")

    def state_handler(self) -> None:
        """Update internal state values."""
        self.node_state["mqtt_connected"] = self.connected
        self.node_state["contact_state"] = self.last_state or "unknown"

    @action(name="get_state")
    def get_state(self) -> ActionResult:
        """Return current contact sensor state (Open/Closed)."""
        state = self.node_state.get("contact_state", "unknown")
        return ActionSucceeded(data={"contact_state": state})


if __name__ == "__main__":
    node = ContactSensorNode()
    node.start_node()
