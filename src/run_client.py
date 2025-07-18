"""Command-line REST Node Client for interacting with a Zigbee2MQTT Power Plug."""

import argparse
import datetime
import json
import logging
from typing import Any

from madsci.client.node.rest_node_client import RestNodeClient
from madsci.common.types.action_types import ActionRequest

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    """Run the REST Node Client with provided command-line arguments."""
    parser = argparse.ArgumentParser(description="REST Node Client Runner")
    parser.add_argument(
        "--url",
        type=str,
        required=True,
        help="Base URL of the node server (e.g. http://127.0.0.1:2000)",
    )
    parser.add_argument(
        "--action",
        type=str,
        default=None,
        help="Name of the action to perform (e.g. get_state, turn_on, turn_off)",
    )

    args = parser.parse_args()

    client = RestNodeClient(args.url)

    # Always log the node state for quick diagnostics
    logger.info("=== Node State ===")
    state = client.get_state()
    logger.info(json.dumps(state, indent=2))

    # If an action is provided, run it
    if args.action:
        logger.info(f"=== Running Action: {args.action} ===")
        result = client.send_action(ActionRequest(action_name=args.action))

        # Serializer for datetime objects to isoformat strings
        def json_serial(obj: Any) -> str:
            if isinstance(obj, datetime.datetime):
                return obj.isoformat()
            raise TypeError(f"Type {obj.__class__.__name__} not serializable")

        logger.info(json.dumps(result.model_dump(), indent=2, default=json_serial))


if __name__ == "__main__":
    main()
