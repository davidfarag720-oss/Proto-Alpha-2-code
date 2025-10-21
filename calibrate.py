"""
calibrate_load_cell.py
----------------------
Simple script to compute the calibration constant (grams per raw unit)
for your HX711-based load cell setup.

Usage:
1. Run the script with nothing on the scale — it will tare automatically.
2. When prompted, place your known weight (e.g., 1235 g) on the scale.
3. It will compute and display the calibration factor.
"""

import time
import logging
from controls import LoadCell  # your class from controls.py

# ----------------------------------------------------------------------
# USER INPUT
# ----------------------------------------------------------------------
KNOWN_WEIGHT_GRAMS = 1235  # the object you’ll use for calibration
SAMPLES = 10               # number of samples to average per reading

# ----------------------------------------------------------------------
def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    print("=== Load Cell Calibration Tool ===")
    print("Ensure the scale is empty, then press Enter to start taring.")
    input("Press Enter when ready...")

    try:
        # Initialize the load cell (replace pins as needed)
        lc = LoadCell(dout_pin=5, pd_sck_pin=6)
        time.sleep(1)

        # Tare (zero) the scale
        print("Taring... please wait.")
        lc.tare()
        print("Tare complete. Reading baseline...")

        time.sleep(1)

        # Confirm baseline reading
        baseline = 0
        readings = []
        for i in range(SAMPLES):
            val = lc.get_weight(1)
            if val is not None:
                readings.append(val)
            time.sleep(0.2)
        if readings:
            baseline = sum(readings) / len(readings)
        print(f"Baseline raw average: {baseline}")

        # Ask user to place known weight
        input(f"\nNow place your {KNOWN_WEIGHT_GRAMS} g weight on the scale and press Enter.")
        time.sleep(1)

        readings = []
        for i in range(SAMPLES):
            val = lc.get_weight(1)
            if val is not None:
                readings.append(val)
            time.sleep(0.2)
        if not readings:
            print("No valid readings received — check wiring or HX711.")
            return

        avg_raw = sum(readings) / len(readings)
        print(f"Average raw reading with {KNOWN_WEIGHT_GRAMS} g: {avg_raw}")

        # Compute calibration constant
        calibration_constant = (avg_raw - baseline) / KNOWN_WEIGHT_GRAMS

        print("\n=== Calibration Complete ===")
        print(f"Calibration constant (raw units per gram): {calibration_constant:.6f}")
        print(f"Use this as your reference_unit in controls.py:")
        print(f"    reference_unit = {calibration_constant:.6f}")

        print("\nYou can test this by updating your LoadCell code to:")
        print(f"    self.scale_factor = 1.0 / {calibration_constant:.6f}")
        print("and multiplying raw readings by that factor to convert to grams.")

    except KeyboardInterrupt:
        print("\nCalibration cancelled.")
    except Exception as e:
        logging.error("Error during calibration: %s", e)
    finally:
        try:
            lc.cleanup()
        except Exception:
            pass
        print("Cleanup complete. Exiting.")

# ----------------------------------------------------------------------
if __name__ == "__main__":
    main()
