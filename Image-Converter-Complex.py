
#install https://pillow.readthedocs.io/en/stable/
import shutil
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
from PIL import Image, PngImagePlugin

# -------------------- SETTINGS --------------------

SUPPORTED_INPUTS = {".webp", ".avif"}
ORIGINALS_FOLDER = "Originals"

BG = "#111318"
PANEL = "#1B1F27"
INPUT_BG = "#252B36"
ACCENT = "#6C8CFF"
TEXT = "#F3F4F6"
MUTED = "#A0A8B8"
SUCCESS = "#65D6A3"
ERROR = "#FF7777"

# -------------------- WINDOW --------------------

root = tk.Tk()
root.title("Picture Converter")
root.geometry("620x700")
root.resizable(False, False)
root.configure(bg=BG)

selected_files = []
busy = False


# -------------------- FUNCTIONS --------------------

def update_status(message, color=MUTED):
    status_label.config(text=message, fg=color)


def refresh_file_list():
    file_list.delete(0, tk.END)

    for path in selected_files:
        file_list.insert(tk.END, str(path))

    count_label.config(text=f"{len(selected_files)} file(s) selected")


def add_files(paths):
    existing = set(selected_files)

    for path in paths:
        path = Path(path)

        if path.is_file() and path.suffix.lower() in SUPPORTED_INPUTS:
            if path not in existing:
                selected_files.append(path)
                existing.add(path)

    refresh_file_list()

    if selected_files:
        update_status("Ready to convert", SUCCESS)
    else:
        update_status("No supported images found", ERROR)


def ask_files():
    files = filedialog.askopenfilenames(
        title="Select WebP or AVIF images",
        filetypes=[
            ("Supported images", "*.webp *.avif"),
            ("WebP images", "*.webp"),
            ("AVIF images", "*.avif"),
        ],
    )

    if files:
        add_files(files)


def ask_folder():
    folder = filedialog.askdirectory(title="Choose an image folder")

    if not folder:
        return

    paths = [
        path for path in Path(folder).iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_INPUTS
    ]

    add_files(paths)


def clear_files():
    if busy:
        return

    selected_files.clear()
    refresh_file_list()
    update_status("Selection cleared")


def convert_one(source, output_format, keep_originals, jpg_quality):
    """Convert an image, preserving supported metadata where possible."""

    extension = ".png" if output_format == "PNG" else ".jpg"
    destination = source.with_suffix(extension)

    # Avoid overwriting an existing output image.
    if destination.exists():
        counter = 1

        while True:
            destination = source.with_name(
                f"{source.stem}_converted_{counter}{extension}"
            )

            if not destination.exists():
                break

            counter += 1

    with Image.open(source) as image:
        image.load()
        info = image.info.copy()

        # Metadata supported by both JPEG and PNG encoders.
        metadata = {}

        for key in ("exif", "icc_profile", "dpi"):
            if key in info:
                metadata[key] = info[key]

        if output_format == "JPG":
            # JPEG does not support transparency.
            rgba = image.convert("RGBA")
            background = Image.new("RGB", rgba.size, "white")

            if "A" in rgba.getbands():
                background.paste(rgba, mask=rgba.getchannel("A"))
            else:
                background.paste(rgba)

            background.save(
                destination,
                format="JPEG",
                quality=jpg_quality,
                optimize=True,
                **metadata,
            )

        else:
            # Preserve transparency in PNG.
            if image.mode not in ("1", "L", "LA", "P", "RGB", "RGBA"):
                image = image.convert("RGBA")

            # Copy textual metadata into PNG text chunks.
            pnginfo = PngImagePlugin.PngInfo()

            reserved_keys = {
                "exif", "icc_profile", "dpi", "transparency",
                "duration", "loop", "background", "timestamp",
                "xmp", "jfif", "jfif_version", "jfif_unit",
                "jfif_density",
            }

            for key, value in info.items():
                if (
                    key not in reserved_keys
                    and isinstance(key, str)
                    and isinstance(value, (str, int, float))
                ):
                    try:
                        pnginfo.add_text(key, str(value))
                    except (TypeError, ValueError):
                        pass

            image.save(
                destination,
                format="PNG",
                optimize=True,
                pnginfo=pnginfo,
                **metadata,
            )

    # Only move/delete the source after successful conversion.
    if keep_originals:
        originals_dir = source.parent / ORIGINALS_FOLDER
        originals_dir.mkdir(exist_ok=True)

        original_destination = originals_dir / source.name
        counter = 1

        while original_destination.exists():
            original_destination = originals_dir / (
                f"{source.stem}_{counter}{source.suffix}"
            )
            counter += 1

        shutil.move(str(source), str(original_destination))

    else:
        source.unlink()

    return destination


def start_conversion():
    global busy

    if busy:
        return

    if not selected_files:
        messagebox.showwarning(
            "No images",
            "Choose a folder or select some images first."
        )
        return

    output_format = format_var.get()
    keep_originals = keep_var.get()
    jpg_quality = int(quality_var.get())

    if keep_originals:
        confirm_text = (
            f"Convert {len(selected_files)} image(s) to {output_format}?\n\n"
            f"Originals will be moved into '{ORIGINALS_FOLDER}' folders."
        )
    else:
        confirm_text = (
            f"Convert {len(selected_files)} image(s) to {output_format}?\n\n"
            "Originals will be deleted after successful conversion."
        )

    if not messagebox.askyesno("Confirm conversion", confirm_text):
        return

    files_to_convert = selected_files.copy()

    busy = True
    convert_button.config(state="disabled")
    clear_button.config(state="disabled")
    select_folder_button.config(state="disabled")
    select_files_button.config(state="disabled")

    progress_bar["maximum"] = len(files_to_convert)
    progress_bar["value"] = 0
    update_status("Converting images...", ACCENT)

    def worker():
        results = []
        errors = []

        for index, source in enumerate(files_to_convert, start=1):
            try:
                destination = convert_one(
                    source,
                    output_format,
                    keep_originals,
                    jpg_quality,
                )
                results.append(f"OK: {source.name} -> {destination.name}")

            except Exception as exc:
                errors.append(f"{source.name}: {exc}")

            root.after(
                0,
                lambda value=index: progress_bar.config(value=value)
            )

        root.after(0, lambda: finish_conversion(results, errors))

    threading.Thread(target=worker, daemon=True).start()


def finish_conversion(results, errors):
    global busy

    busy = False

    convert_button.config(state="normal")
    clear_button.config(state="normal")
    select_folder_button.config(state="normal")
    select_files_button.config(state="normal")

    failed_names = {
        line.split(": ", 1)[0] for line in errors
    }

    # Keep failed files selected so they can be retried.
    selected_files[:] = [
        path for path in selected_files
        if path.name in failed_names
    ]

    refresh_file_list()

    update_status(
        f"Finished: {len(results)} successful, {len(errors)} failed",
        SUCCESS if not errors else ERROR,
    )

    log_text.config(state="normal")
    log_text.delete("1.0", tk.END)

    for line in results:
        log_text.insert(tk.END, line + "\n", "success")

    for line in errors:
        log_text.insert(tk.END, "ERROR: " + line + "\n", "error")

    log_text.config(state="disabled")

    messagebox.showinfo(
        "Conversion finished",
        f"Successful: {len(results)}\nFailed: {len(errors)}"
    )


def update_quality_label(value):
    quality_value_label.config(text=str(int(float(value))))


def update_quality_visibility(*args):
    if format_var.get() == "JPG":
        quality_frame.pack(fill="x", pady=(12, 0))
    else:
        quality_frame.pack_forget()


# -------------------- STYLING --------------------

style = ttk.Style()
style.theme_use("clam")

style.configure(
    "Custom.Horizontal.TProgressbar",
    troughcolor=INPUT_BG,
    background=ACCENT,
    bordercolor=INPUT_BG,
    lightcolor=ACCENT,
    darkcolor=ACCENT,
)

# -------------------- HEADER --------------------

header = tk.Frame(root, bg=BG)
header.pack(fill="x", padx=28, pady=(20, 10))

tk.Label(
    header,
    text="PICTURE CONVERTER",
    bg=BG,
    fg=TEXT,
    font=("Arial", 19, "bold"),
).pack(anchor="w")

tk.Label(
    header,
    text="Convert WebP and AVIF images to PNG or JPG",
    bg=BG,
    fg=MUTED,
    font=("Arial", 10),
).pack(anchor="w", pady=(5, 0))

# -------------------- FILE SELECTION --------------------

selection_panel = tk.Frame(root, bg=PANEL, padx=16, pady=12)
selection_panel.pack(fill="x", padx=24, pady=7)

tk.Label(
    selection_panel,
    text="1. Select images",
    bg=PANEL,
    fg=TEXT,
    font=("Arial", 11, "bold"),
).pack(anchor="w", pady=(0, 8))

button_row = tk.Frame(selection_panel, bg=PANEL)
button_row.pack(fill="x")

select_folder_button = tk.Button(
    button_row,
    text="Choose folder",
    command=ask_folder,
    bg=ACCENT,
    fg="white",
    activebackground="#5475E8",
    activeforeground="white",
    relief="flat",
    cursor="hand2",
    font=("Arial", 10, "bold"),
    padx=12,
    pady=7,
)
select_folder_button.pack(side="left", padx=(0, 8))

select_files_button = tk.Button(
    button_row,
    text="Choose files",
    command=ask_files,
    bg=INPUT_BG,
    fg=TEXT,
    activebackground="#353D4D",
    activeforeground=TEXT,
    relief="flat",
    cursor="hand2",
    font=("Arial", 10),
    padx=12,
    pady=7,
)
select_files_button.pack(side="left")

clear_button = tk.Button(
    button_row,
    text="Clear",
    command=clear_files,
    bg=PANEL,
    fg=MUTED,
    activebackground=PANEL,
    activeforeground=TEXT,
    relief="flat",
    cursor="hand2",
    font=("Arial", 9),
)
clear_button.pack(side="right")

count_label = tk.Label(
    selection_panel,
    text="0 file(s) selected",
    bg=PANEL,
    fg=MUTED,
    font=("Arial", 9),
)
count_label.pack(anchor="w", pady=(10, 5))

file_frame = tk.Frame(selection_panel, bg=INPUT_BG)
file_frame.pack(fill="x")

file_scroll = tk.Scrollbar(file_frame)
file_scroll.pack(side="right", fill="y")

file_list = tk.Listbox(
    file_frame,
    height=3,
    bg=INPUT_BG,
    fg=TEXT,
    selectbackground=ACCENT,
    selectforeground="white",
    font=("Arial", 9),
    relief="flat",
    highlightthickness=0,
    yscrollcommand=file_scroll.set,
    activestyle="none",
)
file_list.pack(side="left", fill="both", expand=True, padx=6, pady=6)
file_scroll.config(command=file_list.yview)

# -------------------- OUTPUT OPTIONS --------------------

options_panel = tk.Frame(root, bg=PANEL, padx=16, pady=12)
options_panel.pack(fill="x", padx=24, pady=7)

tk.Label(
    options_panel,
    text="2. Conversion settings",
    bg=PANEL,
    fg=TEXT,
    font=("Arial", 11, "bold"),
).pack(anchor="w", pady=(0, 10))

format_row = tk.Frame(options_panel, bg=PANEL)
format_row.pack(fill="x")

tk.Label(
    format_row,
    text="Output format",
    bg=PANEL,
    fg=MUTED,
    font=("Arial", 10),
).pack(side="left")

format_var = tk.StringVar(value="PNG")

for label in ("PNG", "JPG"):
    tk.Radiobutton(
        format_row,
        text=label,
        variable=format_var,
        value=label,
        bg=PANEL,
        fg=TEXT,
        selectcolor=INPUT_BG,
        activebackground=PANEL,
        activeforeground=TEXT,
        font=("Arial", 10),
    ).pack(side="left", padx=(16, 0))

# JPG quality slider (1-100).
quality_frame = tk.Frame(options_panel, bg=PANEL)

quality_header = tk.Frame(quality_frame, bg=PANEL)
quality_header.pack(fill="x")

tk.Label(
    quality_header,
    text="JPG quality",
    bg=PANEL,
    fg=MUTED,
    font=("Arial", 10),
).pack(side="left")

quality_value_label = tk.Label(
    quality_header,
    text="90",
    bg=PANEL,
    fg=TEXT,
    font=("Arial", 10, "bold"),
)
quality_value_label.pack(side="right")

quality_var = tk.IntVar(value=90)

tk.Scale(
    quality_frame,
    from_=1,
    to=100,
    orient="horizontal",
    variable=quality_var,
    command=update_quality_label,
    bg=PANEL,
    fg=TEXT,
    troughcolor=INPUT_BG,
    activebackground=ACCENT,
    highlightthickness=0,
    showvalue=False,
    resolution=1,
).pack(fill="x")

tk.Label(
    quality_frame,
    text="Smaller file  ←                 →  Better quality",
    bg=PANEL,
    fg=MUTED,
    font=("Arial", 8),
).pack(fill="x")

keep_var = tk.BooleanVar(value=True)

tk.Checkbutton(
    options_panel,
    text="Keep originals in an 'Originals' subfolder",
    variable=keep_var,
    bg=PANEL,
    fg=TEXT,
    selectcolor=INPUT_BG,
    activebackground=PANEL,
    activeforeground=TEXT,
    font=("Arial", 10),
).pack(anchor="w", pady=(10, 3))

tk.Label(
    options_panel,
    text="Unchecked = delete originals after successful conversion.",
    bg=PANEL,
    fg=MUTED,
    font=("Arial", 9),
).pack(anchor="w")

format_var.trace_add("write", update_quality_visibility)
update_quality_visibility()

# -------------------- CONVERSION --------------------

convert_button = tk.Button(
    root,
    text="CONVERT IMAGES",
    command=start_conversion,
    bg=ACCENT,
    fg="white",
    activebackground="#5475E8",
    activeforeground="white",
    disabledforeground="#A0A8B8",
    relief="flat",
    cursor="hand2",
    font=("Arial", 11, "bold"),
    pady=10,
)
convert_button.pack(fill="x", padx=24, pady=(9, 7))

progress_bar = ttk.Progressbar(
    root,
    style="Custom.Horizontal.TProgressbar",
    mode="determinate",
)
progress_bar.pack(fill="x", padx=24, pady=(0, 5))

status_label = tk.Label(
    root,
    text="Ready",
    bg=BG,
    fg=MUTED,
    font=("Arial", 9),
)
status_label.pack(anchor="w", padx=26)

# -------------------- LOG --------------------

log_frame = tk.Frame(root, bg=BG)
log_frame.pack(fill="both", expand=True, padx=24, pady=(7, 12))

tk.Label(
    log_frame,
    text="Conversion log",
    bg=BG,
    fg=TEXT,
    font=("Arial", 9, "bold"),
).pack(anchor="w", pady=(0, 4))

log_text = tk.Text(
    log_frame,
    height=3,
    bg=INPUT_BG,
    fg=TEXT,
    font=("Consolas", 8),
    relief="flat",
    state="disabled",
    wrap="word",
)
log_text.pack(fill="both", expand=True)
log_text.tag_config("success", foreground=SUCCESS)
log_text.tag_config("error", foreground=ERROR)

root.mainloop()
