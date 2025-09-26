import client_MQTT_broker
import json
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs


# Global state for metrics and packets
PACKET_LIMIT = 1000  # Increase to allow more data collection for UI display
UI_DISPLAY_LIMIT = 200  # Maximum messages to display in UI
STATE_LOCK = threading.Lock()

MQTT_STATE = {
    "packets": [],
    "total_bytes": 0,
    "total_tx_time": 0.0,
    "received_count": 0,
    "done": False,
}


"""
Global MQTT runtime state
- MQTT_TOPIC: current subscribed topic for display and default
- MQTT_CLIENT: active client to allow dynamic subscribe via HTTP API
"""
MQTT_TOPIC = "test/demo"
MQTT_CLIENT = None

COAP_STATE = {
    "packets": [],
    "total_bytes": 0,
    "total_tx_time": 0.0,
    "received_count": 0,
    "done": False,
}

COAP_SERVER = None
MQTT_BROKER = None
COAP_CLIENT_STARTED = False
COAP_CLIENT_CONFIG = {
    "host": "127.0.0.1",
    "port": 5683,
    "path": "/test/demo",
}


class StatsHandler(BaseHTTPRequestHandler):
    def _set_common_headers(self, status=200, content_type="text/html; charset=utf-8"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

    def log_message(self, format, *args):
        # Suppress default HTTP request logging to avoid terminal spam on polling
        return

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/" or parsed.path == "/index.html":
            self._set_common_headers()
            self.wfile.write(INDEX_HTML.encode("utf-8"))
            return

        if parsed.path == "/stats":
            qs = parse_qs(parsed.query or "")
            include_coap = str(qs.get("includeCoap", ["0"])[0]).strip() == "1"
            # Build MQTT payload from state
            with STATE_LOCK:
                mqtt_payload = {
                        "packets": MQTT_STATE["packets"],
                        "total_bytes": MQTT_STATE["total_bytes"],
                        "total_tx_time": MQTT_STATE["total_tx_time"],
                        "received_count": MQTT_STATE["received_count"],
                        "done": MQTT_STATE["done"],
                        "aggregate_rate_bps": (MQTT_STATE["total_bytes"] / MQTT_STATE["total_tx_time"]) if MQTT_STATE["total_tx_time"] > 0 else 0.0,
                }
            # Read CoAP data directly from embedded CoAP server resources if requested
            if include_coap and (COAP_SERVER is not None):
                try:
                    now = time.time()
                    packets = []
                    total_bytes = 0
                    total_tx_time = 0.0
                    received_count = 0
                    resources = getattr(COAP_SERVER, "resources", {}) or {}
                    if isinstance(resources, dict):
                        for path, store in resources.items():
                            if isinstance(store, list):
                                for item in store:
                                    try:
                                        msg_str = json.dumps(item, ensure_ascii=False)
                                    except Exception:
                                        continue
                                    message_bytes = len(msg_str.encode("utf-8"))
                                    start_time = None
                                    # Sử dụng thời gian thực tế nhận được gói tin từ CoAP server
                                    if isinstance(item, dict) and "recv_time" in item:
                                        try:
                                            recv_time_val = float(item["recv_time"])
                                        except Exception:
                                            recv_time_val = now
                                    else:
                                        recv_time_val = now
                                    if isinstance(item, dict):
                                        # Use same time parsing logic as MQTT - ONLY use timestamp_ms
                                        try:
                                            if "timestamp_ms" in item:
                                                # timestamp_ms is already in milliseconds, convert to seconds
                                                start_time = float(item["timestamp_ms"]) / 1000.0
                                            else:
                                                # Fallback to current time if no timestamp_ms
                                                start_time = recv_time_val
                                        except Exception:
                                            start_time = recv_time_val
                                        if "recv_time" in item:
                                            try:
                                                recv_time_val = float(item["recv_time"])
                                            except Exception:
                                                recv_time_val = now
                                    tx_time = 0.0
                                    if start_time is not None:
                                        tx_time = max(0.0, recv_time_val - start_time)

                                    # Debug output for CoAP time calculation
                                    timestamp_ms_value = 0
                                    if isinstance(item, dict) and "timestamp_ms" in item:
                                        timestamp_ms_value = float(item["timestamp_ms"])
                                    print(f"[CoAP DEBUG] path={path}, timestamp_ms={timestamp_ms_value:.0f}ms, start_time={start_time:.6f}s, recv_time={recv_time_val:.6f}s, tx_time={tx_time:.6f}s")

                                    received_count += 1
                                    packets.append({
                                        "index": received_count,
                                        "resource": path,
                                        "message_str": msg_str,
                                        "message_bytes": message_bytes,
                                        "start_time": start_time if start_time is not None else recv_time_val,
                                        "recv_time": recv_time_val,
                                        "tx_time": tx_time,
                                    })
                                    total_bytes += message_bytes
                                    total_tx_time += tx_time
                    coap_payload = {
                        "packets": packets,
                        "total_bytes": total_bytes,
                        "total_tx_time": total_tx_time,
                        "received_count": received_count,
                        # Keep running; let UI poll continuously
                        "done": False,
                        "aggregate_rate_bps": (total_bytes / total_tx_time) if total_tx_time > 0 else 0.0,
                    }
                except Exception:
                    with STATE_LOCK:
                        coap_payload = {
                        "packets": COAP_STATE["packets"],
                        "total_bytes": COAP_STATE["total_bytes"],
                        "total_tx_time": COAP_STATE["total_tx_time"],
                        "received_count": COAP_STATE["received_count"],
                        "done": COAP_STATE["done"],
                        "aggregate_rate_bps": (COAP_STATE["total_bytes"] / COAP_STATE["total_tx_time"]) if COAP_STATE["total_tx_time"] > 0 else 0.0,
                        }
            else:
                with STATE_LOCK:
                    coap_payload = {
                        "packets": COAP_STATE["packets"],
                        "total_bytes": COAP_STATE["total_bytes"],
                        "total_tx_time": COAP_STATE["total_tx_time"],
                        "received_count": COAP_STATE["received_count"],
                        # When include_coap is false, send zeros to avoid unintended UI updates
                        "done": False,
                        "aggregate_rate_bps": (COAP_STATE["total_bytes"] / COAP_STATE["total_tx_time"]) if (include_coap and COAP_STATE["total_tx_time"] > 0) else 0.0,
                    }

            payload = {
                "mqtt": mqtt_payload,
                "coap": coap_payload,
                    "expected_count": PACKET_LIMIT,
                "coap_client": COAP_CLIENT_CONFIG,
                "mqtt_current_topic": MQTT_TOPIC,
                "ui_display_limit": UI_DISPLAY_LIMIT,
                }
            data = json.dumps(payload).encode("utf-8")
            self._set_common_headers(200, "application/json; charset=utf-8")
            self.wfile.write(data)
            return

        if parsed.path == "/coap_fetch":
            # Query param: limit=X
            qs = parse_qs(parsed.query or "")
            try:
                limit = int(qs.get("limit", [10])[0])
                if limit < 1:
                    limit = 1
            except Exception:
                limit = 10

            packets = []
            total_bytes = 0
            total_tx_time = 0.0
            received_count = 0
            now = time.time()

            if (COAP_SERVER is not None):
                resources = getattr(COAP_SERVER, "resources", {}) or {}
                if isinstance(resources, dict):
                    # Flatten all items with their paths
                    flat = []
                    for path, store in resources.items():
                        if isinstance(store, list):
                            for item in store:
                                flat.append((path, item))
                    # Take the last `limit` items overall
                    for path, item in flat[-limit:]:
                        try:
                            msg_str = json.dumps(item, ensure_ascii=False)
                        except Exception:
                            continue
                        message_bytes = len(msg_str.encode("utf-8"))
                        start_time = None
                        # Sử dụng thời gian thực tế nhận được gói tin từ CoAP server
                        if isinstance(item, dict) and "recv_time" in item:
                            try:
                                recv_time_val = float(item["recv_time"])
                            except Exception:
                                recv_time_val = now
                        else:
                            recv_time_val = now
                        if isinstance(item, dict):
                            # Use same time parsing logic as main stats - ONLY use timestamp_ms
                            try:
                                if "timestamp_ms" in item:
                                    # timestamp_ms is already in milliseconds, convert to seconds
                                    start_time = float(item["timestamp_ms"]) / 1000.0
                                else:
                                    # Fallback to current time if no timestamp_ms
                                    start_time = recv_time_val
                            except Exception:
                                start_time = recv_time_val
                            
                            if "recv_time" in item:
                                try:
                                    recv_time_val = float(item["recv_time"])
                                except Exception:
                                    recv_time_val = now
                        tx_time = 0.0
                        if start_time is not None:
                            tx_time = max(0.0, recv_time_val - start_time)

                        received_count += 1
                        packets.append({
                            "index": received_count,
                            "resource": path,
                            "message_str": msg_str,
                            "message_bytes": message_bytes,
                            "start_time": start_time if start_time is not None else recv_time_val,
                            "recv_time": recv_time_val,
                            "tx_time": tx_time,
                        })
                        total_bytes += message_bytes
                        total_tx_time += tx_time

            resp = {
                "packets": packets,
                "total_bytes": total_bytes,
                "total_tx_time": total_tx_time,
                "received_count": received_count,
                "aggregate_rate_bps": (total_bytes / total_tx_time) if total_tx_time > 0 else 0.0,
            }
            self._set_common_headers(200, "application/json; charset=utf-8")
            self.wfile.write(json.dumps(resp).encode("utf-8"))
            return

        self._set_common_headers(404, "text/plain; charset=utf-8")
        self.wfile.write(b"Not Found")

    def do_POST(self):
        parsed = urlparse(self.path)
        global MQTT_CLIENT, MQTT_TOPIC

        if parsed.path == "/mqtt_subscribe":
            try:
                length = int(self.headers.get('Content-Length', '0') or 0)
                raw = self.rfile.read(length) if length > 0 else b""
                body = json.loads(raw.decode('utf-8') or "{}")
            except Exception:
                body = {}

            new_topic = str(body.get("topic", "")).strip()
            if not new_topic:
                self._set_common_headers(400, "application/json; charset=utf-8")
                self.wfile.write(json.dumps({"ok": False, "error": "empty_topic"}).encode("utf-8"))
                return

            ok = False
            err = None
            try:
                if MQTT_CLIENT is not None:
                    MQTT_CLIENT.subscribe(new_topic)
                    with STATE_LOCK:
                        MQTT_TOPIC = new_topic
                    ok = True
                else:
                    err = "mqtt_client_not_ready"
            except Exception as e:
                err = f"{e}"

            resp = {"ok": ok, "topic": new_topic, "error": err}
            self._set_common_headers(200, "application/json; charset=utf-8")
            self.wfile.write(json.dumps(resp).encode("utf-8"))
            return

        if parsed.path == "/coap_command":
            try:
                length = int(self.headers.get('Content-Length', '0') or 0)
                raw = self.rfile.read(length) if length > 0 else b""
                body = json.loads(raw.decode('utf-8') or "{}")
            except Exception:
                body = {}

            method = str(body.get("method", "GET")).upper()
            path = str(body.get("path", "/")).strip() or "/"
            payload = str(body.get("payload", ""))

            host = "192.168.3.4"
            port = 2606

            try:
                from CoAPClient import SimpleCoAPClient
                client = SimpleCoAPClient(timeout=5.0)
                if method == "GET":
                    resp = client.get(host, port, path, payload)
                elif method == "POST":
                    resp = client.post(host, port, path, payload)
                elif method == "PUT":
                    resp = client.put(host, port, path, payload)
                elif method == "DELETE":
                    resp = client.delete(host, port, path, payload)
                else:
                    resp = None

                if resp is None:
                    out = {"ok": False, "error": "no_response"}
                else:
                    try:
                        text = resp.payload.decode('utf-8') if resp.payload else ""
                    except Exception:
                        text = resp.payload.hex() if resp.payload else ""
                    out = {
                        "ok": True,
                        "code": int(resp.code),
                        "code_name": getattr(resp.code, 'name', str(resp.code)),
                        "type": getattr(resp.msg_type, 'name', str(resp.msg_type)),
                        "message_id": resp.message_id,
                        "payload": text,
                    }
            except Exception as e:
                out = {"ok": False, "error": f"{e}"}

            self._set_common_headers(200, "application/json; charset=utf-8")
            self.wfile.write(json.dumps(out).encode("utf-8"))
            return

        if parsed.path == "/mqtt_publish":
            try:
                length = int(self.headers.get('Content-Length', '0') or 0)
                raw = self.rfile.read(length) if length > 0 else b""
                body = json.loads(raw.decode('utf-8') or "{}")
            except Exception:
                body = {}

            topic = str(body.get("topic", "")).strip()
            payload = body.get("payload", "")
            if not topic:
                topic = MQTT_TOPIC
            try:
                if not isinstance(payload, str):
                    payload = json.dumps(payload, ensure_ascii=False)
            except Exception:
                payload = str(payload)

            ok = False
            err = None
            try:
                if MQTT_CLIENT is not None and getattr(MQTT_CLIENT, 'connected', False):
                    ok = bool(MQTT_CLIENT.publish(topic, payload))
                    if not ok:
                        err = "publish_failed"
                else:
                    err = "mqtt_client_not_ready"
            except Exception as e:
                err = f"{e}"

            resp = {"ok": ok, "topic": topic, "payload_len": len(payload.encode('utf-8')) if isinstance(payload, str) else 0, "error": err}
            self._set_common_headers(200, "application/json; charset=utf-8")
            self.wfile.write(json.dumps(resp).encode("utf-8"))
            return

        self._set_common_headers(404, "text/plain; charset=utf-8")
        self.wfile.write(b"Not Found")


def run_http_server(host="127.0.0.1", port=8080):
    httpd = HTTPServer((host, port), StatsHandler)
    print(f"HTTP server running at http://{host}:{port}")
    httpd.serve_forever()


def mqtt_collect_loop(broker_host: str, broker_port: int, topic: str, client_id: str, collect_packets: dict):
    client = client_MQTT_broker.SimpleMQTTClient(
        broker_host=broker_host, broker_port=broker_port, client_id=client_id
    )

    if not client.connect():
        print("Failed to connect MQTT broker")
        return

    client.subscribe(topic)

    # expose client for dynamic subscription
    try:
        global MQTT_CLIENT, MQTT_TOPIC
        MQTT_CLIENT = client
        with STATE_LOCK:
            MQTT_TOPIC = topic
    except Exception:
        pass

    def on_message(msg_topic: str, msg_str: str):
        local_recv_time = time.time()
        message_bytes = len(msg_str.encode("utf-8"))
        send_time = local_recv_time
        recv_time_value = local_recv_time
        
        def normalize_epoch(value) -> float:
             # Handle different time formats from client
             try:
                 # If it's already a number, use existing logic
                 if isinstance(value, (int, float)):
                     v = float(value)
                     if v > 1e14:   # nanoseconds
                         return v / 1e9
                     if v > 1e12:   # microseconds
                         return v / 1e6
                     if v > 1e11:   # milliseconds
                         return v / 1e3
                     return v
                 
                 # If it's a string, try to parse HH:MM:SS format
                 if isinstance(value, str):
                     time_str = value.strip()
                     # Check if it's HH:MM:SS format (e.g., "14:30:25")
                     if ':' in time_str and len(time_str.split(':')) == 3:
                         try:
                             from datetime import datetime
                             # Parse as time today
                             today = datetime.now().date()
                             time_obj = datetime.strptime(f"{today} {time_str}", "%Y-%m-%d %H:%M:%S")
                             return time_obj.timestamp()
                         except Exception:
                             pass
                     
                     # Try parsing as float (epoch timestamp)
                     return float(time_str)
                     
             except Exception:
                 pass
             return local_recv_time
        try:
            obj = json.loads(msg_str)
            # Extract sender time - ONLY use timestamp_ms for consistency
            try:
                if "timestamp_ms" in obj:
                    # timestamp_ms is already in milliseconds, convert to seconds
                    send_time = float(obj.get("timestamp_ms")) / 1000.0
                else:
                    # Fallback to current time if no timestamp_ms
                    send_time = local_recv_time
            except Exception:
                send_time = local_recv_time
            try:
                if "recv_time" in obj:
                    recv_time_value = normalize_epoch(obj.get("recv_time", local_recv_time))
            except Exception:
                recv_time_value = local_recv_time
        except Exception:
            pass
        tx_time = max(0.0, recv_time_value - send_time)
        # Cap to avoid extreme outliers if clocks are skewed
        if tx_time > 30.0:
            tx_time = 30.0

        # Debug output for time calculation verification
        try:
            obj = json.loads(msg_str)
            if "timestamp_ms" in obj:
                time_source = "timestamp_ms"
                timestamp_ms_value = float(obj.get("timestamp_ms"))
            else:
                time_source = "fallback"
                timestamp_ms_value = 0
        except:
            time_source = "error"
            timestamp_ms_value = 0
        print(f"[DEBUG] timestamp_ms={timestamp_ms_value:.0f}ms, send_time={send_time:.6f}s, recv_time={recv_time_value:.6f}s, tx_time={tx_time:.6f}s")

        with STATE_LOCK:
            if MQTT_STATE["done"]:
                return
            index = MQTT_STATE["received_count"] + 1
            packet_entry = {
                "index": index,
                "topic": msg_topic,
                "message_str": msg_str,
                "message_bytes": message_bytes,
                "start_time": send_time,
                "recv_time": recv_time_value,
                "tx_time": tx_time,
            }
            MQTT_STATE["packets"].append(packet_entry)
            MQTT_STATE["total_bytes"] += message_bytes
            MQTT_STATE["total_tx_time"] += tx_time
            MQTT_STATE["received_count"] = index
            if MQTT_STATE["received_count"] >= PACKET_LIMIT:
                MQTT_STATE["done"] = True

        print(f"[MQTT #{index}] topic={msg_topic} bytes={message_bytes} tx_time={tx_time:.6f}s")

    # register callback
    client.onReciveMessage = on_message

    # keep thread alive until done
    while True:
        with STATE_LOCK:
            if MQTT_STATE["done"]:
                break
        time.sleep(0.1)




# Try to import and define CoAP server starter (best-effort)
try:
    from CoAPServer import SimpleCoAPServer
    def start_coap_server_bg():
        try:
            global COAP_SERVER
            COAP_SERVER = SimpleCoAPServer("192.168.3.4",2606)
            t = threading.Thread(target=COAP_SERVER.start, daemon=True)
            t.start()
            print("CoAP server thread started.")
        except Exception as e:
            print(f"CoAP server failed to start: {e}")
except Exception as e:
        print(f"CoAP server import failed: {e}")

# Optional MQTT broker helper (suppress if unavailable)
try:
    from sever_broker import SimpleMQTTBroker
    def start_mqtt_broker_bg(host: str = '127.0.0.1', port: int = 1883):
        try:
            global MQTT_BROKER
            if MQTT_BROKER is None:
                MQTT_BROKER = SimpleMQTTBroker(host=host, port=port)
                t = threading.Thread(target=MQTT_BROKER.start, daemon=True)
                t.start()
                print("MQTT broker thread started.")
        except Exception as e:
            print(f"MQTT broker failed to start: {e}")
except Exception as e:
    print(f"MQTT broker import failed: {e}")


INDEX_HTML = """
<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>MQTT & CoAP Packet Stats</title>
  <style>
    body { font-family: system-ui, Arial, sans-serif; margin: 24px; }
    .row { display: flex; gap: 24px; flex-wrap: wrap; }
    .col { flex: 1 1 420px; min-width: 380px; }
    .card { border: 1px solid #e0e0e0; border-radius: 8px; padding: 16px; }
    .kpi { display: grid; grid-template-columns: repeat(3, minmax(140px, 1fr)); gap: 12px; }
    .muted { color: #666; }
    table { border-collapse: collapse; width: 100%; }
    th, td { border: 1px solid #ddd; padding: 8px; }
    th { background: #fafafa; }
    canvas { max-width: 900px; }
    .resp-dark { background: #111; color: #e0ffe0; font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace; }
  </style>
  <script src=\"https://cdn.jsdelivr.net/npm/chart.js\"></script>
  <script>
    let chartMqtt;
    let chartCoap;
    let autoCoap = false;

    function renderPanel(kind, data) {
      console.log(`[DEBUG] renderPanel(${kind}):`, data);
      document.getElementById(kind+'-count').textContent = data.received_count || 0;
      document.getElementById(kind+'-bytes').textContent = data.total_bytes || 0;
      document.getElementById(kind+'-totaltime').textContent = (data.total_tx_time || 0).toFixed(6);
      document.getElementById(kind+'-aggrate').textContent = (data.aggregate_rate_bps || 0).toFixed(2);

      const labels = data.packets.map(p => p.index);
      const bytes = data.packets.map(p => p.message_bytes);
      const tx = data.packets.map(p => p.tx_time);

      const chartId = kind === 'mqtt' ? 'chartMqtt' : 'chartCoap';
      const chartRef = kind === 'mqtt' ? 'chartMqtt' : 'chartCoap';
      let chart = (kind === 'mqtt') ? chartMqtt : chartCoap;

  if (typeof Chart === 'undefined') {
    // Keep UI responsive if Chart.js CDN fails
    return;
  }
      if (!chart) {
        const ctx = document.getElementById(chartId).getContext('2d');
        chart = new Chart(ctx, {
          type: 'line',
          data: {
            labels,
            datasets: [
              {
                label: 'Bytes',
                data: bytes,
                borderColor: '#1976d2',
                backgroundColor: 'rgba(25, 118, 210, 0.15)'
              },
              {
                label: 'Tx Time (s)',
                data: tx,
                yAxisID: 'y1',
                borderColor: '#d32f2f',
                backgroundColor: 'rgba(211, 47, 47, 0.15)'
              }
            ]
          },
          options: {
            responsive: true,
            interaction: { mode: 'index', intersect: false },
            stacked: false,
            scales: {
              y: { type: 'linear', position: 'left', title: { display: true, text: 'Bytes' } },
              y1: { type: 'linear', position: 'right', grid: { drawOnChartArea: false }, title: { display: true, text: 'Tx Time (s)' } }
            }
          }
        });
        if (kind === 'mqtt') chartMqtt = chart; else chartCoap = chart;
      } else {
        chart.data.labels = labels;
        chart.data.datasets[0].data = bytes;
        chart.data.datasets[1].data = tx;
        chart.update();
      }
    }

    async function fetchStats() {
      try {
        const res = await fetch(`/stats?includeCoap=${autoCoap ? '1' : '0'}`, { cache: 'no-store' });
        if (!res.ok) { setTimeout(fetchStats, 1000); return; }
      const all = await res.json();

        const expEl = document.getElementById('exp');
        if (expEl) expEl.textContent = all.expected_count;
        const curTopicEl = document.getElementById('mqttCurrentTopic');
        if (curTopicEl && all && all.mqtt_current_topic) curTopicEl.textContent = all.mqtt_current_topic;
        const limitEl = document.getElementById('displayLimitText');
        if (limitEl && all && all.ui_display_limit) limitEl.textContent = all.ui_display_limit;
        if (all && all.mqtt) {
      renderPanel('mqtt', all.mqtt);
          // Update message table
          try {
            const curTopic = curTopicEl?.textContent || '';
            const tbody = document.getElementById('messageTableBody');
            if (tbody && Array.isArray(all.mqtt.packets)) {
              const displayLimit = all.ui_display_limit || 200;
              const items = all.mqtt.packets
                .slice(-displayLimit)  // Show last N messages based on UI_DISPLAY_LIMIT
                .reverse(); // newest first
              if (items.length > 0) {
                tbody.innerHTML = items.map(p => 
                  `<tr><td>${p.index}</td><td>${p.topic}</td><td style=\"word-break:break-all;\">${p.message_str}</td></tr>`
                ).join('');
                try {
                  // auto-scroll to bottom of table body container
                  const parent = tbody.parentElement;
                  if (parent) parent.scrollTop = parent.scrollHeight;
                } catch (e) {}
              } else {
                tbody.innerHTML = '<tr><td colspan="3" style="padding:8px; text-align:center; color:#666;">No messages for this topic</td></tr>';
              }
            }
          } catch (e) {}
        }
        if (autoCoap && all && all.coap) renderPanel('coap', all.coap);

        const intervalMs = (all && all.mqtt && all.mqtt.done && !autoCoap) ? 2000 : 500;
        setTimeout(fetchStats, intervalMs);
      } catch (e) {
        setTimeout(fetchStats, 1000);
      }
    }

    // Simulation removed

    // CoAP connect handled automatically; no manual apply

    async function fetchCoapManual() {
      try {
        const limitEl = document.getElementById('coapLimit');
        const limit = limitEl ? parseInt(limitEl.value, 10) || 10 : 10;
        const res = await fetch(`/coap_fetch?limit=${limit}`, { cache: 'no-store' });
        if (!res.ok) return;
        const data = await res.json();
        renderPanel('coap', {
          packets: data.packets,
          total_bytes: data.total_bytes,
          total_tx_time: data.total_tx_time,
          received_count: data.received_count,
          done: false,
          aggregate_rate_bps: data.aggregate_rate_bps,
        });
      } catch (e) {}
    }

    function toggleAutoCoap(ev) {
      autoCoap = ev.target.checked === true;
      if (autoCoap) {
        // kick a refresh to show live data
        fetchStats();
      }
    }

  async function sendCoapCommand() {
    try {
      const method = document.querySelector('input[name="coapMethod"]:checked')?.value || 'GET';
      const path = document.getElementById('coapCmdPath').value.trim() || '/';
      const payload = document.getElementById('coapCmdPayload').value;
      const res = await fetch('/coap_command', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ method, path, payload })
      });
      if (!res.ok) return;
      const out = await res.json();
      const box = document.getElementById('coapCmdResponse');
      box.value = JSON.stringify(out, null, 2);
    } catch (e) {}
  }

    window.addEventListener('load', () => {
      // Simulation UI removed
      const fetchBtn = document.getElementById('fetchCoap');
      if (fetchBtn) fetchBtn.addEventListener('click', fetchCoapManual);
      const autoCb = document.getElementById('autoCoap');
      if (autoCb) autoCb.addEventListener('change', toggleAutoCoap);
    const sendBtn = document.getElementById('coapCmdSend');
    if (sendBtn) sendBtn.addEventListener('click', sendCoapCommand);
    const subBtn = document.getElementById('mqttSubscribeBtn');
    if (subBtn) subBtn.addEventListener('click', async () => {
      const input = document.getElementById('mqttNewTopic');
      const msg = document.getElementById('mqttSubMsg');
      msg.textContent = '';
      const topic = (input?.value || '').trim();
      if (!topic) { msg.textContent = 'Topic is empty'; return; }
      try {
        const res = await fetch('/mqtt_subscribe', {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ topic })
        });
        const out = await res.json();
        if (out.ok) {
          document.getElementById('mqttCurrentTopic').textContent = out.topic || topic;
          msg.textContent = 'Subscribed';
        } else {
          msg.textContent = 'Failed: ' + (out.error || 'unknown');
        }
      } catch (e) { msg.textContent = 'Error'; }
    });
    const pubBtn = document.getElementById('pubSend');
    if (pubBtn) pubBtn.addEventListener('click', async () => {
      const topicEl = document.getElementById('pubTopic');
      const payloadEl = document.getElementById('pubPayload');
      const statusEl = document.getElementById('pubStatus');
      statusEl.textContent = '';
      let payload;
      const raw = payloadEl?.value ?? '';
      // Try parse JSON; fallback to string
      try { payload = raw ? JSON.parse(raw) : ''; } catch { payload = raw; }
      const topic = (topicEl?.value || '').trim();
      try {
        const res = await fetch('/mqtt_publish', {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ topic, payload })
        });
        const out = await res.json();
        statusEl.textContent = out.ok ? `OK (${out.payload_len}B)` : `Failed: ${out.error || 'unknown'}`;
      } catch (e) { statusEl.textContent = 'Error'; }
    });
      fetchStats();
    });
  </script>
</head>
<body>
  <h2>MQTT & CoAP Packet Stats</h2>
  <div class="muted">Expected per channel: <span id="exp">0</span> packets</div>
  <div style="margin:8px 0 16px 0; display:flex; gap:12px; align-items:center;">
    <span class="muted">Fetch N:</span>
    <input id="coapLimit" type="number" value="10" min="1" style="width:80px;"/>
    <button id="fetchCoap">Fetch CoAP</button>
    <label style="display:flex; align-items:center; gap:6px;">
      <input id="autoCoap" type="checkbox"/>
      <span class="muted">Auto CoAP</span>
    </label>
  </div>

  

  <div class="row" style="margin-top:16px;">
    <div class="col card">
      <h3>MQTT</h3>
      <div class="kpi">
        <div><div class="muted">Received</div><div id="mqtt-count">0</div></div>
        <div><div class="muted">Total Bytes</div><div id="mqtt-bytes">0</div></div>
        <div><div class="muted">Total Tx Time (s)</div><div id="mqtt-totaltime">0</div></div>
      </div>
      <div class="kpi" style="margin-top:8px; grid-template-columns: repeat(1, minmax(140px, 1fr));">
        <div><div class="muted">Aggregate Rate (Bytes/s)</div><div id="mqtt-aggrate">0</div></div>
      </div>
      <canvas id="chartMqtt" width="900" height="340" style="margin-top:12px;"></canvas>

      <div class="card" style="margin-top:16px;">
        <h4>MQTT Subscribe</h4>
        <div style="display:flex; gap:12px; align-items:center; flex-wrap:wrap;">
          <span class="muted">Current:</span>
          <code id="mqttCurrentTopic">-</code>
          <input id="mqttNewTopic" placeholder="e.g. sensors/room1" style="min-width:260px;"/>
          <button id="mqttSubscribeBtn">Subscribe</button>
          <span id="mqttSubMsg" class="muted"></span>
        </div>
      </div>

      <div class="card" style="margin-top:16px;">
        <h4>Publish Message</h4>
        <div style="display:flex; gap:12px; flex-wrap:wrap; align-items:center; margin-bottom:8px;">
          <span class="muted">Topic:</span>
          <input id="pubTopic" placeholder="leave empty to use Current" style="width:260px;"/>
          <button id="pubSend">Publish</button>
          <span id="pubStatus" class="muted"></span>
        </div>
        <div>
          <div class="muted">Payload (string or JSON)</div>
          <textarea id="pubPayload" rows="6" style="width:100%;"></textarea>
        </div>
      </div>

      <div class="card" style="margin-top:16px;">
        <h4>Recent Messages</h4>
        <div class="muted" style="margin-bottom:8px;">Latest <span id="displayLimitText">200</span> messages (all topics)</div>
        <div style="max-height:220px; overflow:auto; border:1px solid #eee; border-radius:6px;">
        <table style="width:100%; font-size:12px;">
          <thead>
            <tr style="background:#f5f5f5;">
              <th style="padding:4px; border:1px solid #ddd;">#</th>
              <th style="padding:4px; border:1px solid #ddd;">Topic</th>
              <th style="padding:4px; border:1px solid #ddd;">Message</th>
            </tr>
          </thead>
          <tbody id="messageTableBody">
            <tr><td colspan="3" style="padding:8px; text-align:center; color:#666;">No messages yet</td></tr>
          </tbody>
        </table>
        </div>
      </div>
    </div>

    <div class="col card">
      <h3>CoAP</h3>
      <div class="kpi">
        <div><div class="muted">Received</div><div id="coap-count">0</div></div>
        <div><div class="muted">Total Bytes</div><div id="coap-bytes">0</div></div>
        <div><div class="muted">Total Tx Time (s)</div><div id="coap-totaltime">0</div></div>
      </div>
      <div class="kpi" style="margin-top:8px; grid-template-columns: repeat(1, minmax(140px, 1fr));">
        <div><div class="muted">Aggregate Rate (Bytes/s)</div><div id="coap-aggrate">0</div></div>
      </div>
      <canvas id="chartCoap" width="900" height="340" style="margin-top:12px;"></canvas>

      <div class="card" style="margin-top:16px;">
        <h4>CoAP Command</h4>
        <div style="display:flex; gap:12px; flex-wrap:wrap; align-items:center; margin-bottom:8px;">
          <label><input type="radio" name="coapMethod" value="GET" checked/> GET</label>
          <label><input type="radio" name="coapMethod" value="POST"/> POST</label>
          <label><input type="radio" name="coapMethod" value="PUT"/> PUT</label>
          <label><input type="radio" name="coapMethod" value="DELETE"/> DELETE</label>
          <span class="muted">Path:</span>
          <input id="coapCmdPath" value="/test/demo" style="width:200px;"/>
          <button id="coapCmdSend">Send</button>
        </div>
        <div>
          <div class="muted">Payload</div>
          <textarea id="coapCmdPayload" rows="6" style="width:100%;"></textarea>
        </div>
        <div style="margin-top:12px;">
          <div class="muted">Response</div>
          <textarea id="coapCmdResponse" class="resp-dark" rows="8" style="width:100%;" readonly></textarea>
        </div>
      </div>
    </div>
  </div>
</body>
</html>
"""
def main():
    # Configuration (change as needed)
    broker_host = "192.168.3.4"
    broker_port = 20904
    mqtt_topic = MQTT_TOPIC
    client_id = "web_stats_client"
    http_host = "127.0.0.1"
    http_port = 8080

    # Start HTTP server thread
    http_thread = threading.Thread(target=run_http_server, args=(http_host, http_port), daemon=True)
    http_thread.start()

    # Start embedded CoAP and MQTT broker so clients can connect locally
    # Start embedded CoAP server to accept incoming data
    global COAP_SERVER
    if COAP_SERVER is None:
        try:
            start_coap_server_bg()
        except Exception:
            pass
    # Start embedded MQTT broker on localhost:1883
    try:
        start_mqtt_broker_bg(broker_host, broker_port)
    except Exception:
        pass

    # Start real MQTT collector; CoAP handled by embedded server
    mqtt_thread = threading.Thread(target=mqtt_collect_loop, args=(broker_host, broker_port, mqtt_topic, client_id, {}), daemon=True)
    coap_thread = None

    mqtt_thread.start()
    if coap_thread is not None:
        coap_thread.start()

    print("Open the web UI:")
    print(f"  http://{http_host}:{http_port}")
    print(f"  MQTT topic: {mqtt_topic}")

    # Keep main thread alive until both channels are done
    try:
        while True:
            with STATE_LOCK:
                if MQTT_STATE["done"] and COAP_STATE["done"]:
                    break
            time.sleep(0.2)
        print("Collected all packets on both channels. UI shows final results.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting...")


if __name__ == "__main__":
    main()
