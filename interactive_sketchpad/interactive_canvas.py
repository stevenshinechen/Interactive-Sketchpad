import sys
import threading
import time
import tkinter as tk
from io import BytesIO
from tkinter import colorchooser, ttk

import requests
import uvicorn
from fastapi import FastAPI, File, UploadFile
from PIL import Image, ImageGrab, ImageTk

from interactive_sketchpad.canvas import Canvas


class InteractiveCanvas(Canvas):
    def __init__(self, root, session_id: str):
        super().__init__(root)
        self.session_id = session_id

        self.send_button = tk.Button(
            self.top_frame, text="Send Screenshot", command=self.send_screenshot
        )
        self.send_button.pack(side=tk.LEFT, padx=5)

        self.server_url = "http://127.0.0.1:8000/upload"

        self._screenshot = None
        self.running = True

        self.images = []  # Store images to prevent garbage collection

    @property
    def screenshot(self):
        return self._screenshot

    @screenshot.setter
    def screenshot(self, screenshot):
        self._screenshot = screenshot

    def send_screenshot(self):
        """Capture and send the screenshot to the server regardless of similarity."""
        self.screenshot = self.take_screenshot()
        threading.Thread(
            target=self.send_image_to_server, args=(self.screenshot,), daemon=True
        ).start()

    def start_drawing(self, event):
        self.last_x, self.last_y = event.x, event.y

    def resize_image(self, image):
        """Resize image to fit canvas, maintaining aspect ratio"""
        # Update so winfo_width and height returns correct dimensions
        self.root.update_idletasks()
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        img_width, img_height = image.size

        # Calculate the scaling factor to fit the image within the canvas
        scale_factor = min(canvas_width / img_width, canvas_height / img_height)

        new_width = int(img_width * scale_factor)
        new_height = int(img_height * scale_factor)

        resized_image = image.resize((new_width, new_height))
        return resized_image

    def add_image_to_canvas(self, image):
        """Add an image to the canvas and allow movement."""
        image = self.resize_image(image)
        tk_image = ImageTk.PhotoImage(image)
        self.canvas.create_image(
            self.canvas.winfo_width() // 2,  # Center horizontally
            self.canvas.winfo_height() // 2,  # Center vertically
            image=tk_image,
            anchor=tk.CENTER,
        )
        self.images.append(tk_image)  # Keep reference to prevent garbage collection

    def clear_canvas(self):
        self.canvas.delete("all")
        self.images.clear()

    def take_screenshot(self):
        print("Taking screenshot")
        x = self.root.winfo_rootx() + self.canvas.winfo_x()
        y = self.root.winfo_rooty() + self.canvas.winfo_y()
        x1 = x + self.canvas.winfo_width()
        y1 = y + self.canvas.winfo_height()
        screenshot = ImageGrab.grab((x, y, x1, y1))
        print(x, y, x1, y1)
        return screenshot

    def send_image_to_server(self, image):
        print(f"Sending image to server with {self.session_id=}")
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)

        try:
            response = requests.post(
                f"{self.server_url}?session_id={self.session_id}",  # Append session_id as a query parameter
                files={"file": ("drawing.png", buffer, "image/png")},
            )

            if response.status_code == 200:
                print(f"Image successfully uploaded: {response.text}")
            else:
                print(
                    f"Failed to upload image. Status Code: {response.status_code}, Response: {response.text}"
                )

        except Exception as e:
            print(f"Error sending image: {e}")

    def stop(self):
        self.running = False


def get_session_id():
    """Retrieve session ID from command-line arguments."""
    if len(sys.argv) > 1:
        return sys.argv[1]
    return None


app = FastAPI()


class InteractiveCanvasServer:
    def __init__(self, canvas_app):
        self.canvas_app = canvas_app

    async def receive_image(self, file: UploadFile = File(...)):
        """Receives an image from Chainlit and updates the Tkinter GUI."""
        content = await file.read()
        image = Image.open(BytesIO(content))

        self.canvas_app.create_new_page()
        # Update UI with the new image
        self.canvas_app.add_image_to_canvas(image)
        return {"message": "Image received and displayed"}


if __name__ == "__main__":
    root = tk.Tk()
    drawing_app = InteractiveCanvas(root, session_id=get_session_id())

    server = InteractiveCanvasServer(drawing_app)
    app.post("/send_image_to_canvas")(server.receive_image)

    def run_fastapi():
        uvicorn.run(app, host="0.0.0.0", port=8081, log_level="info")

    threading.Thread(target=run_fastapi, daemon=True).start()

    root.mainloop()
