"""
main.py
--------
Main entry point for Proto Alpha 2 automation system.
Initializes hardware components, camera, and UI, then
starts the main controller.
"""

import logging
import time
from ultralytics import YOLO

from controls import LoadCell, Cutter, Turntable
from camera_controller import CameraController
from dashboard_ui import DashboardUI
from main_controller import MainController
# from order_manager import OrderManager  # if you have it

# -----------------------------------------------------------------------------
# SYSTEM SETUP
# -----------------------------------------------------------------------------
def main():
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s")

    print("Initializing system...")

    # --- Initialize UI ---
    ui = DashboardUI()

    # --- Initialize hardware ---
    try:
        load_cell = LoadCell(dout_pin=5, pd_sck_pin=6, reference_unit=1)
        cutter = Cutter()
        turntable = Turntable(numPositions=6)
        # order_manager = OrderManager()  # optional future use
    except Exception as e:
        logging.error(f"Hardware init failed: {e}")
        return

    # --- Initialize vision system ---
    try:
        model = YOLO("/home/dfarag/ficio/proto_alpha_2_code/CV_Models/pulse_check.pt")
        camera = CameraController(model=model, ui=ui)
    except Exception as e:
        logging.error(f"Camera or model init failed: {e}")
        return

    # --- Initialize main controller ---
    main_controller = MainController(
        ui=ui,
        camera=camera,
        cutter=cutter,
        load_cell=load_cell,
        turntable=turntable,
        order_manager=None  # or order_manager
    )

    # -----------------------------------------------------------------------------
    # MAIN LOOP
    # -----------------------------------------------------------------------------
    try:
        logging.info("Starting main control loop...")
        camera.start_continuous_mode()
        main_controller.run()  # or main_controller.start_loop() if you made it threaded
    except KeyboardInterrupt:
        logging.info("Shutdown requested by user.")
    except Exception as e:
        logging.error(f"Main loop error: {e}")
    finally:
        logging.info("Shutting down system...")
        try:
            camera.shutdown()
            load_cell.cleanup()
            cutter.cleanup()
            turntable.cleanup()
            # order_manager.cleanup() if applicable
        except Exception as e:
            logging.error(f"Cleanup error: {e}")
        print("System safely shut down.")

# -----------------------------------------------------------------------------
# ENTRY POINT
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    main()