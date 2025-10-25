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
        self.safe_update_status("#00AA00")  # Example: green status


    # --------------------------------------------------
    # Layout
    # --------------------------------------------------
    def setup_grid(self):
        """Define main window grid layout: 
        - Row 0: Ingredient Progress + Instructions
        - Row 1: Status panel + Camera feed
        """
        self.root.rowconfigure(0, weight=1, uniform="row")  # Top: Progress + Instructions
        self.root.rowconfigure(1, weight=3, uniform="row")  # Bottom: Status + Camera
        self.root.columnconfigure(0, weight=1, uniform="col")
        self.root.columnconfigure(1, weight=1, uniform="col")

    def section(self, parent, title, icon_path=None):
        """Create a reusable framed section with a header and optional icon."""
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
        """Create all UI panels: progress, instructions, camera, and status."""
        icons = {
            "camera": "/home/dfarag/ficio/proto_alpha_2_code/icons/camera.png",
            "ingredients": "/home/dfarag/ficio/proto_alpha_2_code/icons/ingredients.png",
            "instructions": "/home/dfarag/ficio/proto_alpha_2_code/icons/instructions.png"
        }

        # Bottom half: status (left) + camera feed (right)
        bottom_frame = tk.Frame(self.root, bg="#1E1E1E")
        bottom_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=8, pady=8)
        bottom_frame.columnconfigure(0, weight=1)
        bottom_frame.columnconfigure(1, weight=4)
        bottom_frame.rowconfigure(0, weight=1)

        # --- STATUS PANEL (bottom-left, with title and border)
        status_outer = tk.LabelFrame(
            bottom_frame,
            text="Status",
            fg="white",
            bg="#1E1E1E",
            font=("Segoe UI", 14, "bold"),
            labelanchor="n",
            bd=3,
            relief="groove"
        )
        status_outer.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self.status_frame = tk.Frame(status_outer, bg="#444444")
        self.status_frame.pack(expand=True, fill="both", padx=5, pady=5)
        self.sections["status"] = self.status_frame

        # --- CV RESULTS (bottom-right)
        cam_frame, cam_content = self.section(bottom_frame, "Ficio AI Analysis (Vision/Smell)", icons["camera"])
        cam_frame.grid(row=0, column=1, sticky="nsew")
        self.sections["camera"] = cam_content
        self.cam_label = tk.Label(cam_content, bg="black")
        self.cam_label.pack(expand=True, fill="both", padx=10, pady=10)
        self.cam_image_ref = None  # prevent GC

        # --- INGREDIENT PROGRESS (top-left)
        ing_frame, ing_content = self.section(self.root, "Ingredient Progress", icons["ingredients"])
        ing_frame.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
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

        # --- INSTRUCTIONS (top-right)
        inst_frame, inst_content = self.section(self.root, "Instructions", icons["instructions"])
        inst_frame.grid(row=0, column=1, sticky="nsew", padx=8, pady=8)
        self.sections["instructions"] = inst_content
        self.inst_label = tk.Label(
            inst_content,
            text="",
            bg="#333333",
            fg="white",
            font=("Segoe UI", 24, "bold"),
            wraplength=550,
            justify="center"
        )
        self.inst_label.pack(anchor="w", fill="both", padx=10, pady=10)

    # --------------------------------------------------
    # Continue button
    # --------------------------------------------------
    def create_continue_button(self):
        """Create bottom-right Continue button."""
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
        """Handle Continue button click (thread-safe)."""
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
        """Block until Continue is pressed or timeout expires."""
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
        """Update the camera preview image, maintaining aspect ratio."""
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

    def update_status(self, color):
        """Change the background color of the Status panel."""
        try:
            self.status_frame.config(bg=color)
        except Exception as e:
            print(f"Error updating status color: {e}")

    # --------------------------------------------------
    # Thread-safe wrappers
    # --------------------------------------------------
    def _schedule(self, fn, *args, **kwargs):
        """Schedule a function safely in the Tkinter main thread."""
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

    def safe_update_status(self, color):
        self._schedule(self.update_status, color)

    # --------------------------------------------------
    # Instruction Highlighting
    # --------------------------------------------------
    def highlight_instructions(self, color="#AA0000"):
        """Highlight the instruction section with a color (e.g., red for alert)."""
        try:
            self.inst_label.config(bg=color)
            parent = self.inst_label.master
            parent.config(bg=color)
        except Exception as e:
            print(f"Failed to highlight instructions: {e}")

    def reset_instructions_highlight(self):
        """Reset instruction section to default background."""
        try:
            self.inst_label.config(bg="#333333")
            parent = self.inst_label.master
            parent.config(bg="#333333")
        except Exception as e:
            print(f"Failed to reset instructions highlight: {e}")


# --- Test Run ---
if __name__ == "__main__":
    ui = DashboardUI()
    ui.safe_update_ingredients("Potato: 1345/2500 g")
    ui.safe_update_instructions("Please place the next potato under the camera.")
    ui.root.mainloop()