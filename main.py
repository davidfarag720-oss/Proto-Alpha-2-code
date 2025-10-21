"""
main.py
--------
Main entry point for Proto Alpha 2 automation system.
Initializes hardware components, camera, and UI, then
starts the main controller.
"""

import logging
import threading
import time
from ultralytics import YOLO

from controls import LoadCell, Cutter, Turntable
from camera_controller import CameraController
from dashboard_ui import DashboardUI
from main_flow import MainController
from order_manager import Ingredient, OrderManager


def main():
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s")

    print("Initializing system...")

    # --- Initialize UI (must be in main thread) ---
    ui = DashboardUI()

    # --- Initialize hardware ---
    try:
        load_cell = LoadCell(dout_pin=5, pd_sck_pin=6)
        cutter = Cutter()
        turntable = Turntable(numPositions=6)
        order_manager = OrderManager()
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

    order_manager.add_order("Potato Order", {Ingredient.POTATO: 150})

    # --- Initialize main controller ---
    main_controller = MainController(
        ui=ui,
        camera=camera,
        cutter=cutter,
        load_cell=load_cell,
        turntable=turntable,
        order_manager=order_manager
    )

    # -------------------------------------------------------------------------
    # THREAD SETUP
    # -------------------------------------------------------------------------
    def controller_thread_fn():
        """Run the main control logic on a background thread."""
        try:
            logging.info("Controller thread started.")
            camera.start_continuous_mode()
            main_controller.run()
        except Exception as e:
            logging.exception(f"Main controller error: {e}")
        finally:
            logging.info("Controller thread exiting...")

    controller_thread = threading.Thread(target=controller_thread_fn, daemon=True)
    controller_thread.start()

    # -------------------------------------------------------------------------
    # MAIN THREAD: run Tkinter GUI
    # -------------------------------------------------------------------------
    try:
        logging.info("Starting GUI mainloop...")
        ui.root.mainloop()  # <-- GUI stays open and responsive here
    except KeyboardInterrupt:
        logging.info("GUI interrupted by user.")
    finally:
        logging.info("Shutting down system...")
        main_controller.stop()
        camera.shutdown()
        load_cell.cleanup()
        cutter.cleanup()
        turntable.cleanup()
        logging.info("System safely shut down.")


if __name__ == "__main__":
    main()