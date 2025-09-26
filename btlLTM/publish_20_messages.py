#!/usr/bin/env python3
import json
import time
from typing import Any, Dict

from client_MQTT_broker import SimpleMQTTClient


def build_message(message_id: int) -> str:
    obj: Dict[str, Any] = {
        "id": message_id,
        "data": message_id * 1.0,
        "time": time.time(),
    }
    return json.dumps(obj, ensure_ascii=False)


def main() -> None:
    broker_host = "192.168.3.4"
    broker_port = 20904
    topic = "test/demo"
    client_id = "publisher_20_msgs"

    client = SimpleMQTTClient(broker_host=broker_host, broker_port=broker_port, client_id=client_id)
    if not client.connect():
        print("Failed to connect to MQTT broker")
        return

    # Publish 20 messages with id starting from 1
    for i in range(1, 21):
        payload = build_message(i)
        ok = client.publish(topic, payload)
        print(f"Publish id={i} ok={ok}")
        time.sleep(0.1)

    # Graceful disconnect to avoid broker seeing a forced close
    try:
        client.disconnect()
    except Exception:
        pass


if __name__ == "__main__":
    main()

