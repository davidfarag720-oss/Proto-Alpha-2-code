import time
import threading
import logging

class MainController:
    def __init__(self, ui, camera, cutter, load_cell, turntable, order_manager):
        logging.basicConfig(level=logging.INFO)
        self.ui = ui
        self.camera = camera
        self.cutter = cutter
        self.load_cell = load_cell
        self.turntable = turntable
        self.order_manager = order_manager

        self.required_ingredients: dict = {}
        self.processed_ingredients: dict = {}
        self._stop_event = threading.Event()

        # protect shared state
        self._lock = threading.Lock()

        # Tuning parameters
        self.weight_stable_threshold = 500  # grams
        self.no_change_checks = 20  # 2s (at 100ms)
        self.finish_no_change_checks = 20  # 2s (at 100ms)

        # logger
        self.logger = logging.getLogger("MainController")
    # -----------------------------
    # 🔹 Top-level Loop
    # -----------------------------
    def run(self):
        """Main control loop."""
        while not self._stop_event.is_set():
            order = self._wait_for_order()
            self._process_order(order)

    def stop(self, join_timeout=5.0):
        """Gracefully stop the controller and hardware threads."""
        self._stop_event.set()

        # Ask camera to shutdown (it handles its own thread join)
        try:
            if hasattr(self.camera, "shutdown"):
                self.camera.shutdown()
        except Exception as e:
            print("Camera shutdown failed:", e)

        # Cleanup hardware
        try:
            if hasattr(self.cutter, "cleanup"):
                self.cutter.cleanup()
        except Exception as e:
            print("Cutter cleanup failed:", e)

        try:
            if hasattr(self.load_cell, "cleanup"):
                self.load_cell.cleanup()
        except Exception as e:
            print("LoadCell cleanup failed:", e)

        try:
            if hasattr(self.turntable, "cleanup"):
                self.turntable.cleanup()
        except Exception as e:
            print("Turntable cleanup failed:", e)


    # -----------------------------
    # 🔹 Order-Level Logic
        # -----------------------------
    def _wait_for_order(self):
        """Wait until an order is available."""
        pending = self.order_manager.get_pending_orders()
        if pending:
            return pending[0]

        # No orders -> wait and allow test order creation
        self._ui_update_instructions("Waiting for orders... Click Continue to add a test order.")
        self._ui_wait_for_continue()

        # Add dummy order when Continue is pressed
        from order_manager import Ingredient
        self.order_manager.add_order("Small Fries", {Ingredient.POTATO: 100})

        # Update UI
        self.order_manager.update_ui(self.ui, self.processed_ingredients)

        return self.order_manager.get_pending_orders()[0]



    def _process_order(self, order):
        """Process all ingredients for a given order."""
        order.mark_in_progress()
        self.order_manager.update_ui(self.ui, self.processed_ingredients)

        try:
            try:
                ingredients = self.order_manager.get_order_ingredients(order)
            except TypeError:
                ingredients = self.order_manager.get_ingredients()
        except Exception:
            self.logger.exception("Failed to fetch ingredients for order %s", order)
            return

        for ingredient_enum, required_grams in ingredients.items():
            ingredient_name = ingredient_enum.value
            with self._lock:
                if ingredient_enum not in self.processed_ingredients:
                    self.processed_ingredients[ingredient_enum] = 0.0
                if ingredient_enum not in self.required_ingredients:
                    self.required_ingredients[ingredient_enum] = 0.0

            self.required_ingredients[ingredient_enum] += required_grams

            self._process_ingredient(ingredient_enum)

        self._ui_update_instructions(f"✅ Order completed: {order}")
        try:
            order.mark_completed()
            self.order_manager.update_ui(self.ui, self.processed_ingredients)
        except Exception:
            self.logger.exception("Failed to remove order")


    # -----------------------------
    # 🔹 Ingredient Processing
    # -----------------------------
    def _process_ingredient(self, ingredient_enum):
        """Process a single ingredient until required grams reached."""
        ingredient_name = ingredient_enum.value
        pre_process_weight = self.processed_ingredients[ingredient_enum]
        while (
            self.processed_ingredients[ingredient_enum] < self.required_ingredients[ingredient_enum]
            and not self._stop_event.is_set()
        ):
            self._prompt_user_to_place(ingredient_name)
            if not self._check_quality(ingredient_name):
                continue
            self._run_cutter_until_weight_reached(ingredient_enum)
        self._finish_ingredient(ingredient_enum, pre_process_weight)

    def _prompt_user_to_place(self, ingredient_name):
        """Ask user to place ingredient and wait for continue."""
        self._ui_update_instructions(f"Please place {ingredient_name} in chamber and click Continue.")
        self._ui_wait_for_continue()

    def _check_quality(self, ingredient_name):
        """Capture a fresh image, display it, and check vegetable quality."""

        self._ui_update_instructions("Analyzing vegetable quality...")
        detections = self.camera.get_latest_objects(self.ui)
        healthy = self.is_healthy(detections)

        if not healthy:
            self._ui_update_instructions(   
                f"{ingredient_name} appears unhealthy. Please replace it and click Continue."
            )
            self._ui_wait_for_continue()
        return healthy


    # -----------------------------
    # 🔹 Cutting & Weight Control
    # -----------------------------
    def _run_cutter_until_weight_reached(self, ingredient_enum):
        """Run cutter and monitor weight until target reached or stall detected."""
        ingredient_name = ingredient_enum.value
        self._ui_update_instructions(f"Processing {ingredient_name}...")
        # ensure cutter is deactivated on error/exit
        try:
            self.cutter.activate()
        except Exception:
            self.logger.exception("Failed to activate cutter")
            return

        last_weight = self.load_cell.get_weight() or 0.0
        if last_weight is not None:
            self.ui.safe_update_scale_reading(last_weight)
        no_change_count = 0

        try:
            while not self._stop_event.is_set():
                time.sleep(0.1)
                w = self.load_cell.get_weight(samples=1)
                if w is not None:
                    self.ui.safe_update_scale_reading(w)
                # robust fallback
                if w is None:
                    w = last_weight

                # avoid spurious negative readings or huge jumps: clip delta
                delta = w - last_weight
                if delta < 0:
                    # negative delta: sensor jitter — ignore but don't count as progress
                    delta = 0.0

                # if delta looks unrealistically large, log and clamp
                if delta > 5000:  # arbitrary large threshold; tune as needed
                    self.logger.warning("Suspicious weight jump detected: %s", delta)
                    delta = 0.0

                if delta >= self.weight_stable_threshold:
                    # update processed_ingredients safely
                    with self._lock:
                        self.processed_ingredients[ingredient_enum] = (
                            self.processed_ingredients.get(ingredient_enum, 0.0) + delta
                        )
                    no_change_count = 0
                else:
                    no_change_count += 1

                last_weight = w

                # Check completion
                with self._lock:
                    processed = self.processed_ingredients.get(ingredient_enum, 0.0)
                if processed >= self.required_ingredients[ingredient_enum]:
                    # we reached the requested grams
                    try:
                        self.cutter.deactivate()
                    except Exception:
                        self.logger.exception("Failed to deactivate cutter on completion")
                    self._rotate_turntable()
                    # Wait for output to settle
                    self._resume_until_stable()
                    break

                # Detect stall (no weight change)
                if no_change_count >= self.no_change_checks:
                    try:
                        self.cutter.deactivate()
                    except Exception:
                        self.logger.exception("Failed to deactivate cutter on stall")
                    self._ui_update_instructions(
                        f"No weight increase detected. Please add more {ingredient_name} and click Continue."
                    )
                    self._ui_wait_for_continue()
                    # Restart full loop for this ingredient
                    return
        finally:
            # ensure cutter is off even on exceptions or stop
            try:
                self.cutter.deactivate()
            except Exception:
                pass

    def _resume_until_stable(self):
        """Run cutter briefly until output stabilizes."""
        try:
            self.cutter.activate()
        except Exception:
            self.logger.exception("Failed to activate cutter for resume")
            return

        stable_count = 0
        last = self.load_cell.get_weight() or 0.0
        self.ui.safe_update_scale_reading(last)
        self._ui_update_instructions("Finalizing... please wait.")

        try:
            while stable_count < self.finish_no_change_checks and not self._stop_event.is_set():
                time.sleep(0.1)
                w = self.load_cell.get_weight(samples=1)
                self.ui.safe_update_scale_reading(w)
                if w is None:
                    w = last
                if abs(w - last) < self.weight_stable_threshold:
                    stable_count += 1
                else:
                    stable_count = 0
                last = w
        finally:
            try:
                self.cutter.deactivate()
            except Exception:
                self.logger.exception("Failed to deactivate cutter after resume")

    def _rotate_turntable(self):
        """Dummy turntable rotation."""
        self._ui_update_instructions("Rotating turntable...")
        next_pos = (self.turntable.currentPosition + 1) % self.turntable.numPositions
        self.turntable.moveToPosition(next_pos)
        self.turntable.currentPosition = next_pos

    def _finish_ingredient(self, ingredient_enum, pre_process_weight):
        """Update GUI and confirm done."""
        grams = self.processed_ingredients[ingredient_enum] - pre_process_weight
        self._ui_update_instructions(f"{ingredient_enum.value} processed: {grams:.1f}g. Please collect it.")
        self._ui_wait_for_continue()

    # -----------------------------
    # 🔹 Utility
    # -----------------------------
    def is_healthy(self, detections):
        """Dummy logic: Assume healthy if 'potato' or 'healthy' detected in any label."""
        if not detections:
            return False
        try:
            for obj in detections:
                s = str(obj).lower()
                if "unhealthy" in s:
                    return False
            return True
        except Exception:
            self.logger.exception("Error while evaluating detections")
            return False

    # -----------------------------
    # UI helper wrappers (thread-safe if DashboardUI supports it)
    # -----------------------------
    def _ui_update_instructions(self, text):
        if hasattr(self.ui, "safe_update_instructions"):
            self.ui.safe_update_instructions(text)
        else:
            # fallback: best-effort direct call (only safe if controller runs off the main thread)
            try:
                self.ui.update_instructions(text)
            except Exception:
                # as a last resort, schedule via `after` if UI exposes root
                try:
                    if hasattr(self.ui, "root") and hasattr(self.ui.root, "after"):
                        self.ui.root.after(0, lambda: self.ui.update_instructions(text))
                except Exception as e:
                    self.logger.exception("Failed to update GUI instructions: %s", e)
    def _ui_wait_for_continue(self, timeout=None):
        """
        Wait for the UI continue action. If UI exposes a blocking `wait_for_continue` this will use it.
        If the UI provides a non-blocking API, you may need to adapt this.
        Optional timeout (seconds) can be used if you want a backstop.
        """
        try:
            if timeout is None:
                return self.ui.wait_for_continue()
            # some UIs support a timeout arg; try it
            return self.ui.wait_for_continue(timeout=timeout)
        except TypeError:
            # ui.wait_for_continue doesn't accept timeout
            # emulate with polling (not ideal but prevents locking forever if you want a timeout)
            if timeout is None:
                return self.ui.wait_for_continue()
            deadline = time.time() + timeout
            while time.time() < deadline and not self._stop_event.is_set():
                # UI's wait_for_continue probably blocks, so we try simple sleep fallback
                time.sleep(0.1)
            return False
        except Exception:
            self.logger.exception("wait_for_continue failed")
            return False