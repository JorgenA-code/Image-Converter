
"""
Pildi teisendaja.

Teisendab valitud pildid PNG-vormingusse ja säilitab toetatud metaandmed.
Originaalfailid saab alles jätta eraldi kausta või kustutada.

Vajab Pillow paketti: https://pillow.readthedocs.io/en/stable/
"""

import shutil
import tkinter as tk
from pathlib import Path
from tkinter import filedialog
from PIL import Image, PngImagePlugin


# Faililaiendite lisamine ja muutmine
SUPPORTED_EXTENSIONS = {
    ".webp", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif"
}

root = tk.Tk()
root.title("Image Converter")
root.geometry("320x230")
root.resizable(False, False)
root.configure(bg="#181818")

keep_original = tk.BooleanVar(value=True)
selected_files = []
status = tk.StringVar(value="No files selected")


def select_files():
    files = filedialog.askopenfilenames(
        title="Select images",
        filetypes=[
            (
                "Supported images",
                " ".join(f"*{ext}" for ext in sorted(SUPPORTED_EXTENSIONS))
            ),
            ("All files", "*.*")
        ]
    )

    selected_files.clear()
    selected_files.extend(files)
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

        try:
            with Image.open(source) as img:
                img.load()
                info = img.info
                metadata = PngImagePlugin.PngInfo()

                for key in (
                    "Title", "Author", "Description",
                    "Copyright", "Comment"
                ):
                    if key in info:
                        metadata.add_text(key, str(info[key]))

                if "xmp" in info:
                    xmp = info["xmp"]
                    if isinstance(xmp, bytes):
                        xmp = xmp.decode("utf-8", errors="replace")
                    metadata.add_itxt("XML:com.adobe.xmp", xmp)

                options = {
                    key: info[key]
                    for key in ("exif", "icc_profile", "dpi")
                    if key in info
                }
                options["pnginfo"] = metadata

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
                    target = originals / (
                        f"{source.stem}_{counter}{source.suffix}"
                    )
                    counter += 1

                shutil.move(str(source), str(target))
            else:
                source.unlink()

            converted += 1

        except FileExistsError:
            print(f"Skipping {source.name}: PNG already exists.")
            skipped += 1

        except Exception as error:
            print(f"Error processing {source.name}: {error}")
            failed += 1

            if created_destination and not png_saved:
                destination.unlink(missing_ok=True)

    status.set(
        f"Done: {converted} converted, "
        f"{skipped} skipped, {failed} failed"
    )
    selected_files.clear()


tk.Label(
    root,
    text="Image → PNG",
    font=("Arial", 16, "bold"),
    bg="#181818",
    fg="white"
).pack(pady=(15, 8))

tk.Checkbutton(
    root,
    text="Keep original files",
    variable=keep_original,
    bg="#181818",
    fg="white",
    selectcolor="#303030",
    activebackground="#181818",
    activeforeground="white"
).pack()

tk.Button(
    root,
    text="1. Select files",
    command=select_files,
    bg="#303030",
    fg="white",
    relief="flat",
    width=22,
    pady=5
).pack(pady=(8, 4))

tk.Button(
    root,
    text="2. Convert to PNG",
    command=convert,
    bg="#5278E8",
    fg="white",
    relief="flat",
    width=22,
    pady=5
).pack(pady=4)

tk.Label(
    root,
    textvariable=status,
    bg="#181818",
    fg="#BBBBBB",
    wraplength=300
).pack(pady=5)

tk.Label(
    root,
    text=f"Supported formats: {', '.join(sorted(SUPPORTED_EXTENSIONS))}",
    bg="#181818",
    fg="#BBBBBB",
    wraplength=300
).pack(pady=2)

root.mainloop()
