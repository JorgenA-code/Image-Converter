"""Erinevate pildi failide kuvaja ja muutja"""

import os
import tkinter as tk
from tkinter import filedialog
#import pillow

root = tk.Tk()
root.geometry("400x300")
root.title("Image Converter")
root.configure(background="#000000")
root.resizable(width=False, height=False)

title = tk.Label(root, text="Picture Converter", font=("Arial", 12), bg="#000000", fg="#FFFFFF")
title.place(x=200, y=25, width=250, height=75, anchor="center")


def ask_folder():
    pictures_folder = filedialog.askdirectory()
    
 
    
def ask_files():
    picture_files = filedialog.askopenfilenames()



button_ask_folder = tk.Button(root, text="Choose Folder", bg="#000000", fg="#FFFFFF", command=ask_folder)
button_ask_folder.place(x=40, y=110, height=25, width=120)

button_ask_files = tk.Button(root, text="Choose Files", bg="#000000", fg="#FFFFFF", command=ask_files)
button_ask_files.place(x=200, y=110, height=25, width=120)

# muuda neid nimesi
filepath = tk.Label(root, text=" ",anchor="center", font=("Arial", 8), bg="#000000", fg="#FFFFFF", wraplength=200)
filepath.place(x=0, y=50, height=50, width=200)

example_text = tk.Label(root, text='Text test', anchor="center",
                font=("Arial", 12), bg="#000000", fg="#FF0000", wraplength=200)
example_text.place(x=0, y=150, height=120, width=200,)

root.mainloop()  # Keeps window open





