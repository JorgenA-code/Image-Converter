"""
Image Converter

Converts supported images to PNG and preserves supported metadata.
Originals can be moved to an "originals" folder or deleted.

Edit SUPPORTED_EXTENSIONS to change input formats.
Requires Pillow: https://pillow.readthedocs.io/en/stable/
"""

import tkinter as tk
from tkinter import filedialog
from pathlib import Path
from PIL import Image, PngImagePlugin
import shutil


# EDIT HERE (1): Supported input formats.
SUPPORTED_EXTENSIONS = {
    ".webp", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif"
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

    extensions = " ".join(f"*{ext}" for ext in sorted(SUPPORTED_EXTENSIONS))
    selected_files = list(filedialog.askopenfilenames(
        title="Select images",
        filetypes=[("Supported images", extensions)]
    ))
    status.set(f"{len(selected_files)} file(s) selected")


def convert():
    if not selected_files:
        status.set("Select files first!")
        return

    converted = skipped = failed = 0

    for file in selected_files:
        source = Path(file)
        destination = source.with_suffix(".png")
        created_destination = False
        png_saved = False

        # EDIT HERE (2): Never overwrite an existing PNG.
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

                # "xb" creates a new file and refuses to overwrite an existing one.
                with destination.open("xb") as output:
                    created_destination = True
                    img.save(output, format="PNG", **options)

                png_saved = True

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

        except FileExistsError:
            print(f"Skipping {source.name}: PNG already exists.")
            skipped += 1

        except Exception as e:
            print(f"Error processing {source.name}: {e}")
            failed += 1

            # Remove an incomplete PNG, but keep a successfully saved one.
            if created_destination and not png_saved:
                destination.unlink(missing_ok=True)

        # A successfully saved PNG is retained if moving/deleting the
        # original fails, so the converted image is not lost.

    status.set(
        f"Done: {converted} converted, {skipped} skipped, {failed} failed"
    )
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
