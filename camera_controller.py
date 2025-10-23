import threading
import time
from PIL import Image
import cv2
from picamera2 import Picamera2
from dashboard_ui import DashboardUI
from ultralytics import YOLO

class CameraController:
    def __init__(self, model, ui, update_interval=2.0,
                 save_path="/home/dfarag/ficio/proto_alpha_2_code/CV_Images/latest.jpg"):
        self.model = model
        self.ui = ui
        self.update_interval = update_interval
        self.save_path = save_path

        self.picam2 = Picamera2()
        config = self.picam2.create_still_configuration()
        self.picam2.configure(config)
        self.picam2.start()

        self._stop_event = threading.Event()
        self._thread = None
        self._lock = threading.Lock()

        print("Attempting to autofocus...")
        success = self.picam2.autofocus_cycle()
        print("Autofocus successful!" if success else "Autofocus failed.")

    # ----------------------------------------------------------------------
    # Continuous background loop that calls get_latest_objects each cycle
    # ----------------------------------------------------------------------
    def _continuous_loop(self):
        while not self._stop_event.is_set():
            # capture under lock, then release lock for processing
            with self._lock:
                tmp_path = self.save_path
                self.picam2.capture_file(tmp_path)

            # run model and post-processing outside camera lock
            try:
                results = self.model(tmp_path)
                detections = self._parse_detections(results)
                self.annotate_image(tmp_path, detections)
            except Exception as e:
                print(f"[CameraController] Model/process failed: {e}")

            time.sleep(self.update_interval)


    # ----------------------------------------------------------------------
    # Start / Stop the continuous mode
    # ----------------------------------------------------------------------
    def start_continuous_mode(self):
        if self._thread and self._thread.is_alive():
            print("Continuous loop already running.")
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._continuous_loop, daemon=True)
        self._thread.start()
        print("Continuous camera loop started.")

    def stop_continuous_mode(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join()
        print("Continuous camera loop stopped.")

    # ----------------------------------------------------------------------
    # Take a new image and get detections
    # ----------------------------------------------------------------------
    def get_latest_objects(self, DashboardUI=None):
        # capture under lock, then process without holding lock
        with self._lock:
            tmp_path = self.save_path
            self.picam2.capture_file(tmp_path)

        results = self.model(tmp_path)
        detections = self._parse_detections(results)
        self.annotate_image(tmp_path, detections)
        if(DashboardUI is not None):
            DashboardUI.safe_update_camera_image(tmp_path)
        return detections

    # ----------------------------------------------------------------------
    # Convert YOLO output to usable detections
    # ----------------------------------------------------------------------
    def _parse_detections(self, results):
        detections = []
        try:
            for r in results[0].boxes.data.tolist():
                x1, y1, x2, y2, conf, cls = r
                detections.append({
                    "bbox": (x1, y1, x2, y2),
                    "confidence": float(conf),
                    "class_id": int(cls),
                    "label": self.model.names[int(cls)]
                })
        except Exception as e:
            print(f"[CameraController] Error parsing detections: {e}")
        return detections

    # ----------------------------------------------------------------------
    # Annotate and update GUI image
    # ----------------------------------------------------------------------
    def annotate_image(self, image_path, detections):
        """Annotate image, save, and update UI — but call UI via safe wrapper."""
        img = cv2.imread(image_path)
        if img is None:
            print(f"[CameraController] Failed to read image at {image_path}")
            return

        if detections:
            for det in detections:
                try:
                    x1, y1, x2, y2 = map(int, det["bbox"])
                    label = det["label"]
                    conf = det["confidence"]
                    text = f"{label} {conf:.2f}"
                    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 10)
                    cv2.putText(img, text, (x1, max(y1 - 10, 30)),
                                cv2.FONT_HERSHEY_SIMPLEX, 10.0, (255, 0, 100), 20)
                except Exception as e:
                    print("[CameraController] Bad detection entry:", e)
        else:
            # no objects: optionally annotate or leave image as-is
            pass

        # Save annotated image (may be heavy; it's okay outside lock)
        cv2.imwrite(self.save_path, img)

        # Update UI via a thread-safe wrapper if available, else fallback
        try:
            if hasattr(self.ui, "safe_update_camera_image"):
                self.ui.safe_update_camera_image(self.save_path)
            else:
                # fallback (risky): call directly
                self.ui.update_camera_image(self.save_path)
        except Exception as e:
            print(f"[CameraController] GUI update failed: {e}")

    # ----------------------------------------------------------------------
    # Fully stop the camera when done
    # ----------------------------------------------------------------------
    def shutdown(self):
        self.stop_continuous_mode()
        self.picam2.stop()
        print("Camera fully stopped.")

if __name__ == "__main__":
    ui = DashboardUI()

    model = YOLO("/home/dfarag/ficio/proto_alpha_2_code/CV_Models/pulse_check.pt")
    camera = CameraController(model=model, ui=ui)
    camera.start_continuous_mode()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down camera...")
        camera.shutdown()
