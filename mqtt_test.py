"""
shelly_test.py
---------------
Simple test for controlling a Shelly Gen 2 Plug via MQTT.

Requires:
    pip install paho-mqtt
"""

import json
import time
import logging
import paho.mqtt.client as mqtt

# ========== Configuration ==========
BROKER = "10.42.0.1"         # IP address of your MQTT broker (your Pi or PC)
TOPIC = "shellyp/rpc"        # Topic prefix (from your Shelly's MQTT settings)
CLIENT_ID = "shelly_test"    # Arbitrary client ID for MQTT session
# ===================================

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.info("✅ Connected to MQTT broker.")
        client.subscribe("shellyp/events/rpc")  # listen for responses
    else:
        logging.error(f"Connection failed with code {rc}")

def on_message(client, userdata, msg):
    logging.info(f"📩 Message on {msg.topic}: {msg.payload.decode()}")

def main():
    client = mqtt.Client(CLIENT_ID)
    client.on_connect = on_connect
    client.on_message = on_message

    # Connect to the broker
    client.connect(BROKER, 1883, 60)
    client.loop_start()

    time.sleep(1)

    # --- Turn ON ---
    on_payload = {
        "id": 1,
        "src": CLIENT_ID,
        "method": "Switch.Set",
        "params": {"id": 0, "on": True}
    }
    logging.info("⚙️ Turning ON Shelly Plug...")
    client.publish(TOPIC, json.dumps(on_payload))

    time.sleep(3)

    # --- Turn OFF ---
    off_payload = {
        "id": 2,
        "src": CLIENT_ID,
        "method": "Switch.Set",
        "params": {"id": 0, "on": False}
    }
    logging.info("⚙️ Turning OFF Shelly Plug...")
    client.publish(TOPIC, json.dumps(off_payload))

    # Give it a moment to respond
    time.sleep(2)

    client.loop_stop()
    client.disconnect()
    logging.info("✅ Test complete. Disconnected.")

if __name__ == "__main__":
    main()
