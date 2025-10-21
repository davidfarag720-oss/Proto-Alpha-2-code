import time
import threading
import tkinter as tk
from ultralytics import YOLO

from dashboard_ui import DashboardUI
from camera_controller import CameraController

def main():
    button_event = threading.Event()

    def handle_complete_click():
        print("✅ Complete button clicked. Handling order completion...")
        button_event.set()
    
    
    # --- Initialize GUI ---
    root = tk.Tk()
    ui = DashboardUI(root, on_complete_click=handle_complete_click)

    # --- Load YOLO model ---
    print("Loading YOLO model...")
    model = YOLO("/home/dfarag/ficio/proto_alpha_2_code/CV_Models/pulse_check.pt")

    # --- Initialize Camera Controller ---
    camera = CameraController(
        model=model,
        ui=ui,
        update_interval=3.0,  # seconds between updates
    )

    # --- Start continuous mode in background ---
    camera.start_continuous_mode()
    print("📸 Continuous camera mode started.")

    # --- Schedule a test action after a few seconds ---
    def test_capture():
        print("\n🔍 Requesting manual object detection...")
        objects = camera.get_latest_objects()
        print("Detected objects:", objects)
        ui.update_instructions("Manual detection complete!")

    # Run the test after 10 seconds (in a separate thread so it doesn't block the GUI)
    threading.Timer(10.0, test_capture).start()

    # --- Graceful shutdown when window closes ---
    def on_close():
        print("\n🛑 Shutting down...")
        camera.shutdown()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)

    # --- Start GUI loop ---
    root.mainloop()


if __name__ == "__main__":
    main()
