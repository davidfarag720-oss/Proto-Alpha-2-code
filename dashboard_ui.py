import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import threading


# ------------------------------------------------------------
# Main App with two pages
# ------------------------------------------------------------
class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Smart Veggie Station")
        self.geometry("800x480")  # ideal for most 7-inch Pi touchscreens
        self.minsize(800, 480)
        self.configure(bg="#FFFFFF")

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        # Container for pages
        self.container = tk.Frame(self, bg="#FFFFFF")
        self.container.grid(row=0, column=0, sticky="nsew")

        # Dictionary of pages
        self.pages = {}

        # Add both pages
        self.add_page("vegetable_selection", VegetableSelectionPage)
        self.add_page("vegetable_processing", VegetableProcessingPage)

        # Start on selection page
        self.current_page = "vegetable_selection"
        self.show_page(self.current_page)

    def add_page(self, name, page_class):
        page = page_class(parent=self.container, controller=self)
        self.pages[name] = page
        page.grid(row=0, column=0, sticky="nsew")

    def show_page(self, name):
        self.pages[name].tkraise()
        self.current_page = name
    def get_page(self, name):
        return self.pages.get(name, None)

    def toggle_page(self):
        """Switch between selection and processing pages."""
        if self.current_page == "vegetable_selection":
            self.show_page("vegetable_processing")
        else:
            self.show_page("vegetable_selection")


# ------------------------------------------------------------
# Vegetable Selection Page (new)
# ------------------------------------------------------------
class VegetableSelectionPage(tk.Frame):
    def __init__(self, parent, controller, on_select_callback=None):
        super().__init__(parent, bg="#FFFFFF")
        self.controller = controller
        self.on_select_callback = on_select_callback
        self.select_event = threading.Event()

        # Configure grid for a 2x2 layout
        for i in range(2):
            self.rowconfigure(i, weight=1, uniform="row")
            self.columnconfigure(i, weight=1, uniform="col")

        # Define vegetable buttons (image + label)
        veggies = [
            ("Carrot", "/home/dfarag/ficio/proto_alpha_2_code/icons/carrot.jpg"),
            ("Tomato", "/home/dfarag/ficio/proto_alpha_2_code/icons/tomato.jpg"),
            ("Bell Pepper", "/home/dfarag/ficio/proto_alpha_2_code/icons/bell_pepper.jpg"),
            ("Potato", "/home/dfarag/ficio/proto_alpha_2_code/icons/potato.jpg"),
        ]

        # Create 2x2 grid of buttons
        idx = 0
        for r in range(2):
            for c in range(2):
                name, img_path = veggies[idx]
                idx += 1
                self.create_veg_button(r, c, name, img_path)

    def create_veg_button(self, row, col, name, img_path):
        frame = tk.Frame(self, bg="#F9F9F9", highlightbackground="#CCCCCC", highlightthickness=2)
        frame.grid(row=row, column=col, padx=40, pady=40, sticky="nsew")
        frame.rowconfigure(0, weight=4)
        frame.rowconfigure(1, weight=1)
        frame.columnconfigure(0, weight=1)

        # Load image safely
        try:
            img = Image.open(img_path).resize((200, 200))
        except Exception:
            img = Image.new("RGB", (200, 200), color=(200, 200, 200))
        photo = ImageTk.PhotoImage(img)

        # Button image
        btn = tk.Button(
            frame,
            image=photo,
            bg="#FFFFFF",
            relief="flat",
            command=self._internal_on_select,
        )
        btn.image = photo
        btn.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Label
        label = tk.Label(
            frame,
            text=name,
            bg="#FFFFFF",
            fg="#222222",
            font=("Segoe UI", 18, "bold"),
        )
        label.grid(row=1, column=0, sticky="nsew", pady=(0, 10))

    def _internal_on_select(self):
        """Trigger callback (same idea as Continue button)."""
        try:
            self.select_event.set()
        except Exception:
            pass
        if callable(self.on_select_callback):
            try:
                self.on_select_callback()
            except Exception as e:
                print("Error in selection callback:", e)

    def wait_for_selection(self, timeout=None):
        """Block until a vegetable is selected."""
        self.select_event.clear()
        return self.select_event.wait(timeout=timeout)

# ------------------------------------------------------------
# VegetableProcessingPage (your existing UI adapted to be a page)
# ------------------------------------------------------------
class VegetableProcessingPage(tk.Frame):
    def __init__(self, parent, controller, on_continue_click=None):
        super().__init__(parent, bg="#FFFFFF")
        self.controller = controller
        self.on_continue_click = on_continue_click
        self.continue_event = threading.Event()

        # Style config
        style = ttk.Style()
        style.theme_use("default")
        style.configure("TFrame", background="#FFFFFF", borderwidth=1, relief="solid")
        style.configure("TLabelframe", background="#FFFFFF", borderwidth=2, relief="groove", foreground="#444444")
        style.configure("TLabelframe.Label", background="#FFFFFF", foreground="#444444", font=("Segoe UI", 12, "bold"))

        # Make the page frame expandable
        self.rowconfigure(0, weight=1, uniform="row")
        self.rowconfigure(1, weight=3, uniform="row")
        self.columnconfigure(0, weight=1, uniform="col")
        self.columnconfigure(1, weight=1, uniform="col")

        # Store sections
        self.sections = {}
        self.create_sections()
        self.create_continue_button()
        self.safe_update_status("#00AA00")

    # --------------------------------------------------
    # Reusable section factory (no grid_propagate so it can resize)
    # --------------------------------------------------
    def section(self, parent, title, icon_path=None):
        frame = ttk.Frame(parent, padding=10)
        # allow the frame to resize with its parent (do NOT disable grid propagation)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)

        header_frame = tk.Frame(frame, bg="#F2F2F2")
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        header_frame.columnconfigure(1, weight=1)

        if icon_path:
            try:
                icon_img = Image.open(icon_path).resize((28, 28))
                icon = ImageTk.PhotoImage(icon_img)
                icon_label = tk.Label(header_frame, image=icon, bg="#F2F2F2")
                icon_label.image = icon
                icon_label.grid(row=0, column=0, padx=(5, 10))
            except Exception:
                # don't fail if icon path is wrong
                pass

        title_label = tk.Label(header_frame, text=title, bg="#F2F2F2", fg="#222222", font=("Segoe UI", 14, "bold"))
        title_label.grid(row=0, column=1, sticky="w")

        content = tk.Frame(frame, bg="#FFFFFF", highlightbackground="#CCCCCC", highlightthickness=1)
        content.grid(row=1, column=0, sticky="nsew")

        return frame, content

    # --------------------------------------------------
    # Sections
    # --------------------------------------------------
    def create_sections(self):
        icons = {
            "camera": "/home/dfarag/ficio/proto_alpha_2_code/icons/camera.png",
            "ingredients": "/home/dfarag/ficio/proto_alpha_2_code/icons/ingredients.png",
            "instructions": "/home/dfarag/ficio/proto_alpha_2_code/icons/instructions.png"
        }

        # bottom_frame uses grid and expands
        bottom_frame = tk.Frame(self, bg="#FFFFFF")
        bottom_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=8, pady=8)
        bottom_frame.rowconfigure(0, weight=1)
        bottom_frame.columnconfigure(0, weight=1)
        bottom_frame.columnconfigure(1, weight=4)

        status_outer = tk.LabelFrame(
            bottom_frame,
            text="Status",
            fg="#444444",
            bg="#FFFFFF",
            font=("Segoe UI", 14, "bold"),
            labelanchor="n",
            bd=2,
            relief="groove"
        )
        status_outer.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        # allow the status_frame to expand inside status_outer
        self.status_frame = tk.Frame(status_outer, bg="#DDDDDD")
        self.status_frame.pack(expand=True, fill="both", padx=5, pady=5)
        self.sections["status"] = self.status_frame

        cam_frame, cam_content = self.section(bottom_frame, "Ficio AI Analysis (Vision/Smell)", icons["camera"])
        cam_frame.grid(row=0, column=1, sticky="nsew")
        cam_frame.rowconfigure(1, weight=1)
        cam_content.rowconfigure(0, weight=1)
        self.sections["camera"] = cam_content
        self.cam_label = tk.Label(cam_content, bg="#EEEEEE")
        self.cam_label.pack(expand=True, fill="both", padx=10, pady=10)
        self.cam_image_ref = None

        ing_frame, ing_content = self.section(self, "Ingredient Progress", icons["ingredients"])
        ing_frame.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        ing_frame.rowconfigure(1, weight=1)
        self.sections["ingredients"] = ing_content
        self.ing_label = tk.Label(
            ing_content,
            text="",
            bg="#FFFFFF",
            fg="#222222",
            font=("Segoe UI", 21, "bold"),
            justify="center",
            anchor="center"
        )
        self.ing_label.pack(expand=True, fill="both", padx=10, pady=10)

        inst_frame, inst_content = self.section(self, "Instructions", icons["instructions"])
        inst_frame.grid(row=0, column=1, sticky="nsew", padx=8, pady=8)
        inst_frame.rowconfigure(1, weight=1)
        self.sections["instructions"] = inst_content
        self.inst_label = tk.Label(
            inst_content,
            text="",
            bg="#FFFFFF",
            fg="#222222",
            font=("Segoe UI", 21, "bold"),
            wraplength=550,
            justify="center"
        )
        self.inst_label.pack(anchor="w", fill="both", padx=10, pady=10)

    # --------------------------------------------------
    # Continue Button (keeps same look but now inside the page)
    # --------------------------------------------------
    def create_continue_button(self):
        # place is okay here; it is relative to this page frame and will move with it
        self.continue_btn = tk.Button(
            self,
            text="Continue",
            bg="#0078D7",
            fg="white",
            font=("Segoe UI", 12, "bold"),
            borderwidth=0,
            relief="flat",
            command=self._internal_on_continue_click
        )
        self.continue_btn.place(relx=0.95, rely=0.95, anchor="se")

    # --------------------------------------------------
    # Unchanged helper methods
    # --------------------------------------------------
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

    def update_status(self, color):
        try:
            self.status_frame.config(bg=color)
        except Exception as e:
            print(f"Error updating status color: {e}")

    def safe_update_status(self, color):
        self.after(0, lambda: self.update_status(color))

    def safe_update_instructions(self, text):
        self.after(0, lambda: self.update_instructions(text))

    def safe_update_ingredients(self, text):
        self.after(0, lambda: self.update_ingredients(text))


# ------------------------------------------------------------
# Run the App
# ------------------------------------------------------------
if __name__ == "__main__":
    app = MainApp()
    page = app.pages["vegetable_processing"]
    page.safe_update_ingredients("Potato: 1345/2500 g")
    page.safe_update_instructions("Please place the next potato under the camera.")
    app.mainloop()
