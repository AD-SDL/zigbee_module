"""REST-based node for Zigbee2MQTT Power Plug with state tracking."""

import json
import time
from typing import Any, Optional

from madsci.common.types.action_types import ActionResult, ActionSucceeded
from madsci.common.types.node_types import NodeDefinition, RestNodeConfig
from madsci.node_module.helpers import action
from madsci.node_module.rest_node_module import RestNode
from paho.mqtt import client as mqtt_client
from ulid import ULID


class PlugNodeConfig(RestNodeConfig):
    """Configuration for MQTT Plug Node."""

    broker: str = "localhost"
    port: int = 1883
    command_topic: str = "zigbee2mqtt/Power Plug/set"
    state_topic: str = "zigbee2mqtt/Power Plug"


class PlugNode(RestNode):
    """Node to control and monitor MQTT-based Power Plug."""

    config_model = PlugNodeConfig
    config: PlugNodeConfig = PlugNodeConfig()
    client: Optional[mqtt_client.Client] = None
    connected: bool = False
    last_state: Optional[str] = None

    def __init__(self) -> None:
        """Initialize the PlugNode with node definition."""
        node_def = NodeDefinition(
            node_name="zigbee_power_plug", module_name="plug_node"
        )
        super().__init__(node_definition=node_def)

    def startup_handler(self) -> None:
        """Initialize MQTT connection and subscribe to state topic."""

        def on_connect(_: Any, __: Any, ___: Any, rc: int) -> None:
            if rc == 0:
                self.logger.log_info("Connected to MQTT broker.")
                self.connected = True
                self.client.subscribe(self.config.state_topic)
            else:
                self.logger.log_error(f"Failed to connect to MQTT broker: {rc}")

        def on_message(_: Any, __: Any, msg: mqtt_client.MQTTMessage) -> None:
            try:
                payload = json.loads(msg.payload.decode())
                current_state = payload.get("state")
                if current_state and current_state != self.last_state:
                    self.logger.log_info(
                        f"State changed: {self.last_state} → {current_state}"
                    )
                    self.last_state = current_state
                    self.node_state["plug_state"] = current_state
            except Exception as e:
                self.logger.log_error(f"Failed to parse MQTT message: {e}")

        def new_ulid_str() -> str:
            return str(ULID())

        client_id = f"plug-controller-{new_ulid_str()}"
        self.client = mqtt_client.Client(
            client_id=client_id, protocol=mqtt_client.MQTTv311
        )
        self.client.on_connect = on_connect
        self.client.on_message = on_message
        self.client.connect(self.config.broker, self.config.port)
        self.client.loop_start()

    def shutdown_handler(self) -> None:
        """Disconnect MQTT client."""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            self.logger.log_info("Disconnected from MQTT broker.")

    def state_handler(self) -> None:
        """Update node state periodically."""
        self.node_state["mqtt_connected"] = self.connected
        self.node_state["target_topic"] = self.config.command_topic

    import time

    def publish_command(self, command: str) -> bool:
        """Publish an ON/OFF command to the MQTT topic and verify the state change."""
        if not self.client:
            self.logger.log_error("MQTT client does not exist.")
            return False

        if not self.connected:
            self.logger.log_error("MQTT client is not connected yet.")
            return False

        if command.lower() not in ["on", "off"]:
            self.logger.log_error("Invalid command. Use 'on' or 'off'.")
            return False

        target_state = command.upper()
        payload = json.dumps({"state": target_state})
        self.logger.log_info(f"Publishing to {self.config.command_topic}: {payload}")
        result = self.client.publish(self.config.command_topic, payload)

        if result[0] != 0:
            self.logger.log_error("Publish failed")
            return False

        # Wait for state confirmation
        self.logger.log_info("Waiting for plug state to update...")
        for _ in range(10):  # check once per second for up to 10 seconds
            time.sleep(1)
            current_state = self.node_state.get("plug_state")
            if current_state == target_state:
                self.logger.log_info(f"Plug state confirmed: {current_state}")
                return True

        self.logger.log_warning(
            f"Plug state did not update to {target_state} after 10s"
        )
        return False

    @action(name="turn_on")
    def turn_on(self) -> ActionResult:
        """Turn the power plug ON."""
        success = self.publish_command("on")
        if success:
            return ActionSucceeded(data={"status": "ON command succeeded"})
        return ActionResult(success=False, message="Failed to turn ON plug")

    @action(name="turn_off")
    def turn_off(self) -> ActionResult:
        """Turn the power plug OFF."""
        success = self.publish_command("off")
        if success:
            return ActionSucceeded(data={"status": "OFF command succeeded"})
        return ActionResult(success=False, message="Failed to turn OFF plug")

    @action(name="get_state")
    def get_state(self) -> ActionResult:
        """Get the current state of the plug."""
        state = self.node_state.get("plug_state", "unknown")
        return ActionSucceeded(data={"plug_state": state})

    @action(name="check_mqtt_connection")
    def check_mqtt_connection(self) -> ActionResult:
        """Check if MQTT client is connected."""
        return ActionSucceeded(data={"mqtt_connected": self.connected})


if __name__ == "__main__":
    plug_node = PlugNode()
    plug_node.start_node()
