"""Erinevate pildi failide kuvaja ja muutja"""

import os
import tkinter as tk
#import pillow

root = tk.Tk()
root.geometry("200x450")
root.title("Resizer")
root.configure(background="#000000")
root.resizable(width=False, height=False)

title = tk.Label(root, text="Picture Converter", font=("Arial", 12), bg="#000000", fg="#FFFFFF")
title.place(x=100, y=25, width=250, height=75, anchor="center")



button_mingi = tk.Button(root, text="Choose Folder", bg="#000000", fg="#FFFFFF", command=buttonFunction)
button_mingi.place(x=40, y=110, height=25, width=120)

filepath = tk.Label(root, text=" ",anchor="center", font=("Arial", 8), bg="#000000", fg="#FFFFFF", wraplength=200)
filepath.place(x=0, y=50, height=50, width=200)

dont = tk.Label(root, text='Text test', anchor="center",
                font=("Arial", 12), bg="#000000", fg="#FF0000", wraplength=200)
dont.place(x=0, y=330, height=120, width=200,)

root.mainloop()  # Keeps window open
#123123


#window avaneb
#Seleclt folder / select files
# if folder kuidagi ainult teatud file extensionid
#milline compresser muutja kinda
#kas jätta alles originaalid
# do the thing button
