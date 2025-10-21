"""
controls.py
------------
This file contains the hardware control functions.

Currently Supports:
- Load Cell (HX711)
"""

import time
import logging
import threading
try:
    import paho.mqtt.client as mqtt
except ImportError:
    mqtt = None
    logging.warning("download paho-mqtt for MQTT functionality.")

try:
    from hx711 import HX711
except ImportError:
    HX711 = None
    logging.warning("HX711 library not found. Load cell functionality will be disabled.")

try:
    import RPi.GPIO as GPIO
except ImportError:
    GPIO = None
    logging.warning("RPi.GPIO not found. GPIO cleanup will be skipped.")

class LoadCell:
    """Class to interface with HX711 load cell amplifier."""

    def __init__(self, dout_pin, pd_sck_pin, reference_unit=1.0):
        if HX711 is None:
            raise ImportError("HX711 library is not available on this system.")

        self.hx = HX711(dout_pin, pd_sck_pin)
        self._lock = threading.Lock()
        self._powered = True
        self.reference_unit = reference_unit
        self.offset = 0

        self.hx.reset()
        self.tare()
        logging.info(f"LoadCell initialized (DOUT={dout_pin}, SCK={pd_sck_pin}, ref={reference_unit})")

    def _flatten(self, data):
        """Recursively flatten any nested lists into a 1D list of numbers."""
        if isinstance(data, list):
            flattened = []
            for item in data:
                flattened.extend(self._flatten(item))
            return flattened
        else:
            return [data]

    def tare(self, samples=15):
        """Manually tare the load cell by averaging multiple raw readings."""
        try:
            with self._lock:
                readings = []
                for _ in range(samples):
                    val = self.hx.get_raw_data()
                    if val is not None:
                        readings.extend(self._flatten(val))
                    time.sleep(0.05)
                if readings:
                    self.offset = sum(readings) / len(readings)
                    logging.info(f"LoadCell tared with offset={self.offset:.2f}")
                else:
                    logging.warning("No valid readings for tare.")
        except Exception as e:
            logging.error("Error during tare: %s", e)

    def calibrate(self, known_weight_grams, samples=15):
        """Calibrate reference unit using a known weight."""
        try:
            with self._lock:
                readings = []
                for _ in range(samples):
                    val = self.hx.get_raw_data()
                    if val is not None:
                        readings.extend(self._flatten(val))
                    time.sleep(0.05)
                if readings:
                    avg_val = sum(readings) / len(readings)
                    raw_value = avg_val - self.offset
                    if raw_value != 0:
                        self.reference_unit = known_weight_grams / raw_value
                        logging.info(f"Calibration complete. Reference unit = {self.reference_unit:.6f}")
                    else:
                        logging.warning("Calibration failed: zero raw value.")
                else:
                    logging.warning("No valid readings for calibration.")
        except Exception as e:
            logging.error("Error during calibration: %s", e)

    def get_weight(self, samples=5):
        """Read averaged, tared, and calibrated weight from the load cell."""
        try:
            with self._lock:
                readings = []
                for _ in range(samples):
                    val = self.hx.get_raw_data()
                    if val is not None:
                        readings.extend(self._flatten(val))
                    time.sleep(0.02)
                if not readings:
                    return None
                avg_val = sum(readings) / len(readings)
                net_val = avg_val - self.offset
                weight_grams = net_val * self.reference_unit
            return round(weight_grams, 2)
        except Exception as e:
            logging.error("Error reading weight: %s", e)
            return None

    def cleanup(self):
        """Power down and clean up GPIO pins."""
        try:
            with self._lock:
                self.hx.power_down()
                self._powered = False
            if GPIO:
                GPIO.cleanup()
            logging.info("LoadCell powered down and GPIO cleaned up.")
        except Exception as e:
            logging.error("Error powering down HX711: %s", e)

# Dummy implementations for other hardware (unchanged)

# MQTT broker settings
BROKER = "192.168.1.100"     # Your MQTT broker IP
PORT = 1883
TOPIC = "shellies/shellyplug/relay/0/command"
class Cutter:
    
    """Class to interface with a cutting hardware device."""

    def __init__(self, BROKER=BROKER, PORT=PORT, TOPIC=TOPIC):
        self.broker = BROKER
        self.port = PORT
        self.topic = TOPIC
        self.client = mqtt.Client() if mqtt else None
        logging.info("Cutter initialized.")

    def connect(self):
        self.client.connect(self.broker, self.port, 60)
        self.client.loop_start()
        logging.info("Cutter MQTT connected.")
    def activate(self):
        if self.client:
            self.client.publish(self.topic, "ON")
        logging.info("Cutter activated.")
    def deactivate(self):
        if self.client:
            self.client.publish(self.topic, "OFF")
        logging.info("Cutter deactivated.")

    def cleanup(self):
        self.client.loop_stop()
        self.client.disconnect()
        logging.info("Cutter GPIO cleaned up.")


class Turntable:
    """Class to interface with a turntable hardware device."""

    def __init__(self, numPositions: int):
        self.currentPosition = 0
        self.numPositions = numPositions
        logging.info("Turntable initialized.")

    def moveToPosition(self, position: int):
        logging.info(f"Turntable moving to position {position}.")

    def cleanup(self):
        logging.info("Turntable GPIO cleaned up.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    load_cell = None
    try:
        load_cell = LoadCell(dout_pin=5, pd_sck_pin=6)
        print("Taring load cell, please wait...")
        load_cell.tare()
        print("Tare complete.")

        # Optional: place a known weight and calibrate
        # load_cell.calibrate(known_weight_grams=100.0)

        print("Press Ctrl+C to exit.")
        while True:
            weight = load_cell.get_weight(samples=5)
            if weight is not None:
                print(f"Weight: {weight:.2f} g      \r", end="")
            else:
                print("Failed to read weight. Retrying...\r", end="")
            time.sleep(0.1)

    except (KeyboardInterrupt, SystemExit):
        print("\nMeasurement stopped by user.")
    except ImportError as e:
        logging.error("LoadCell test failed: %s", e)
        print("Please install the required HX711 library.")
    except Exception as e:
        logging.error("An error occurred during the test: %s", e)
    finally:
        if load_cell:
            load_cell.cleanup()
        print("Script finished.")
