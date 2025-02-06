import tkinter as tk
from PIL import Image, ImageTk
from tkinter import messagebox
import numpy as np

ventana = None
listaMatriz_2 = []
listaMatriz_3 = []
valida = None

##########INTERFAZ PRINCIPAL############
root = tk.Tk()
root.geometry("400x400+300+150")
root.resizable(width=False, height=False)
root.title("TALLER 2")
img = Image.open("IMAGES/numeros.jpg")
new = img.resize((400, 400))
background_image = ImageTk.PhotoImage(new)
background_label = tk.Label(root, image=background_image)
background_label.place(x=0, y=0, relwidth=1, relheight=1)
titulaso = tk.Label(root, text='ELIGE LA DIMENSION DE LA MATRIZ', font='Arial')
titulaso.place(x=60, y=50)
titulaso.config(bg="red")

boton = tk.Button(root, text="2X2", height=2, width=20)
boton.place(x=40, y=140)
boton.config(bg="yellow")
boton2 = tk.Button(root, text="3X3", height=2, width=20)
boton2.place(x=40, y=300)
boton2.config(bg="yellow")
imgMatriz2 = Image.open("IMAGES/matriz-2x2-2.jpg")
new2 = imgMatriz2.resize((150, 100))
back = ImageTk.PhotoImage(new2)
background = tk.Label(root, image=back)
background.place(x=220, y=110)
imgMatriz3 = Image.open("IMAGES/matriz-3x3.jpg")
new3 = imgMatriz3.resize((150, 100))
back2 = ImageTk.PhotoImage(new3)
background2 = tk.Label(root, image=back2)
background2.place(x=220, y=270)
root.mainloop()