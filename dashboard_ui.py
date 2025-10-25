import time
import tkinter as tk
import threading
from tkinter import ttk
from PIL import Image, ImageTk


class DashboardUI:
    def __init__(self, on_continue_click=None):
        self.on_continue_click = on_continue_click
        self.continue_event = threading.Event()
        self.root = tk.Tk()
        self.root.title("Smart Veggie Station")
        self.root.configure(bg="#1E1E1E")
        self.root.geometry("1200x700")

        # Store references to each content area
        self.sections = {}

        self.setup_grid()
        self.create_sections()
        self.create_continue_button()

    # --------------------------------------------------
    # Layout
    # --------------------------------------------------
    def setup_grid(self):
        """Define grid layout: 2 rows (top large, bottom split), 2 columns."""
        self.root.rowconfigure(0, weight=3, uniform="row")  # Top (CV Results)
        self.root.rowconfigure(1, weight=1, uniform="row")  # Bottom (Progress + Instructions)
        self.root.columnconfigure(0, weight=1, uniform="col")
        self.root.columnconfigure(1, weight=1, uniform="col")

    def section(self, parent, title, icon_path=None):
        """Reusable section with title + optional icon."""
        frame = ttk.Frame(parent, padding=10)
        frame.grid_propagate(False)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)

        header_frame = tk.Frame(frame, bg="#2C2C2C")
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        header_frame.columnconfigure(1, weight=1)

        if icon_path:
            icon_img = Image.open(icon_path).resize((28, 28))
            icon = ImageTk.PhotoImage(icon_img)
            icon_label = tk.Label(header_frame, image=icon, bg="#2C2C2C")
            icon_label.image = icon
            icon_label.grid(row=0, column=0, padx=(5, 10))

        title_label = tk.Label(header_frame, text=title, bg="#2C2C2C",
                               fg="white", font=("Segoe UI", 14, "bold"))
        title_label.grid(row=0, column=1, sticky="w")

        content = tk.Frame(frame, bg="#333333")
        content.grid(row=1, column=0, sticky="nsew")

        return frame, content

    # --------------------------------------------------
    # Sections
    # --------------------------------------------------
    def create_sections(self):
        icons = {
            "camera": "icons/camera.png",
            "ingredients": "icons/ingredients.png",
            "instructions": "icons/instructions.png"
        }

        # --- CV RESULTS (Top, spans full width)
        cam_frame, cam_content = self.section(self.root, "CV Results", icons["camera"])
        cam_frame.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=8, pady=8)
        self.sections["camera"] = cam_content
        self.cam_label = tk.Label(cam_content, bg="black")
        self.cam_label.pack(expand=True, fill="both", padx=10, pady=10)
        self.cam_image_ref = None  # prevent GC

        # --- INGREDIENT PROGRESS (Bottom Left)
        ing_frame, ing_content = self.section(self.root, "Ingredient Progress", icons["ingredients"])
        ing_frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=8)
        self.sections["ingredients"] = ing_content
        self.ing_label = tk.Label(
            ing_content,
            text="",
            bg="#333333",
            fg="white",
            font=("Segoe UI", 24, "bold"),
            justify="center",
            anchor="center"
        )
        self.ing_label.pack(expand=True, fill="both", padx=10, pady=10)

        # --- INSTRUCTIONS (Bottom Right)
        inst_frame, inst_content = self.section(self.root, "Instructions", icons["instructions"])
        inst_frame.grid(row=1, column=1, sticky="nsew", padx=8, pady=8)
        self.sections["instructions"] = inst_content
        self.inst_label = tk.Label(
            inst_content,
            text="",
            bg="#333333",
            fg="white",
            font=("Segoe UI", 14),
            wraplength=250,
            justify="left"
        )
        self.inst_label.pack(anchor="w", fill="both", padx=10, pady=10)

    # --------------------------------------------------
    # Continue button
    # --------------------------------------------------
    def create_continue_button(self):
        self.continue_btn = tk.Button(
            self.root,
            text="Continue",
            bg="#00C7A5",
            fg="white",
            font=("Segoe UI", 12, "bold"),
            borderwidth=0,
            relief="flat",
            command=self._internal_on_continue_click
        )
        self.continue_btn.place(relx=0.95, rely=0.95, anchor="se")

    def _internal_on_continue_click(self):
        try:
            self.continue_event.set()
        except Exception:
            pass

        if callable(self.on_continue_click):
            try:
                self.on_continue_click()
            except Exception as e:
                print("Error in on_continue_click callback:", e)

    def wait_for_continue(self, timeout=None):
        self.continue_event.clear()
        return self.continue_event.wait(timeout=timeout)

    # --------------------------------------------------
    # Update Functions
    # --------------------------------------------------
    def update_ingredients(self, text):
        self.ing_label.config(text=text)

    def update_instructions(self, text):
        self.inst_label.config(text=text)

    def update_camera_image(self, image_path):
        try:
            img = Image.open(image_path)
            w = max(self.cam_label.winfo_width(), 1)
            h = max(self.cam_label.winfo_height(), 1)
            img_ratio = img.width / img.height
            target_ratio = w / h

            if img_ratio > target_ratio:
                new_w, new_h = w, int(w / img_ratio)
            else:
                new_h, new_w = h, int(h * img_ratio)

            img = img.resize((new_w, new_h), Image.LANCZOS)
            background = Image.new("RGB", (w, h), color=(0, 0, 0))
            offset = ((w - new_w) // 2, (h - new_h) // 2)
            background.paste(img, offset)

            photo = ImageTk.PhotoImage(background)
            self.cam_label.config(image=photo)
            self.cam_image_ref = photo
        except Exception as e:
            print(f"Error loading image: {e}")

    # --------------------------------------------------
    # Thread-safe wrappers
    # --------------------------------------------------
    def _schedule(self, fn, *args, **kwargs):
        try:
            self.root.after(0, lambda: fn(*args, **kwargs))
        except Exception as e:
            print("Failed to schedule GUI update:", e)

    def safe_update_instructions(self, text):
        self._schedule(self.update_instructions, text)

    def safe_update_camera_image(self, image_path):
        self._schedule(self.update_camera_image, image_path)

    def safe_update_ingredients(self, text):
        self._schedule(self.update_ingredients, text)

    # --------------------------------------------------
    # Instruction Highlighting
    # --------------------------------------------------
    def highlight_instructions(self, color="#AA0000"):
        try:
            self.inst_label.config(bg=color)
            parent = self.inst_label.master
            parent.config(bg=color)
        except Exception as e:
            print(f"Failed to highlight instructions: {e}")

    def reset_instructions_highlight(self):
        try:
            self.inst_label.config(bg="#333333")
            parent = self.inst_label.master
            parent.config(bg="#333333")
        except Exception as e:
            print(f"Failed to reset instructions highlight: {e}")

    # --------------------------------------------------
    # Optional Complete handler
    # --------------------------------------------------
    def complete_click_handler(self):
        cb = getattr(self, "on_complete_click", None)
        if callable(cb):
            try:
                cb()
            except Exception as e:
                print("Error in on_complete_click callback:", e)


# --- Test Run ---
if __name__ == "__main__":
    ui = DashboardUI()
    ui.safe_update_ingredients("Potato: 1345/2500 g")
    ui.safe_update_instructions("Please place the next potato under the camera.")
    ui.root.mainloop()