import time
import tkinter as tk
import threading
from tkinter import ttk
from PIL import Image, ImageTk
from order_manager import OrderManager, Ingredient

class DashboardUI:
    def __init__(self, on_continue_click=None):
        self.on_continue_click = on_continue_click
        self.continue_event = threading.Event()
        self.root = tk.Tk()
        self.root.title("Smart Veggie Station")
        self.root.configure(bg="#1E1E1E")
        self.root.geometry("1200x700")

        # We'll store references to each content area here
        self.sections = {}

        self.setup_grid()
        self.create_sections()
        self.create_continue_button()

    def setup_grid(self):
        for i in range(2):
            self.root.rowconfigure(i, weight=1, uniform="row")
        for j in range(2):
            self.root.columnconfigure(j, weight=1, uniform="col")

    def section(self, parent, title, icon_path=None):
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

    def create_sections(self):
        icons = {
            "order": "/home/dfarag/ficio/proto_alpha_2_code/icons/orders.png",
            "camera": "/home/dfarag/ficio/proto_alpha_2_code/icons/camera.png",
            "ingredients": "/home/dfarag/ficio/proto_alpha_2_code/icons/ingredients.png",
            "instructions": "/home/dfarag/ficio/proto_alpha_2_code/icons/instructions.png"
        }

        # Order
        order_frame, order_content = self.section(self.root, "Order", icons["order"])
        order_frame.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        self.sections["order"] = order_content
        self.order_label = tk.Label(order_content, text="", bg="#333333", fg="white", font=("Segoe UI", 12), justify="left", anchor="nw")
        self.order_label.pack(anchor="w", fill="both", padx=10, pady=10)

        # Camera
        cam_frame, cam_content = self.section(self.root, "Camera", icons["camera"])
        cam_frame.grid(row=0, column=1, sticky="nsew", padx=8, pady=8)
        self.sections["camera"] = cam_content
        self.cam_label = tk.Label(cam_content, bg="black")
        self.cam_label.pack(expand=True, fill="both", padx=10, pady=10)
        self.cam_image_ref = None  # to prevent garbage collection

        # Ingredients
        ing_frame, ing_content = self.section(self.root, "Ingredients", icons["ingredients"])
        ing_frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=8)
        self.sections["ingredients"] = ing_content
        self.ing_label = tk.Label(ing_content, text="", bg="#333333", fg="white", font=("Segoe UI", 12), justify="left", anchor="nw")
        self.ing_label.pack(anchor="w", fill="both", padx=10, pady=10)

        # Instructions
        inst_frame, inst_content = self.section(self.root, "Instructions", icons["instructions"])
        inst_frame.grid(row=1, column=1, sticky="nsew", padx=8, pady=8)
        self.sections["instructions"] = inst_content
        self.inst_label = tk.Label(inst_content, text="", bg="#333333", fg="white", font=("Segoe UI", 12), wraplength=250, justify="left")
        self.inst_label.pack(anchor="w", fill="both", padx=10, pady=10)

    def create_continue_button(self):
        self.continue_btn = tk.Button(self.root, text="Continue", bg="#00C7A5", fg="white",
                                      font=("Segoe UI", 12, "bold"), borderwidth=0, relief="flat",
                                      command=self._internal_on_continue_click)
        self.continue_btn.place(relx=0.95, rely=0.95, anchor="se")
    def _internal_on_continue_click(self):
        """Internal handler invoked by the button (GUI thread)."""
        # set the event so any waiting controller thread wakes up
        try:
            self.continue_event.set()
        except Exception:
            pass

        # also call external callback if provided (non-blocking)
        if callable(self.on_continue_click):
            try:
                self.on_continue_click()
            except Exception as e:
                print("Error in on_continue_click callback:", e)

    def wait_for_continue(self, timeout=None):
        """
        Blocks until Continue is pressed.
        Call with timeout in seconds if you want to bail out.
        Returns True if the event fired, False if timed out.
        """
        # clear any previous event state, then wait
        self.continue_event.clear()
        return self.continue_event.wait(timeout=timeout)

    # -----------------------------
    # 🔹 Update Functions
    # -----------------------------

    def update_order(self, items):
        """Update the order section with a list of items."""
        text = "\n".join([f"• {item}" for item in items])
        self.order_label.config(text=text)

    def update_ingredients(self, ingredients):
        """Update the ingredients section."""
        text = "\n".join([f"• {ing}" for ing in ingredients])
        self.ing_label.config(text=text)

    def update_instructions(self, text):
        """Update the instructions text."""
        self.inst_label.config(text=text)

    def update_camera_image(self, image_path):
        """Update the camera display with a new image."""
        try:
            img = Image.open(image_path)
            #img = img.resize((self.cam_label.winfo_width(), self.cam_label.winfo_height()))
            photo = ImageTk.PhotoImage(img)
            self.cam_label.config(image=photo)
            self.cam_image_ref = photo  # keep a reference to avoid garbage collection
        except Exception as e:
            print(f"Error loading image: {e}")

    def _schedule(self, fn, *args, **kwargs):
        """Schedule a function to run on the tkinter mainloop thread."""
        try:
            # `after(0, ...)` runs the callable on the GUI thread ASAP.
            self.root.after(0, lambda: fn(*args, **kwargs))
        except Exception as e:
            print("Failed to schedule GUI update:", e)

    def safe_update_instructions(self, text):
        """Thread-safe wrapper for update_instructions."""
        self._schedule(self.update_instructions, text)

    def safe_update_camera_image(self, image_path):
        """Thread-safe wrapper for update_camera_image."""
        self._schedule(self.update_camera_image, image_path)

    def safe_update_order(self, items):
        """Thread-safe wrapper for update_order."""
        self._schedule(self.update_order, items)

    def safe_update_ingredients(self, ingredients):
        """Thread-safe wrapper for update_ingredients."""
        self._schedule(self.update_ingredients, ingredients)
    # -----------------------------
    # 🔹 Button Listener
    # -----------------------------
    def complete_click_handler(self):
        """Old on_complete_click replacement (if you need it)."""
        cb = getattr(self, "on_complete_click", None)
        if callable(cb):
            try:
                cb()
            except Exception as e:
                print("Error in on_complete_click callback:", e)

# Run test
if __name__ == "__main__":
    ui = DashboardUI()

    # Example dynamic updates
    manager = OrderManager()
    manager.add_order("Potato Order", {Ingredient.POTATO: 150})
    manager.add_order("Another Potato Order", {Ingredient.POTATO: 200})
    manager.add_order("Small Potato Order", {Ingredient.POTATO: 100})
    ui.safe_update_order([str(order) for order in manager.orders])
    ui.safe_update_ingredients([f"{ing.value}: {amt}g" for ing, amt in manager.ingredient_totals.items()])
    ui.safe_update_instructions("Welcome! Please place the vegetable in front of the camera.")
    ui.root.mainloop()