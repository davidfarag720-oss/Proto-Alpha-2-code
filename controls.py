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


class LoadCell:
    """Class to interface with HX711 load cell amplifier."""

    def __init__(self, dout_pin, pd_sck_pin, reference_unit=1):
        """
        Initialize the load cell.

        Args:
            dout_pin (int): GPIO pin connected to HX711 DOUT.
            pd_sck_pin (int): GPIO pin connected to HX711 SCK.
            reference_unit (float): Calibration factor (grams per raw unit).
        """
        if HX711 is None:
            raise ImportError("HX711 library is not available on this system.")

        self.hx = HX711(dout=dout_pin, pd_sck=pd_sck_pin)
        self.hx.set_reading_format("MSB", "MSB")
        self.hx.set_reference_unit(reference_unit)
        self._lock = threading.Lock()
        self._powered = True
        self.hx.reset()
        self.hx.tare()
        logging.info(f"LoadCell initialized (DOUT={dout_pin}, SCK={pd_sck_pin}, ref={reference_unit})")

    def get_weight(self, samples=5):
        """
        Read averaged weight from the load cell.
        Thread-safe and avoids repeated power cycling.
        """
        try:
            with self._lock:
                weight = self.hx.get_weight(samples)
            return round(weight, 2)
        except Exception as e:
            logging.error("Error reading weight: %s", e)
            return None

    def tare(self):
        try:
            with self._lock:
                self.hx.tare()
            logging.info("LoadCell tared.")
        except Exception as e:
            logging.error("Error during tare: %s", e)

    def cleanup(self):
        try:
            with self._lock:
                self.hx.power_down()
                self._powered = False
            logging.info("LoadCell powered down.")
        except Exception as e:
            logging.error("Error powering down HX711: %s", e)

class Cutter:
    """Class to interface with a cutting hardware device."""

    # Currently a dummy implementation


    def __init__(self):
        """
        Initialize the cutter.
        """
        logging.info("Cutter initialized.")
    def activate(self):
        """Activate the cutter."""
        logging.info("Cutter activated.")

    def deactivate(self):
        """Deactivate the cutter."""
        logging.info("Cutter deactivated.")

    def cleanup(self):
        """Cleanup GPIO resources."""
        logging.info("Cutter GPIO cleaned up.")

class Turntable:
    """Class to interface with a turntable hardware device."""

    # Currently a dummy implementation
    # 360 degrees divided into numPositions, 

    def __init__(self, numPositions: int):
        """
        Initialize the turntable.
        """
        self.currentPosition = 0
        self.numPositions = numPositions
        logging.info("Turntable initialized.")

    def moveToPosition(self, position: int):
        """Move the turntable to a specific position."""
        logging.info(f"Turntable moving to position {position}.")

    def cleanup(self):
        """Cleanup GPIO resources."""
        logging.info("Turntable GPIO cleaned up.")