import tkinter as tk
from tkinter import filedialog, messagebox, colorchooser
from PIL import Image, ImageTk, ImageEnhance, ImageFilter, ImageDraw

class PhotoEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Photo Editor - Full Featured")
        self.root.geometry("1200x800")

        self.image = None
        self.display_image = None
        self.original_image = None
        self.image_path = None

        self.undo_stack = []
        self.redo_stack = []

        self.zoom_level = 1.0
        self.pan_x = 0
        self.pan_y = 0

        self.draw_mode = False
        self.brush_color = "black"
        self.brush_size = 5

        self.crop_mode = False
        self.crop_start = None
        self.crop_rect = None

        self.canvas = tk.Canvas(self.root, bg='gray', cursor="cross")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)

        self.create_menu()
        self.create_controls()

    def create_menu(self):
        menu = tk.Menu(self.root)
        self.root.config(menu=menu)

        file_menu = tk.Menu(menu, tearoff=0)
        file_menu.add_command(label="Open", command=self.open_image)
        file_menu.add_command(label="Save As", command=self.save_image)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        filter_menu = tk.Menu(menu, tearoff=0)
        filter_menu.add_command(label="Grayscale", command=self.apply_grayscale)
        filter_menu.add_command(label="Blur", command=self.apply_blur)
        filter_menu.add_command(label="Sepia", command=self.apply_sepia)

        transform_menu = tk.Menu(menu, tearoff=0)
        transform_menu.add_command(label="Rotate Left", command=lambda: self.rotate(-90))
        transform_menu.add_command(label="Rotate Right", command=lambda: self.rotate(90))

        edit_menu = tk.Menu(menu, tearoff=0)
        edit_menu.add_command(label="Undo", command=self.undo)
        edit_menu.add_command(label="Redo", command=self.redo)

        draw_menu = tk.Menu(menu, tearoff=0)
        draw_menu.add_command(label="Toggle Draw Mode", command=self.toggle_draw)
        draw_menu.add_command(label="Pick Brush Color", command=self.pick_color)

        crop_menu = tk.Menu(menu, tearoff=0)
        crop_menu.add_command(label="Start Crop Mode", command=self.toggle_crop_mode)

        menu.add_cascade(label="File", menu=file_menu)
        menu.add_cascade(label="Filters", menu=filter_menu)
        menu.add_cascade(label="Transform", menu=transform_menu)
        menu.add_cascade(label="Edit", menu=edit_menu)
        menu.add_cascade(label="Draw", menu=draw_menu)
        menu.add_cascade(label="Crop", menu=crop_menu)

    def create_controls(self):
        control_frame = tk.Frame(self.root)
        control_frame.pack(fill=tk.X)

        tk.Label(control_frame, text="Brightness").pack(side=tk.LEFT)
        self.brightness_slider = tk.Scale(control_frame, from_=0.5, to=2.0, resolution=0.1, orient=tk.HORIZONTAL,
                                          command=self.update_brightness)
        self.brightness_slider.set(1.0)
        self.brightness_slider.pack(side=tk.LEFT)

        tk.Label(control_frame, text="Contrast").pack(side=tk.LEFT)
        self.contrast_slider = tk.Scale(control_frame, from_=0.5, to=2.0, resolution=0.1, orient=tk.HORIZONTAL,
                                        command=self.update_contrast)
        self.contrast_slider.set(1.0)
        self.contrast_slider.pack(side=tk.LEFT)

    def open_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.bmp")])
        if file_path:
            self.image_path = file_path
            self.image = Image.open(file_path).convert("RGB")
            self.original_image = self.image.copy()
            self.undo_stack = []
            self.redo_stack = []
            self.zoom_level = 1.0
            self.pan_x = 0
            self.pan_y = 0
            self.push_undo()
            self.display()

    def save_image(self):
        if self.image:
            file_path = filedialog.asksaveasfilename(defaultextension=".png",
                                                     filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg;*.jpeg")])
            if file_path:
                self.image.save(file_path)
                messagebox.showinfo("Saved", f"Image saved at {file_path}")

    def display(self):
        if self.image:
            resized = self.image.resize((int(self.image.width * self.zoom_level),
                                         int(self.image.height * self.zoom_level)))
            self.display_image = ImageTk.PhotoImage(resized)
            self.canvas.delete("all")
            self.canvas.create_image(self.pan_x, self.pan_y, image=self.display_image, anchor=tk.CENTER)

    def apply_grayscale(self):
        if self.image:
            self.push_undo()
            self.image = self.image.convert("L").convert("RGB")
            self.display()

    def apply_blur(self):
        if self.image:
            self.push_undo()
            self.image = self.image.filter(ImageFilter.GaussianBlur(3))
            self.display()

    def apply_sepia(self):
        if self.image:
            self.push_undo()
            sepia = self.image.convert("RGB")
            pixels = sepia.load()
            for y in range(sepia.height):
                for x in range(sepia.width):
                    r, g, b = pixels[x, y]
                    tr = int(0.393 * r + 0.769 * g + 0.189 * b)
                    tg = int(0.349 * r + 0.686 * g + 0.168 * b)
                    tb = int(0.272 * r + 0.534 * g + 0.131 * b)
                    pixels[x, y] = (min(tr, 255), min(tg, 255), min(tb, 255))
            self.image = sepia
            self.display()

    def rotate(self, angle):
        if self.image:
            self.push_undo()
            self.image = self.image.rotate(angle, expand=True)
            self.display()

    def update_brightness(self, val):
        if self.original_image:
            enhancer = ImageEnhance.Brightness(self.original_image)
            temp = enhancer.enhance(float(val))
            self.update_contrast(self.contrast_slider.get(), temp)

    def update_contrast(self, val, base_img=None):
        img = base_img if base_img else self.original_image
        if img:
            enhancer = ImageEnhance.Contrast(img)
            self.image = enhancer.enhance(float(val))
            self.display()

    def push_undo(self):
        if self.image:
            self.undo_stack.append(self.image.copy())
            self.redo_stack.clear()

    def undo(self):
        if self.undo_stack:
            self.redo_stack.append(self.image.copy())
            self.image = self.undo_stack.pop()
            self.original_image = self.image.copy()
            self.display()

    def redo(self):
        if self.redo_stack:
            self.undo_stack.append(self.image.copy())
            self.image = self.redo_stack.pop()
            self.original_image = self.image.copy()
            self.display()

    def toggle_draw(self):
        self.draw_mode = not self.draw_mode
        messagebox.showinfo("Draw", f"Draw mode is {'ON' if self.draw_mode else 'OFF'}")

    def pick_color(self):
        color = colorchooser.askcolor()[1]
        if color:
            self.brush_color = color

    def on_mouse_down(self, event):
        if self.crop_mode:
            self.crop_start = (event.x, event.y)
            self.crop_rect = self.canvas.create_rectangle(event.x, event.y, event.x, event.y, outline="red")
        elif self.draw_mode and self.image:
            self.push_undo()

    def on_mouse_drag(self, event):
        if self.draw_mode and self.image:
            x, y = self.canvas_to_image_coords(event.x, event.y)
            draw = ImageDraw.Draw(self.image)
            draw.ellipse((x - self.brush_size, y - self.brush_size,
                          x + self.brush_size, y + self.brush_size),
                         fill=self.brush_color)
            self.display()
        elif self.crop_mode and self.crop_start:
            self.canvas.coords(self.crop_rect, self.crop_start[0], self.crop_start[1], event.x, event.y)

    def on_mouse_up(self, event):
        if self.crop_mode and self.crop_start:
            x0, y0 = self.canvas_to_image_coords(*self.crop_start)
            x1, y1 = self.canvas_to_image_coords(event.x, event.y)
            self.crop_mode = False
            self.canvas.delete(self.crop_rect)
            self.crop_image(x0, y0, x1, y1)

    def crop_image(self, x0, y0, x1, y1):
        if self.image:
            self.push_undo()
            x0, x1 = sorted([max(0, x0), min(self.image.width, x1)])
            y0, y1 = sorted([max(0, y0), min(self.image.height, y1)])
            self.image = self.image.crop((x0, y0, x1, y1))
            self.display()

    def toggle_crop_mode(self):
        self.crop_mode = True
        messagebox.showinfo("Crop", "Click and drag to select crop area.")

    def on_mouse_wheel(self, event):
        if event.delta > 0:
            self.zoom_level *= 1.1
        else:
            self.zoom_level /= 1.1
        self.display()

    def canvas_to_image_coords(self, cx, cy):
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        x = int((cx - self.pan_x + canvas_width / 2) / self.zoom_level)
        y = int((cy - self.pan_y + canvas_height / 2) / self.zoom_level)
        return x, y

# Run
if __name__ == "__main__":
    root = tk.Tk()
    app = PhotoEditor(root)
    root.mainloop()
