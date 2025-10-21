"""
shelly_test.py
---------------
Control a Shelly Gen 2 Plug via MQTT using the modern Paho MQTT v2 API.

Requirements:
    pip install paho-mqtt
"""

import json
import time
import logging
import paho.mqtt.client as mqtt

# ======= CONFIGURATION =======
BROKER = "10.42.0.1"       # Your Mosquitto broker or Raspberry Pi IP
PORT = 1883
TOPIC_RPC = "shellyp/rpc"  # From your Shelly MQTT settings
TOPIC_EVENTS = "shellyp/events/rpc"
CLIENT_ID = "shelly_test"
# ==============================

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


# --- Callback Handlers (using v2 signature) ---

def on_connect(client, userdata, flags, reason_code, properties):
    """Called when the client connects to the broker."""
    if reason_code == 0:
        logging.info("✅ Connected to MQTT broker.")
        client.subscribe(TOPIC_EVENTS)
    else:
        logging.error(f"Failed to connect. Reason code: {reason_code}")

def on_message(client, userdata, message):
    """Called when a subscribed message is received."""
    try:
        payload = message.payload.decode()
        logging.info(f"📩 [{message.topic}] {payload}")
    except Exception as e:
        logging.error(f"Error decoding message: {e}")

def main():
    # Create MQTT client using the new callback API
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, CLIENT_ID)
    client.on_connect = on_connect
    client.on_message = on_message

    logging.info("🔌 Connecting to broker...")
    client.connect(BROKER, PORT, 60)
    client.loop_start()

    time.sleep(1)

    # --- Turn ON the Shelly Plug ---
    on_payload = {
        "id": 1,
        "src": CLIENT_ID,
        "method": "Switch.Set",
        "params": {"id": 0, "on": True}
    }
    logging.info("⚙️ Turning ON Shelly Plug...")
    client.publish(TOPIC_RPC, json.dumps(on_payload))

    time.sleep(3)

    # --- Turn OFF the Shelly Plug ---
    off_payload = {
        "id": 2,
        "src": CLIENT_ID,
        "method": "Switch.Set",
        "params": {"id": 0, "on": False}
    }
    logging.info("⚙️ Turning OFF Shelly Plug...")
    client.publish(TOPIC_RPC, json.dumps(off_payload))

    time.sleep(2)

    client.loop_stop()
    client.disconnect()
    logging.info("✅ Test complete and disconnected.")

if __name__ == "__main__":
    main()
