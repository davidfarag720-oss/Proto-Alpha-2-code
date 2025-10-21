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
        """
        Initialize the load cell.

        Args:
            dout_pin (int): GPIO pin connected to HX711 DOUT.
            pd_sck_pin (int): GPIO pin connected to HX711 SCK.
            reference_unit (float): Calibration factor (grams per raw unit).
        """
        if HX711 is None:
            raise ImportError("HX711 library is not available on this system.")

        self.hx = HX711(dout_pin, pd_sck_pin)
        self._lock = threading.Lock()
        self._powered = True
        self.reference_unit = reference_unit
        self.offset = 0  # manual tare offset

        self.hx.reset()
        self.tare()
        logging.info(f"LoadCell initialized (DOUT={dout_pin}, SCK={pd_sck_pin}, ref={reference_unit})")

    def tare(self, samples=15):
        """
        Manually tare the load cell by averaging a few readings.
        """
        try:
            with self._lock:
                readings = []
                for _ in range(samples):
                    val = self.hx.get_raw_data()
                    if val is not None:
                        readings.append(val)
                    time.sleep(0.05)
                if readings:
                    self.offset = sum(readings) / len(readings)
                    logging.info(f"LoadCell tared with offset={self.offset:.2f}")
                else:
                    logging.warning("No valid readings for tare.")
        except Exception as e:
            logging.error("Error during tare: %s", e)

    def calibrate(self, known_weight_grams, samples=15):
        """
        Calibrate the reference unit using a known weight.

        Args:
            known_weight_grams (float): The known weight placed on the scale.
        """
        try:
            with self._lock:
                readings = []
                for _ in range(samples):
                    val = self.hx.get_raw_data()
                    if val is not None:
                        readings.append(val)
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
        """
        Read averaged, tared, and calibrated weight from the load cell.
        """
        try:
            with self._lock:
                readings = []
                for _ in range(samples):
                    val = self.hx.get_raw_data()
                    if val is not None:
                        readings.append(val)
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
class Cutter:
    """Class to interface with a cutting hardware device."""

    def __init__(self):
        logging.info("Cutter initialized.")

    def activate(self):
        logging.info("Cutter activated.")

    def deactivate(self):
        logging.info("Cutter deactivated.")

    def cleanup(self):
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