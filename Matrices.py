import tkinter as tk
from PIL import Image, ImageTk
from tkinter import messagebox
import numpy as np

ventana = None
listaMatriz_2 = []
listaMatriz_3 = []
valida = None

def numero(num):
    if num > 0:
        return f"+ {num}"
    elif num < 0:
        return num
    else:
        return f"+ {num}"
def polinomio_caracteristico ():
    global valida
    global ventana
    if valida == 2:
        vn2 = ventana
        global listaMatriz_2
        for entry in listaMatriz_2:
            if not entry.get():
                messagebox.showerror("Error", "Complete todos los datos.")
                return
            elif not is_float(entry.get()) :
                messagebox.showerror("Error", "Se ingresa solo numeros.")
                return
        x1 = float(listaMatriz_2[0].get())
        y1 = float(listaMatriz_2[1].get())
        x2 = float(listaMatriz_2[2].get())
        y2 = float(listaMatriz_2[3].get())   
        q = round((-x1 -y2),2)
        r = round((x1 * y2) - (y1 * x2),2)
        labelpoli2 = tk.Label(vn2, text =f" λ^2  {numero(q)}λ  {numero(r)} ",width=30,height=2)
        labelpoli2.place(x=200,y=160)
        return labelpoli2
    else:
        vn3 = ventana
        global listaMatriz_3
        for entry in listaMatriz_3:
            if not entry.get():
                messagebox.showerror("Error", "Complete todos los datos.")
                return
            elif not is_float(entry.get()) :
                messagebox.showerror("Error", "Se ingresa solo numeros.")
                return
        x1 = float(listaMatriz_3[0].get())
        y1 = float(listaMatriz_3[1].get())
        z1 = float(listaMatriz_3[2].get())
        x2 = float(listaMatriz_3[3].get())
        y2 = float(listaMatriz_3[4].get())
        z2 = float(listaMatriz_3[5].get())
        x3 = float(listaMatriz_3[6].get())
        y3 = float(listaMatriz_3[7].get())
        z3 = float(listaMatriz_3[8].get())
        p1 = round(x1 + z3 + y2, 2)
        p2 = round(y3*z2 -(y2*z3) - (y2*x1) - (z3*x1) + x2*y1 + x3*z1, 2)
        p3 = round(x1*y2*z3 - y3*z2*x1 - y1*x2*z3 + x3*z2*y1 + z1*x2*y3 - x3*y2*z1, 2)
        ecuacion = f" -λ^3  {numero(p1)}λ^2  {numero(p2)}λ  {numero(p3)} "
        labelpoli3 = tk.Label(vn3, text =ecuacion,width=30,height=2)
        labelpoli3.place(x=200,y=180)
        return labelpoli3
def valores_propios():
    global valida
    global ventana
    if valida == 2:
        vn2 = ventana
        global listaMatriz_2
        for entry in listaMatriz_2:
            if not entry.get():
                messagebox.showerror("Error", "Complete todos los datos.")
                return
            elif not is_float(entry.get()) :
                messagebox.showerror("Error", "Se ingresa solo numeros.")
                return
        x1 = float(listaMatriz_2[0].get())
        y1 = float(listaMatriz_2[1].get())
        x2 = float(listaMatriz_2[2].get())
        y2 = float(listaMatriz_2[3].get())   
        matriz= np.array([[x1, y1],
                          [x2, y2]]) 
        valores_propios = np.linalg.eigvals(matriz)
        almacena =""
        for valor in valores_propios:
            almacena = f" {almacena}  {round(valor, 2)} ;"
        labelvalores2 = tk.Label(vn2, text = almacena ,width=30,height=2)
        labelvalores2.place(x=200,y=220)
        return labelvalores2
    else:
        vn3 = ventana
        global listaMatriz_3
        for entry in listaMatriz_3:
            if not entry.get():
                messagebox.showerror("Error", "Complete todos los datos.")
                return
            elif not is_float(entry.get()) :
                messagebox.showerror("Error", "Se ingresa solo numeros.")
                return
        x1 = float(listaMatriz_3[0].get())
        y1 = float(listaMatriz_3[1].get())
        z1 = float(listaMatriz_3[2].get())
        x2 = float(listaMatriz_3[3].get())
        y2 = float(listaMatriz_3[4].get())
        z2 = float(listaMatriz_3[5].get())
        x3 = float(listaMatriz_3[6].get())
        y3 = float(listaMatriz_3[7].get())
        z3 = float(listaMatriz_3[8].get())
        matriz = np.array([[x1, y1, z1],
                           [x2, y2, z2],
                           [x3, y3, z3]])
        valores_propios = np.linalg.eigvals(matriz)
        almacena = ""
        for valor in valores_propios:
            almacena = f" {almacena} {round(valor)} ;"
        labelvalores3 = tk.Label(vn3, text = almacena,width=30,height=2)
        labelvalores3.place(x=200,y=240) 
        return labelvalores3      
def vectores_propios():
    global valida
    global ventana
    if valida == 2:
        vn2 = ventana
        global listaMatriz_2
        for entry in listaMatriz_2:
            if not entry.get():
                messagebox.showerror("Error", "Complete todos los datos.")
                return
            elif not is_float(entry.get()):
                messagebox.showerror("Error", "Se ingresa solo números.")
                return
        x1 = float(listaMatriz_2[0].get())
        y1 = float(listaMatriz_2[1].get())
        x2 = float(listaMatriz_2[2].get())
        y2 = float(listaMatriz_2[3].get())
        matriz = np.array([[x1, y1],
                           [x2, y2]])
        valores_propios, vectores_propios = np.linalg.eig(matriz)
        almacena = ""
        for i in range(len(vectores_propios)):
            vector = vectores_propios[:, i]
            almacena += f"Vector {i + 1}: {vector}\n"

        labelVectores2 = tk.Label(vn2, text=almacena, width=40, height=3)
        labelVectores2.place(x=200, y=280)
    else:
        vn3 = ventana
        global listaMatriz_3
        for entry in listaMatriz_3:
            if not entry.get():
                messagebox.showerror("Error", "Complete todos los datos.")
                return
            elif not is_float(entry.get()):
                messagebox.showerror("Error", "Se ingresa solo números.")
                return
        x1 = float(listaMatriz_3[0].get())
        y1 = float(listaMatriz_3[1].get())
        z1 = float(listaMatriz_3[2].get())
        x2 = float(listaMatriz_3[3].get())
        y2 = float(listaMatriz_3[4].get())
        z2 = float(listaMatriz_3[5].get())
        x3 = float(listaMatriz_3[6].get())
        y3 = float(listaMatriz_3[7].get())
        z3 = float(listaMatriz_3[8].get())
        matriz = np.array([[x1, y1, z1],
                           [x2, y2, z2],
                           [x3, y3, z3]])
        valores_propios, vectores_propios = np.linalg.eig(matriz)
        almacena = ""
        for i in range(len(vectores_propios)):
            vector = vectores_propios[:, i]
            almacena += f"Vector {i + 1}: {vector}\n"
        labelvectores3 = tk.Label(vn3, text=almacena, width=50, height=5)
        labelvectores3.place(x=185, y=300)
def limpiar_campos2():
    for entry in listaMatriz_2:
        entry.delete(0, 'end')
def limpiar_campos3():
    for entry in listaMatriz_3:
        entry.delete(0, 'end')
def dimension2():
    root.withdraw()
    vn2 = tk.Tk()
    global ventana
    ventana = vn2
    vn2.title("MATRIZ DE 2X2")
    vn2.geometry("600x400+300+150")
    vn2.config(bg="skyblue")
    vn2.resizable(width=False, height=False)
    tituloV2 = tk.Label(vn2, text='Ingrese valores de la matriz', font='Arial')
    tituloV2.place(x=100, y=20)
    tituloV2.config(bg="gray")
    ingreso_x1 = tk.Label(vn2, text='x1:')
    ingreso_x1.place(x=30,y=70)
    entra_x1 = tk.Entry(vn2,width=5)
    entra_x1.place(x=60,y=70)
    ingreso_y1 = tk.Label(vn2, text = 'y1:')
    ingreso_y1.place(x=100,y=70)
    entra_y1 = tk.Entry(vn2,width=5)
    entra_y1.place(x=130,y=70)
    ingreso_x2 = tk.Label(vn2, text='x2:')
    ingreso_x2.place(x=30,y=100)
    entra_x2 = tk.Entry(vn2,width=5)
    entra_x2.place(x=60,y=100)
    ingreso_y2 = tk.Label(vn2, text = 'y2:')
    ingreso_y2.place(x=100,y=100)
    entra_y2 = tk.Entry(vn2,width=5)
    entra_y2.place(x=130,y=100) 
    global listaMatriz_2   
    listaMatriz_2 = [entra_x1,entra_y1,entra_x2,entra_y2]
    global valida
    valida = 2
    boton_Polinomio = tk.Button(vn2, text="Polinomio Caracteristico", height=2, width=20,command=polinomio_caracteristico)
    boton_Polinomio.place(x=30, y=160)
    boton_Polinomio.config(bg="yellow")
    boton_ValoresPropios = tk.Button(vn2, text="Valores Propios", height=2, width=20,command=valores_propios)
    boton_ValoresPropios.place(x=30, y=220)
    boton_ValoresPropios.config(bg="yellow")
    boton_VectoresPropios = tk.Button(vn2, text="Vectores Propios", height=2, width=20,command=vectores_propios)
    boton_VectoresPropios.place(x=30, y=280)
    boton_VectoresPropios.config(bg="yellow")
    boton_limpiar = tk.Button(vn2, text="Limpiar", command=limpiar_campos2)
    boton_limpiar.place(x=30, y=340)
    boton_limpiar.config(bg="blue")
    boton_volver = tk.Button(vn2, text="Volver", height=2, width=20, command=volver)
    boton_volver.place(x=240, y=350)
    boton_volver.config(bg="red")
    vn2.mainloop()
def dimension3():
    global ventana
    root.withdraw()
    vn3 = tk.Tk()
    ventana = vn3
    vn3.title("MATRIZ DE 3X3")
    vn3.geometry("630x480+300+150")
    vn3.config(bg="skyblue")
    vn3.resizable(width=False, height=False)
    tituloV3 = tk.Label(vn3, text='Ingrese valores de la matriz', font='Arial')
    tituloV3.place(x=100, y=20)
    tituloV3.config(bg="gray")
    ingreso_x1 = tk.Label(vn3, text='x1:')
    ingreso_x1.place(x=30,y=70)
    entra_x1 = tk.Entry(vn3,width=5)
    entra_x1.place(x=60,y=70)
    ingreso_y1 = tk.Label(vn3, text = 'y1:')
    ingreso_y1.place(x=100,y=70)
    entra_y1 = tk.Entry(vn3,width=5)
    entra_y1.place(x=130,y=70)
    ingreso_z1 = tk.Label(vn3, text = 'z1:')
    ingreso_z1.place(x=170,y=70)
    entra_z1 = tk.Entry(vn3,width=5)
    entra_z1.place(x=200,y=70)
    ingreso_x2 = tk.Label(vn3, text='x2:')
    ingreso_x2.place(x=30,y=100)
    entra_x2 = tk.Entry(vn3,width=5)
    entra_x2.place(x=60,y=100)
    ingreso_y2 = tk.Label(vn3, text = 'y2:')
    ingreso_y2.place(x=100,y=100)
    entra_y2 = tk.Entry(vn3,width=5)
    entra_y2.place(x=130,y=100)   
    ingreso_z2 = tk.Label(vn3, text = 'z2:')
    ingreso_z2.place(x=170,y=100)
    entra_z2 = tk.Entry(vn3,width=5)
    entra_z2.place(x=200,y=100)
    ingreso_x3 = tk.Label(vn3, text='x3:')
    ingreso_x3.place(x=30,y=130)
    entra_x3 = tk.Entry(vn3,width=5)
    entra_x3.place(x=60,y=130)
    ingreso_y3 = tk.Label(vn3, text = 'y3:')
    ingreso_y3.place(x=100,y=130)
    entra_y3 = tk.Entry(vn3,width=5)
    entra_y3.place(x=130,y=130) 
    ingreso_z3 = tk.Label(vn3, text = 'z3:')
    ingreso_z3.place(x=170,y=130)
    entra_z3 = tk.Entry(vn3,width=5)
    entra_z3.place(x=200,y=130)
    global listaMatriz_3
    listaMatriz_3 = [entra_x1,entra_y1,entra_z1,entra_x2,entra_y2,entra_z2,entra_x3,entra_y3,entra_z3]
    global valida
    valida = 3
    boton_Polinomio = tk.Button(vn3, text="Polinomio Caracteristico", height=2, width=20,command=polinomio_caracteristico)
    boton_Polinomio.place(x=30, y=180)
    boton_Polinomio.config(bg="yellow")
    boton_ValoresPropios = tk.Button(vn3, text="Valores Propios", height=2, width=20,command=valores_propios)
    boton_ValoresPropios.place(x=30, y=240)
    boton_ValoresPropios.config(bg="yellow")
    boton_VectoresPropios = tk.Button(vn3, text="Vectores Propios", height=2, width=20,command=vectores_propios)
    boton_VectoresPropios.place(x=30, y=300)
    boton_VectoresPropios.config(bg="yellow")
    boton_limpiar = tk.Button(vn3, text="Limpiar", command=limpiar_campos3)
    boton_limpiar.place(x=30, y=420)
    boton_limpiar.config(bg="blue")
    boton_volver = tk.Button(vn3, text="Volver", height=2, width=20, command=volver)
    boton_volver.place(x=240, y=410)
    boton_volver.config(bg="red")
    vn3.mainloop()
def volver():
    global ventana
    ventana.destroy()
    root.deiconify()
def is_float(value):
    try:
        float(value)
        return True
    except ValueError:
        return False

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

boton = tk.Button(root, text="2X2", height=2, width=20, command=dimension2)
boton.place(x=40, y=140)
boton.config(bg="yellow")
boton2 = tk.Button(root, text="3X3", height=2, width=20, command=dimension3)
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