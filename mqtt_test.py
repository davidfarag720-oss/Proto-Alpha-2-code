import paho.mqtt.client as mqtt
import time
import logging
from controls import Cutter

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    try:
        plug = Cutter()
        plug.connect()
        logging.info("Testing Shelly MQTT control...")

        logging.info("Turning ON plug for 3 seconds...")
        plug.activate()
        time.sleep(10)

        logging.info("Turning OFF plug...")
        plug.deactivate()

    except Exception as e:
        logging.error(f"Error during MQTT test: {e}")

    finally:
        plug.cleanup()
        logging.info("MQTT test finished. Cutter cleaned up.")