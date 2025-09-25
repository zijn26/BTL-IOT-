"""
CoAP Simulator Client
Gửi N gói JSON đến CoAP server để test luồng nhận.

Payload mẫu mỗi gói:
  {"id": <int>, "data": <float>, "time": <epoch_seconds>}

Usage (mặc định 20 gói, path /test/demo):
  python btlLTM/CoAPSimClient.py
  python btlLTM/CoAPSimClient.py --host 127.0.0.1 --port 5683 --path /test/demo --count 20
"""

import argparse
import json
import random
import time

from CoAPClient import SimpleCoAPClient, print_response


def send_packets(host: str, port: int, path: str, count: int) -> None:
    client = SimpleCoAPClient()
    base_id = 0

    print(f"Sending {count} packets to coap://{host}:{port}{path}")
    for i in range(1, count + 1):
        payload = {
            "id": base_id + i,
            "data": round(random.uniform(0.0, 100.0), 3),
            "time": time.time(),  # start time
        }
        payload_str = json.dumps(payload)
        print(f"\n[#{i}] POST {path} -> {payload_str}")
        resp = client.post(host, port, "/test/demo", payload_str)
        print_response(resp)

        # Giả lập delay giữa các gói
        time.sleep(random.uniform(0.05, 0.25))


def main():
    parser = argparse.ArgumentParser(description="CoAP Simulator Client")
    parser.add_argument("--host", default="127.0.0.1", help="CoAP server host")
    parser.add_argument("--port", type=int, default=5683, help="CoAP server port")
    parser.add_argument("--path", default="/test/demo", help="CoAP resource path")
    parser.add_argument("--count", type=int, default=20, help="Number of packets to send")
    args = parser.parse_args()

    send_packets(args.host, args.port, args.path, args.count)


if __name__ == "__main__":
    main()

