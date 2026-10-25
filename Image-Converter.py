"""
Image Converter

Converts selected images to PNG while preserving supported metadata.
Original files can be moved to an "originals" folder or deleted.

To add file types, edit SUPPORTED_FORMATS below.
Requires Pillow: https://pillow.readthedocs.io/en/stable/
"""

import tkinter as tk
from tkinter import filedialog
from pathlib import Path
from PIL import Image, PngImagePlugin
import shutil


# EDIT HERE (1): Add or remove supported input file extensions.
# Format: file extension -> Pillow format name.
SUPPORTED_FORMATS = {
    ".webp": "WEBP",
    ".avif": "AVIF",
}

root = tk.Tk()
root.title("Image to PNG")
root.geometry("300x210")
root.resizable(False, False)
root.configure(bg="#181818")

keep_original = tk.BooleanVar(value=True)
selected_files = []
status = tk.StringVar(value="No files selected")


def select_files():
    global selected_files

    # EDIT HERE (2): The file picker updates automatically
    # when you change SUPPORTED_FORMATS above.
    extensions = " ".join(f"*{ext}" for ext in SUPPORTED_FORMATS)
    selected_files = list(filedialog.askopenfilenames(
        title="Select images",
        filetypes=[("Supported images", extensions),
                   ("All files", "*.*")]
    ))

    status.set(f"{len(selected_files)} file(s) selected")


def convert():
    if not selected_files:
        status.set("Select files first!")
        return

    converted = 0
    skipped = 0

    for file in selected_files:
        source = Path(file)
        destination = source.with_suffix(".png")

        # EDIT HERE (3): Skip existing PNGs to prevent overwriting.
        if destination.exists():
            print(f"Skipping {source.name}: PNG already exists.")
            skipped += 1
            continue

        try:
            with Image.open(source) as img:
                img.load()
                info = img.info
                metadata = PngImagePlugin.PngInfo()

                for key in ("Title", "Author", "Description",
                            "Copyright", "Comment"):
                    if key in info:
                        metadata.add_text(key, str(info[key]))

                if "xmp" in info:
                    xmp = info["xmp"]
                    if isinstance(xmp, bytes):
                        xmp = xmp.decode("utf-8", errors="replace")
                    metadata.add_itxt("XML:com.adobe.xmp", xmp)

                options = {"pnginfo": metadata}
                options.update({
                    key: info[key]
                    for key in ("exif", "icc_profile", "dpi")
                    if key in info
                })

                img.save(destination, format="PNG", **options)

            if keep_original.get():
                originals = source.parent / "originals"
                originals.mkdir(exist_ok=True)
                target = originals / source.name

                counter = 1
                while target.exists():
                    target = originals / f"{source.stem}_{counter}{source.suffix}"
                    counter += 1

                shutil.move(str(source), str(target))
            else:
                source.unlink()

            converted += 1

        except Exception as e:
            print(f"Error converting {source.name}: {e}")

    status.set(f"Converted {converted}, skipped {skipped}")
    selected_files.clear()


tk.Label(
    root, text="Image → PNG", font=("Arial", 16, "bold"),
    bg="#181818", fg="white"
).pack(pady=(15, 8))

tk.Checkbutton(
    root, text="Keep original files", variable=keep_original,
    bg="#181818", fg="white", selectcolor="#303030",
    activebackground="#181818", activeforeground="white"
).pack()

tk.Button(
    root, text="1. Select files", command=select_files,
    bg="#303030", fg="white", relief="flat",
    width=20, pady=5
).pack(pady=(8, 4))

tk.Button(
    root, text="2. Convert to PNG", command=convert,
    bg="#5278E8", fg="white", relief="flat",
    width=20, pady=5
).pack(pady=4)

tk.Label(
    root, textvariable=status, bg="#181818", fg="#BBBBBB",
    wraplength=280
).pack(pady=5)

root.mainloop()
