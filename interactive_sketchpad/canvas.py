import time
import tkinter as tk
from tkinter import colorchooser

PAGE_ROW = 1


class Canvas:
    def __init__(self, root):
        self.root = root
        self.root.title("Interactive Whiteboard")

        self.root.grid_rowconfigure(0, weight=1)  # Allow canvas to expand
        self.root.grid_columnconfigure(0, weight=1)

        self.pages = [tk.Canvas(root, width=800, height=600, bg="white")]
        self.current_page_index = 0
        self.pages[self.current_page_index].grid(row=PAGE_ROW, column=0, sticky="nsew")

        # Top Frame (Contains navigation + tools)
        self.top_frame = tk.Frame(root, padx=10, pady=10)
        self.top_frame.grid(row=0, column=0, columnspan=2, sticky="ew")

        self.back_button = tk.Button(
            self.top_frame, text="← Back", command=self.go_back, state=tk.DISABLED
        )
        self.back_button.pack(side=tk.LEFT, padx=5)

        self.forward_button = tk.Button(
            self.top_frame,
            text="Forward →",
            command=self.go_forward,
            state=tk.DISABLED,
        )
        self.forward_button.pack(side=tk.LEFT, padx=5)

        self.new_page_button = tk.Button(
            self.top_frame, text="New Page", command=self.create_new_page
        )
        self.new_page_button.pack(side=tk.LEFT, padx=5)

        # Use self.canvas to refer to the active page
        self.canvas = self.pages[self.current_page_index]
        self.bind_canvas_events(self.canvas)

        self.brush_thickness = 5
        self.prev_brush_color = "black"
        self.brush_color = "black"
        self.eraser_mode = False
        self.last_x, self.last_y = None, None

        self.pan_start_x = None
        self.pan_start_y = None

        self.tools_frame = tk.Frame(root, padx=10, pady=10)
        self.tools_frame.grid(row=0, column=1, sticky="ns")

        # Brush thickness preview (Canvas acts as button)
        self.thickness_preview = tk.Canvas(
            self.top_frame, width=40, height=40, bg="white", highlightthickness=1
        )
        self.thickness_preview.pack(side=tk.LEFT, padx=5)

        # Bind click event to open popup slider
        self.thickness_preview.bind("<Button-1>", self.open_thickness_popup)
        self.update_brush_preview(self.brush_thickness)

        # Color selection canvas (acts as a button)
        self.color_canvas = tk.Canvas(
            self.top_frame,
            width=40,
            height=40,
            bg=self.brush_color,
            highlightthickness=1,
        )
        self.color_canvas.pack(side=tk.LEFT, padx=5)

        # Bind a click event to open the color chooser
        self.color_canvas.bind("<Button-1>", lambda event: self.choose_color())

        self.eraser_button = tk.Button(
            self.top_frame, text="Eraser (off)", command=self.toggle_eraser
        )
        self.eraser_button.pack(side=tk.LEFT, padx=5)

        self.clear_button = tk.Button(
            self.top_frame, text="Clear Canvas", command=self.clear_canvas
        )
        self.clear_button.pack(side=tk.LEFT, padx=5)

    def bind_canvas_events(self, canvas):
        """Bind drawing and panning events to a canvas."""
        canvas.bind("<ButtonPress-1>", self.start_drawing)
        canvas.bind("<B1-Motion>", self.draw)
        canvas.bind("<ButtonRelease-1>", self.stop_drawing)
        canvas.bind("<Shift-ButtonPress-1>", self.start_panning)
        canvas.bind("<Shift-B1-Motion>", self.pan_canvas)
        canvas.bind("<Shift-ButtonRelease-1>", self.stop_panning)

    def create_new_page(self):
        """Create a new blank canvas page."""
        for page in self.pages:
            page.pack_forget()

        new_canvas = tk.Canvas(self.root, width=800, height=600, bg="white")
        self.pages.append(new_canvas)
        self.current_page_index = len(self.pages) - 1
        new_canvas.grid(row=PAGE_ROW, column=0, sticky="nsew")
        self.canvas = new_canvas
        self.bind_canvas_events(new_canvas)

        # Enable back button if there are multiple pages
        if len(self.pages) > 1:
            self.back_button.config(state=tk.NORMAL)

    def go_back(self):
        """Switch to the previous page."""
        if self.current_page_index > 0:
            self.pages[self.current_page_index].grid_forget()
            self.current_page_index -= 1
            self.pages[self.current_page_index].grid(
                row=PAGE_ROW, column=0, sticky="nsew"
            )
            self.canvas = self.pages[self.current_page_index]
            self.canvas.config(bg="white")
            self.bind_canvas_events(self.canvas)

        self.update_navigation_buttons()

    def go_forward(self):
        """Switch to the next page."""
        if self.current_page_index < len(self.pages) - 1:
            self.pages[self.current_page_index].grid_forget()
            self.current_page_index += 1
            self.pages[self.current_page_index].grid(
                row=PAGE_ROW, column=0, sticky="nsew"
            )
            self.canvas = self.pages[self.current_page_index]
            self.canvas.config(bg="white")
            self.bind_canvas_events(self.canvas)

        self.update_navigation_buttons()

    def update_navigation_buttons(self):
        """Enable or disable navigation buttons based on the current page index."""
        self.back_button.config(
            state=tk.NORMAL if self.current_page_index > 0 else tk.DISABLED
        )
        self.forward_button.config(
            state=(
                tk.NORMAL
                if self.current_page_index < len(self.pages) - 1
                else tk.DISABLED
            )
        )

    def start_panning(self, event):
        """Capture the initial position when right-clicking to start panning."""
        self.pan_start_x = event.x
        self.pan_start_y = event.y

    def pan_canvas(self, event):
        """Move the canvas when dragging with right-click."""
        if self.pan_start_x is not None and self.pan_start_y is not None:
            dx = event.x - self.pan_start_x  # Calculate movement delta
            dy = event.y - self.pan_start_y
            self.canvas.move("all", dx, dy)  # Move all objects on the canvas
            self.pan_start_x = event.x  # Update last position
            self.pan_start_y = event.y

    def stop_panning(self, event):
        """Reset panning start coordinates when right-click is released."""
        self.pan_start_x = None
        self.pan_start_y = None

    def toggle_eraser(self):
        """Toggle eraser mode on/off."""
        self.eraser_mode = not self.eraser_mode
        self.eraser_button.config(
            text=f"Eraser ({"On" if self.eraser_mode else "Off"})"
        )
        if self.eraser_mode:
            self.prev_brush_color = self.brush_color
            self.brush_color = "white"  # Set color to background color
        else:
            self.brush_color = self.prev_brush_color  # Restore the default brush color

    def start_drawing(self, event):
        self.last_x, self.last_y = event.x, event.y

    def draw(self, event):
        x, y = event.x, event.y
        if self.last_x and self.last_y:
            self.canvas.create_line(
                self.last_x,
                self.last_y,
                x,
                y,
                fill=self.brush_color,
                width=self.brush_thickness,
                capstyle=tk.ROUND,
                smooth=True,
            )
            self.canvas.delete("brush_outline")
            radius = self.brush_thickness // 2
            self.canvas.create_oval(
                x - radius,
                y - radius,
                x + radius,
                y + radius,
                outline="black",
                width=1,
                tags="brush_outline",
            )
        self.last_x, self.last_y = x, y

    def stop_drawing(self, event):
        self.last_x, self.last_y = None, None
        self.canvas.delete("brush_outline")

    def choose_color(self):
        color = colorchooser.askcolor(color=self.brush_color)
        if color[1]:
            self.brush_color = color[1]
            self.color_canvas.config(bg=self.brush_color)

    def update_brush_preview(self, value):
        """Update the brush preview to reflect the selected thickness."""
        self.thickness_preview.delete("all")
        CANVAS_BOUNDS = 18
        size = int(value)
        center_x, center_y = 20, 20  # Center of the preview canvas
        radius = min(size // 2, CANVAS_BOUNDS)

        self.thickness_preview.create_oval(
            center_x - radius,
            center_y - radius,
            center_x + radius,
            center_y + radius,
            fill=self.brush_color,
            outline="black",
        )

    def open_thickness_popup(self, event):
        """Open a popup window containing the brush thickness slider."""
        popup = tk.Toplevel(self.root)
        popup.title("Adjust Brush Thickness")
        popup.geometry(
            f"250x100+{self.root.winfo_x() + event.x_root}+{self.root.winfo_y() + event.y_root}"
        )  # Position near cursor
        popup.resizable(False, False)

        # Slider inside popup
        tk.Label(popup, text="Brush Thickness").pack(pady=5)
        thickness_slider = tk.Scale(
            popup,
            from_=1,
            to=100,
            orient=tk.HORIZONTAL,
            command=self.update_brush_preview,
        )
        thickness_slider.set(self.brush_thickness)
        thickness_slider.pack(pady=5)

        # Close popup when a thickness is selected
        def close_popup():
            self.brush_thickness = thickness_slider.get()
            popup.destroy()

        thickness_slider.bind("<ButtonRelease-1>", lambda event: close_popup())

    def clear_canvas(self):
        self.canvas.delete("all")
