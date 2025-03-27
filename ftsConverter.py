import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import numpy as np
from astropy.io import fits
from PIL import Image, ImageEnhance, ImageTk

def normalise_data(data):
    """
    normalise the image data to a 0-255 range using linear stretching.
    """
    data = data - np.min(data)
    if np.max(data) != 0:
        data = data / np.max(data) * 255.0
    return data.astype(np.uint8)

def load_fits_image(filepath, auto_normalise=True):
    """
    Open an FTS/FITS file and return a PIL Image.
    """
    hdulist = fits.open(filepath)
    data = hdulist[0].data
    hdulist.close()
    if data is None:
        raise ValueError("No image data found.")
    if auto_normalise:
        image_data = normalise_data(data)
    else:
        image_data = data

    # Create a grayscale image if 2D, or RGB if 3D.
    if image_data.ndim == 2:
        img = Image.fromarray(image_data, mode="L")
    elif image_data.ndim == 3:
        img = Image.fromarray(image_data)
    else:
        raise ValueError("Unsupported image dimensions.")
    return img

def apply_adjustments(img, brightness=1.0, contrast=1.0, rotation=0):
    """
    Adjust brightness, contrast, and rotation.
    """
    enhancer_b = ImageEnhance.Brightness(img)
    img = enhancer_b.enhance(brightness)
    enhancer_c = ImageEnhance.Contrast(img)
    img = enhancer_c.enhance(contrast)
    if rotation != 0:
        img = img.rotate(rotation, expand=True)
    return img

def convert_file(filepath, output_format, auto_normalise=True, brightness=1.0, contrast=1.0, rotation=0):
    """
    Load a FITS/FTS file, apply adjustments, and save it with the chosen output format.
    """
    try:
        img = load_fits_image(filepath, auto_normalise=auto_normalise)
        img = apply_adjustments(img, brightness, contrast, rotation)
        base, _ = os.path.splitext(filepath)
        new_filepath = f"{base}.{output_format.lower()}"
        img.save(new_filepath)
        return new_filepath
    except Exception as e:
        print(f"Error converting {filepath}: {e}")
        return None

class ConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("FTS/FITS File Converter")
        self.selected_files = []
        self.output_format = tk.StringVar(value="PNG")
        self.auto_normalise = tk.BooleanVar(value=True)
        self.brightness = tk.DoubleVar(value=1.0)
        self.contrast = tk.DoubleVar(value=1.0)
        self.rotation = tk.IntVar(value=0)
        self.create_widgets()

    def create_widgets(self):
        # File selection and preview buttons.
        file_frame = tk.Frame(self.root)
        file_frame.pack(pady=5)

        select_button = tk.Button(file_frame, text="Select Files", command=self.select_files)
        select_button.pack(side=tk.LEFT, padx=5)

        preview_button = tk.Button(file_frame, text="Preview Selected", command=self.preview_file)
        preview_button.pack(side=tk.LEFT, padx=5)

        self.file_label = tk.Label(file_frame, text="No files selected")
        self.file_label.pack(side=tk.LEFT, padx=5)

        # Output format options.
        format_frame = tk.LabelFrame(self.root, text="Output Format")
        format_frame.pack(pady=5, fill="x", padx=10)
        for fmt in ["PNG", "TIFF", "JPG", "BMP"]:
            rb = tk.Radiobutton(format_frame, text=fmt, variable=self.output_format, value=fmt)
            rb.pack(side=tk.LEFT, padx=5)

        # Auto-normalise checkbox.
        norm_check = tk.Checkbutton(self.root, text="Auto Normalise", variable=self.auto_normalise)
        norm_check.pack(pady=5)

        # Adjustment controls.
        adjust_frame = tk.LabelFrame(self.root, text="Adjustments")
        adjust_frame.pack(pady=5, fill="x", padx=10)

        tk.Label(adjust_frame, text="Brightness:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        brightness_slider = tk.Scale(adjust_frame, from_=0.5, to=2.0, resolution=0.1, orient=tk.HORIZONTAL, variable=self.brightness)
        brightness_slider.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(adjust_frame, text="Contrast:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        contrast_slider = tk.Scale(adjust_frame, from_=0.5, to=2.0, resolution=0.1, orient=tk.HORIZONTAL, variable=self.contrast)
        contrast_slider.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(adjust_frame, text="Rotation:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        rotation_slider = tk.Scale(adjust_frame, from_=0, to=360, resolution=1, orient=tk.HORIZONTAL, variable=self.rotation)
        rotation_slider.grid(row=2, column=1, padx=5, pady=5)

        # Convert button.
        convert_button = tk.Button(self.root, text="Convert Files", command=self.convert_files)
        convert_button.pack(pady=5)

        # Progress bar.
        self.progress = ttk.Progressbar(self.root, orient=tk.HORIZONTAL, length=300, mode="determinate")
        self.progress.pack(pady=5)

        # Log text widget.
        self.log_text = tk.Text(self.root, height=10, width=60)
        self.log_text.pack(pady=5)

    def select_files(self):
        filetypes = [("FTS Files", "*.fts"), ("FITS Files", "*.fits"), ("All Files", "*.*")]
        files = filedialog.askopenfilenames(title="Select FTS/FITS Files", filetypes=filetypes)
        if files:
            self.selected_files = list(files)
            self.file_label.config(text=f"{len(self.selected_files)} files selected")
            self.log(f"Selected {len(self.selected_files)} files.")
        else:
            self.log("No files selected.")

    def preview_file(self):
        """
        Preview the first selected file with current adjustment settings.
        """
        if not self.selected_files:
            messagebox.showwarning("No Files", "Please select a file to preview.")
            return
        try:
            filepath = self.selected_files[0]
            img = load_fits_image(filepath, auto_normalise=self.auto_normalise.get())
            img = apply_adjustments(img, self.brightness.get(), self.contrast.get(), self.rotation.get())
            # Create a thumbnail for preview.
            preview_img = img.copy()
            preview_img.thumbnail((300,300))
            preview_window = tk.Toplevel(self.root)
            preview_window.title("Preview")
            img_tk = ImageTk.PhotoImage(preview_img)
            label = tk.Label(preview_window, image=img_tk)
            label.image = img_tk  # Keep a reference to avoid garbage collection.
            label.pack()
            self.log(f"Previewing {os.path.basename(filepath)}")
        except Exception as e:
            messagebox.showerror("Preview Error", str(e))
            self.log(f"Error previewing file: {e}")

    def convert_files(self):
        if not self.selected_files:
            messagebox.showwarning("No Files", "Please select files to convert.")
            return

        output_format = self.output_format.get()
        self.log(f"Starting conversion to {output_format}...")
        total_files = len(self.selected_files)
        self.progress["maximum"] = total_files
        self.progress["value"] = 0

        for i, filepath in enumerate(self.selected_files, start=1):
            filename = os.path.basename(filepath)
            self.log(f"Converting: {filename}")
            result = convert_file(
                filepath, 
                output_format, 
                auto_normalise=self.auto_normalise.get(), 
                brightness=self.brightness.get(), 
                contrast=self.contrast.get(), 
                rotation=self.rotation.get()
            )
            if result:
                self.log(f"Saved: {result}")
            else:
                self.log(f"Failed to convert: {filename}")
            self.progress["value"] = i
            self.root.update_idletasks()
        self.log("Conversion completed.")

    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = ConverterApp(root)
    root.mainloop()
