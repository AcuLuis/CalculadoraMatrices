import random
import tkinter as tk
import traceback
from fractions import Fraction
from tkinter import messagebox, ttk

import numpy as np

from calculos import (
    CLAVES,
    CLAVES_CON_B,
    CLAVES_TODO,
    OPERACIONES,
    calcular,
    formatear_matriz,
    formatear_matriz_exacta,
    formatear_numero,
    parsear_fraccion,
    parsear_texto_matriz,
)


# ──────────────────────────────────────────────────────────────────────
# Constantes de estilo y configuración
# ──────────────────────────────────────────────────────────────────────
COLORES = {
    "fondo":          "#1a1a2e",
    "fondo_claro":    "#16213e",
    "acento":         "#0f3460",
    "primario":       "#e94560",
    "texto":          "#ffffff",
    "texto_sec":      "#a8a8b3",
    "entrada_bg":     "#2a2a4a",
    "entrada_fg":     "#ffffff",
    "exito":          "#00d4aa",
    "advertencia":    "#ffa726",
    "tarjeta_bg":     "#1e1e3f",
    "borde":          "#3a3a6a",
    "foco":           "#00d4aa",
    "celda_error_bg": "#4a2338",
}

FUENTES = {
    "titulo":     ("Segoe UI", 18, "bold"),
    "subtitulo":  ("Segoe UI", 12, "bold"),
    "normal":     ("Segoe UI", 10),
    "pequena":    ("Segoe UI", 9),
    "etiqueta":   ("Segoe UI", 9, "bold"),
    "entrada":    ("Consolas", 12),
    "resultado":  ("Consolas", 11),
    "boton":      ("Segoe UI", 10, "bold"),
}

# Color del borde y del título de cada tarjeta según Resultado.tipo
COLOR_TIPO = {
    "ok":     COLORES["exito"],
    "aviso":  COLORES["advertencia"],
    "error":  COLORES["primario"],
}

DIM_MIN, DIM_MAX = 2, 6
DIM_INICIAL = 3
EXPONENTE_MIN, EXPONENTE_MAX = -10, 20
RETARDO_RECALCULO_MS = 350
TEXTO_COPIAR_TODO = "Copiar resultados  (Ctrl+Shift+C)"

EJEMPLOS = [
    ("Ejemplo 2×2", [[1, 2], [3, 4]]),
    ("Ejemplo 3×3 singular (1 … 9)", [[1, 2, 3], [4, 5, 6], [7, 8, 9]]),
    ("Simétrica 3×3", [[2, -1, 0], [-1, 2, -1], [0, -1, 2]]),
    ("Valor propio repetido (diagonalizable)", [[3, 1, 1], [1, 3, 1], [1, 1, 3]]),
    ("No diagonalizable", [[1, 1], [0, 1]]),
    ("Rotación 90° (valores propios complejos)", [[0, -1], [1, 0]]),
    ("Con fracciones", [["1/2", "1/3"], ["1/4", "1/5"]]),
]


def _plural(n, singular, plural):
    return singular if n == 1 else plural


def _configurar_estilos_ttk(root):
    """Barras de scroll oscuras (las de tk.Scrollbar no admiten color en Windows)."""
    estilo = ttk.Style(root)
    estilo.theme_use("clam")
    for orientacion in ("Vertical", "Horizontal"):
        nombre = f"Oscuro.{orientacion}.TScrollbar"
        estilo.configure(
            nombre, troughcolor=COLORES["fondo_claro"], background=COLORES["borde"],
            bordercolor=COLORES["fondo_claro"], lightcolor=COLORES["borde"],
            darkcolor=COLORES["borde"], arrowcolor=COLORES["texto_sec"],
        )
        estilo.map(nombre, background=[("active", COLORES["acento"])])


def _crear_boton(parent, texto, comando, bg, fg=COLORES["texto"], activo=COLORES["primario"], **kwargs):
    opciones = dict(
        font=FUENTES["boton"], fg=fg, bg=bg,
        activebackground=activo, activeforeground=fg,
        relief="flat", bd=0, padx=18, pady=10, cursor="hand2",
    )
    opciones.update(kwargs)
    return tk.Button(parent, text=texto, command=comando, **opciones)


def _crear_selector(parent, texto, valor, variable, comando):
    """Botón de opción con aspecto de pestaña (seleccionado = color primario)."""
    return tk.Radiobutton(
        parent, text=texto, value=valor, variable=variable, command=comando,
        indicatoron=False, font=FUENTES["boton"],
        fg=COLORES["texto"], bg=COLORES["acento"],
        selectcolor=COLORES["primario"],
        activebackground=COLORES["primario"], activeforeground=COLORES["texto"],
        relief="flat", bd=0, padx=10, pady=4, cursor="hand2",
    )


def _crear_casilla(parent, texto, variable, comando):
    return tk.Checkbutton(
        parent, text=texto, variable=variable, command=comando,
        font=FUENTES["normal"], fg=COLORES["texto"], bg=COLORES["fondo"],
        selectcolor=COLORES["entrada_bg"],
        activebackground=COLORES["fondo"], activeforeground=COLORES["texto"],
        cursor="hand2",
    )


# ──────────────────────────────────────────────────────────────────────
# Frame con scroll (para resultados)
# ──────────────────────────────────────────────────────────────────────
class ScrollableFrame(tk.Frame):
    """Frame con scroll vertical y horizontal (la barra horizontal se oculta
    cuando no hace falta). La rueda del ratón funciona sobre cualquier widget
    interior, en Windows, macOS y Linux; con Shift desplaza en horizontal."""

    def __init__(self, parent, bg, **kwargs):
        super().__init__(parent, bg=bg, **kwargs)

        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0, width=440)
        self.scroll_y = ttk.Scrollbar(
            self, orient=tk.VERTICAL, command=self.canvas.yview, style="Oscuro.Vertical.TScrollbar"
        )
        self.scroll_x = ttk.Scrollbar(
            self, orient=tk.HORIZONTAL, command=self.canvas.xview, style="Oscuro.Horizontal.TScrollbar"
        )
        self.interior = tk.Frame(self.canvas, bg=bg)
        self._ventana = self.canvas.create_window((0, 0), window=self.interior, anchor="nw")

        # Solo la barra horizontal se oculta sola: ocultar la vertical cambia
        # el ancho, el texto se reparte en otras líneas y podría oscilar.
        self.canvas.configure(
            yscrollcommand=self.scroll_y.set,
            xscrollcommand=self._ajustar_barra_x,
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scroll_y.grid(row=0, column=1, sticky="ns")
        self.scroll_x.grid(row=1, column=0, sticky="ew")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.interior.bind("<Configure>", self._actualizar_region)
        self.canvas.bind("<Configure>", lambda e: self.ajustar_ancho())

        # Se usa bind_all y se comprueba la posición del puntero: con
        # <Enter>/<Leave> sobre el canvas, el scroll deja de funcionar al
        # pasar sobre los widgets interiores.
        for secuencia in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self.bind_all(secuencia, self._on_rueda, add="+")

    def _ajustar_barra_x(self, primero, ultimo):
        if float(primero) <= 0 and float(ultimo) >= 1:
            self.scroll_x.grid_remove()
        else:
            self.scroll_x.grid()
        self.scroll_x.set(primero, ultimo)

    def _actualizar_region(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def ajustar_ancho(self):
        """El interior ocupa el ancho visible, o más si su contenido lo pide."""
        ancho = max(self.canvas.winfo_width(), self.interior.winfo_reqwidth())
        self.canvas.itemconfigure(self._ventana, width=ancho)

    def _puntero_dentro(self, event):
        try:
            widget = self.winfo_containing(event.x_root, event.y_root)
        except (KeyError, tk.TclError):
            return False
        while widget is not None:
            if widget is self:
                return True
            widget = widget.master
        return False

    def _on_rueda(self, event):
        if not self.winfo_exists() or not self._puntero_dentro(event):
            return
        if event.num == 4:
            pasos = -1
        elif event.num == 5:
            pasos = 1
        elif abs(event.delta) >= 120:
            pasos = -int(event.delta / 120)
        else:
            pasos = -event.delta       # macOS: delta en pasos pequeños
        if event.state & 0x1:          # Shift
            self.canvas.xview_scroll(pasos, "units")
        else:
            self.canvas.yview_scroll(pasos, "units")

    def ir_al_inicio(self):
        self.canvas.yview_moveto(0)
        self.canvas.xview_moveto(0)

    def ir_a(self, widget):
        """Desplaza la vista para que `widget` (hijo de interior) quede arriba."""
        self.update_idletasks()
        alto = self.interior.winfo_height()
        if alto > 0:
            self.canvas.yview_moveto(widget.winfo_y() / alto)


# ──────────────────────────────────────────────────────────────────────
# Tarjeta de resultado
# ──────────────────────────────────────────────────────────────────────
class Tarjeta(tk.Frame):
    """Muestra un Resultado con botones para copiarlo y cerrarlo."""

    def __init__(self, parent, al_cerrar):
        bg = COLORES["tarjeta_bg"]
        super().__init__(parent, bg=bg, highlightthickness=1)
        self.resultado = None

        # La cabecera mide exactamente el ancho visible (lo fija el puntal), así
        # los botones quedan a la vista aunque la tarjeta sea más ancha.
        cabecera = tk.Frame(self, bg=bg)
        cabecera.pack(anchor="w", padx=10, pady=(6, 2))
        cabecera.columnconfigure(1, weight=1)

        self.lbl_titulo = tk.Label(cabecera, font=("Segoe UI", 10, "bold"), bg=bg, anchor="w")
        self.lbl_titulo.grid(row=0, column=0, sticky="w")

        estilo = dict(
            font=FUENTES["pequena"], fg=COLORES["texto_sec"], bg=bg,
            activebackground=COLORES["acento"], activeforeground=COLORES["texto"],
            relief="flat", bd=0, padx=6, pady=0, cursor="hand2",
        )
        self.btn_copiar = tk.Button(cabecera, text="Copiar", command=self._copiar, **estilo)
        self.btn_copiar.grid(row=0, column=2, padx=(8, 2))
        tk.Button(cabecera, text="✕", command=al_cerrar, **estilo).grid(row=0, column=3)

        self._puntal = tk.Frame(cabecera, bg=bg, height=1, width=1)
        self._puntal.grid(row=1, column=0, columnspan=4)

        self.lbl_texto = tk.Label(
            self, font=FUENTES["resultado"], fg=COLORES["texto"],
            bg=bg, anchor="w", justify="left",
        )
        self.lbl_texto.pack(fill=tk.X, padx=10, pady=(0, 8))

    def mostrar(self, resultado):
        self.resultado = resultado
        self.lbl_titulo.configure(text=resultado.titulo)
        self.lbl_texto.configure(text=resultado.texto)
        self.atenuar(False)

    def ajustar(self, ancho_visible):
        """La tarjeta ocupa el ancho visible y parte ahí las líneas largas.
        Las matrices (texto preformateado) no se parten: si no caben, solo esa
        tarjeta es más ancha y se usa el scroll horizontal."""
        self._puntal.configure(width=max(1, ancho_visible - 20))
        if self.resultado.preformateado:
            self.lbl_texto.configure(wraplength=0)
        else:
            self.lbl_texto.configure(wraplength=max(150, ancho_visible - 24))

    def atenuar(self, atenuada):
        """Atenúa la tarjeta cuando no corresponde a los datos actuales."""
        color = COLORES["texto_sec"] if atenuada else COLOR_TIPO[self.resultado.tipo]
        self.configure(highlightbackground=color, highlightcolor=color)
        self.lbl_titulo.configure(fg=color)
        self.lbl_texto.configure(fg=COLORES["texto_sec"] if atenuada else COLORES["texto"])

    def resaltar(self):
        self.configure(highlightthickness=3)
        self.after(700, lambda: self.winfo_exists() and self.configure(highlightthickness=1))

    def _copiar(self):
        self.clipboard_clear()
        self.clipboard_append(self.resultado.texto)
        self.btn_copiar.configure(text="✓ Copiado")
        self.after(1200, lambda: self.btn_copiar.winfo_exists() and self.btn_copiar.configure(text="Copiar"))


# ──────────────────────────────────────────────────────────────────────
# Editor de una matriz
# ──────────────────────────────────────────────────────────────────────
class EditorMatriz(tk.Frame):
    """Cuadrícula de celdas para escribir una matriz, con validación en cada
    celda y navegación con flechas.

    al_editar(): se llama cada vez que cambia una celda.
    al_pegar(editor, i, j): maneja Ctrl+V en la celda (i, j).
    """

    def __init__(self, parent, nombre, al_editar, al_pegar):
        super().__init__(parent, bg=COLORES["fondo_claro"])
        self.nombre = nombre
        self._al_editar = al_editar
        self._al_pegar = al_pegar
        self.n = 0
        self.celdas = []                 # filas de tk.Entry
        self.textos = []                 # filas de tk.StringVar

    def construir(self, n, valores=None):
        """Crea la cuadrícula n×n con `valores` (filas de textos) o, si no se
        dan, conservando los valores actuales que caben."""
        if valores is None:
            valores = self.valores_texto()
        for widget in self.winfo_children():
            widget.destroy()
        self.n = n
        self.celdas, self.textos = [], []
        # Más compacta a partir de 5×5 para que quepa en pantallas bajas
        ancho = 8 if n <= 4 else 6
        fuente = FUENTES["entrada"] if n <= 4 else ("Consolas", 11)
        separacion = 3 if n <= 4 else 2

        for j in range(n):
            tk.Label(
                self, text=f"Col {j + 1}", font=FUENTES["etiqueta"],
                fg=COLORES["texto_sec"], bg=COLORES["fondo_claro"],
            ).grid(row=0, column=j + 1, padx=4, pady=(0, 4))

        for i in range(n):
            tk.Label(
                self, text=f"Fila {i + 1}", font=FUENTES["etiqueta"],
                fg=COLORES["texto_sec"], bg=COLORES["fondo_claro"],
            ).grid(row=i + 1, column=0, padx=(0, 8), pady=separacion, sticky="e")

            fila_celdas, fila_textos = [], []
            for j in range(n):
                inicial = valores[i][j] if i < len(valores) and j < len(valores[i]) else ""
                var = tk.StringVar(value=inicial)
                entry = tk.Entry(
                    self, textvariable=var, width=ancho,
                    font=fuente, fg=COLORES["entrada_fg"],
                    insertbackground=COLORES["texto"],
                    relief="flat", justify="center", highlightthickness=2,
                )
                entry.grid(row=i + 1, column=j + 1, padx=4, pady=separacion)

                var.trace_add("write", lambda *_, i=i, j=j: self._celda_editada(i, j))
                entry.bind("<Up>", lambda e, i=i, j=j: self.ir_a_celda(i - 1, j))
                entry.bind("<Down>", lambda e, i=i, j=j: self.ir_a_celda(i + 1, j))
                entry.bind("<Left>", lambda e, i=i, j=j: self._mover_horizontal(e, i, j, -1))
                entry.bind("<Right>", lambda e, i=i, j=j: self._mover_horizontal(e, i, j, 1))
                entry.bind("<<Paste>>", lambda e, i=i, j=j: self._al_pegar(self, i, j))

                fila_celdas.append(entry)
                fila_textos.append(var)
            self.celdas.append(fila_celdas)
            self.textos.append(fila_textos)

        self.marcar_todas(vacias_cero=True)

    def valores_texto(self):
        return [[var.get() for var in fila] for fila in self.textos]

    def cargar(self, filas, desde=(0, 0)):
        """Escribe las filas de textos a partir de la celda `desde`. Con
        desde=(0, 0), las celdas que no estén en `filas` se vacían."""
        i0, j0 = desde
        completa = desde == (0, 0)
        for i in range(i0, self.n):
            for j in range(j0, self.n):
                di, dj = i - i0, j - j0
                if di < len(filas) and dj < len(filas[di]):
                    self.textos[i][j].set(filas[di][dj])
                elif completa:
                    self.textos[i][j].set("")

    def ir_a_celda(self, i, j):
        if 0 <= i < self.n and 0 <= j < self.n:
            celda = self.celdas[i][j]
            celda.focus_set()
            celda.select_range(0, tk.END)
            celda.icursor(tk.END)
        return "break"

    def _mover_horizontal(self, event, i, j, direccion):
        """Las flechas laterales cambian de celda solo en el borde del texto
        (o con todo el texto seleccionado); si no, mueven el cursor."""
        celda = event.widget
        largo = len(celda.get())
        posicion = celda.index(tk.INSERT)
        en_borde = (direccion < 0 and posicion == 0) or (direccion > 0 and posicion == largo)
        if celda.selection_present():
            en_borde = celda.index("sel.first") == 0 and celda.index("sel.last") == largo
        if en_borde:
            return self.ir_a_celda(i, j + direccion)
        return None

    # ── Validación ──

    def error_celda(self, i, j, vacias_cero):
        """Mensaje de error de la celda, o None si es válida."""
        texto = self.textos[i][j].get()
        if not texto.strip():
            return None if vacias_cero else "está vacía"
        try:
            parsear_fraccion(texto)
        except ValueError as e:
            return str(e)
        return None

    def marcar_celda(self, i, j, con_error):
        if con_error:
            self.celdas[i][j].configure(
                bg=COLORES["celda_error_bg"],
                highlightbackground=COLORES["primario"],
                highlightcolor=COLORES["primario"],
            )
        else:
            self.celdas[i][j].configure(
                bg=COLORES["entrada_bg"],
                highlightbackground=COLORES["borde"],
                highlightcolor=COLORES["foco"],
            )

    def marcar_todas(self, vacias_cero):
        """Marca las celdas con texto inválido (las vacías no se marcan hasta
        que se intenta calcular)."""
        for i in range(self.n):
            for j in range(self.n):
                vacia = not self.textos[i][j].get().strip()
                self.marcar_celda(i, j, not vacia and self.error_celda(i, j, vacias_cero) is not None)

    def _celda_editada(self, i, j):
        vacia = not self.textos[i][j].get().strip()
        self.marcar_celda(i, j, not vacia and self.error_celda(i, j, True) is not None)
        self._al_editar()

    def analizar(self, vacias_cero):
        """Devuelve (matriz de fracciones o None, errores, celdas vacías).
        Cada error es (i, j, texto, mensaje)."""
        matriz = [[Fraction(0)] * self.n for _ in range(self.n)]
        errores, vacias = [], 0
        for i in range(self.n):
            for j in range(self.n):
                texto = self.textos[i][j].get()
                error = self.error_celda(i, j, vacias_cero)
                if error is not None:
                    errores.append((i, j, texto, error))
                elif not texto.strip():
                    vacias += 1
                else:
                    matriz[i][j] = parsear_fraccion(texto)
        return (None if errores else matriz), errores, vacias


# ──────────────────────────────────────────────────────────────────────
# Aplicación principal
# ──────────────────────────────────────────────────────────────────────
class CalculadoraApp:
    """Ventana única: entrada de las matrices, operaciones y resultados."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Calculadora de Matrices")
        self.root.configure(bg=COLORES["fondo"])
        self.root.report_callback_exception = self._error_inesperado
        _configurar_estilos_ttk(self.root)

        self.n = 0
        self.var_dimension = tk.IntVar(value=DIM_INICIAL)
        self.var_vacias_cero = tk.BooleanVar(value=True)
        self.var_exacto = tk.BooleanVar(value=True)
        self.var_editor = tk.StringVar(value="A")
        self.var_exponente = tk.StringVar(value="2")

        self.claves_visibles = []        # operaciones mostradas (orden canónico)
        self.tarjetas = {}               # clave → Tarjeta
        self.placeholder = None
        self.entrada_resultados = None   # (A, B, k) con que se calcularon
        self._firma_resultados = None    # identifica datos + opciones de esos resultados
        self._pendiente = None           # claves de un cálculo que falló por datos inválidos
        self._recalculo = None           # id del after() pendiente
        self._estado_tipo = "info"       # "info", "vacias" o "error"

        self._crear_interfaz()
        self._cambiar_dimension(DIM_INICIAL)
        self._configurar_atajos()
        self._centrar_ventana()

    # ── Construcción de la interfaz ──

    def _crear_interfaz(self):
        main = tk.Frame(self.root, bg=COLORES["fondo"])
        main.pack(fill=tk.BOTH, expand=True, padx=20, pady=12)

        cabecera = tk.Frame(main, bg=COLORES["fondo"])
        cabecera.pack(fill=tk.X)
        tk.Label(
            cabecera, text="Calculadora de Matrices",
            font=FUENTES["titulo"], fg=COLORES["primario"], bg=COLORES["fondo"],
        ).pack(side=tk.LEFT)
        tk.Label(
            cabecera,
            text="Valores y vectores propios · diagonalización · determinante · inversa · "
                 "Gauss-Jordan · operaciones con dos matrices",
            font=FUENTES["pequena"], fg=COLORES["texto_sec"], bg=COLORES["fondo"],
        ).pack(side=tk.LEFT, padx=(14, 0), pady=(8, 0))

        self._crear_barra(main)

        contenido = tk.Frame(main, bg=COLORES["fondo"])
        contenido.pack(fill=tk.BOTH, expand=True)
        contenido.columnconfigure(1, weight=1)
        contenido.rowconfigure(0, weight=1)
        self._crear_panel_entrada(contenido)
        self._crear_panel_resultados(contenido)

        self._crear_botones_operaciones(main)

        # — Botones de acción —
        acciones = tk.Frame(main, bg=COLORES["fondo"])
        acciones.pack(fill=tk.X, pady=(8, 0))
        _crear_boton(
            acciones, "Calcular todo  (Enter)", self._calcular_todo,
            bg=COLORES["exito"], fg=COLORES["fondo"], activo="#00b894", pady=8,
        ).pack(side=tk.LEFT, padx=(0, 6))
        _crear_boton(
            acciones, "Limpiar  (Ctrl+L)", self._limpiar,
            bg=COLORES["advertencia"], fg=COLORES["fondo"], activo="#ff9800", pady=8,
        ).pack(side=tk.LEFT)
        self.btn_copiar_todo = _crear_boton(
            acciones, TEXTO_COPIAR_TODO, self._copiar_todo, bg=COLORES["acento"], pady=8,
        )
        self.btn_copiar_todo.pack(side=tk.RIGHT)

    def _crear_barra(self, parent):
        barra = tk.Frame(parent, bg=COLORES["fondo"])
        barra.pack(fill=tk.X, pady=(10, 8))

        tk.Label(
            barra, text="Dimensión:", font=FUENTES["normal"],
            fg=COLORES["texto"], bg=COLORES["fondo"],
        ).pack(side=tk.LEFT, padx=(0, 6))
        for k in range(DIM_MIN, DIM_MAX + 1):
            _crear_selector(
                barra, f"{k}×{k}", k, self.var_dimension,
                lambda: self._cambiar_dimension(self.var_dimension.get()),
            ).pack(side=tk.LEFT, padx=2)

        boton_ejemplos = tk.Menubutton(
            barra, text="Ejemplos ▾", font=FUENTES["boton"],
            fg=COLORES["texto"], bg=COLORES["acento"],
            activebackground=COLORES["primario"], activeforeground=COLORES["texto"],
            relief="flat", padx=10, pady=4, cursor="hand2",
        )
        menu = tk.Menu(
            boton_ejemplos, tearoff=False, font=FUENTES["normal"],
            bg=COLORES["fondo_claro"], fg=COLORES["texto"],
            activebackground=COLORES["primario"], activeforeground=COLORES["texto"],
        )
        menu.add_command(label="Identidad", command=self._cargar_identidad)
        menu.add_command(label="Aleatoria (enteros de -9 a 9)", command=self._cargar_aleatoria)
        menu.add_separator()
        for nombre, valores in EJEMPLOS:
            menu.add_command(label=nombre, command=lambda v=valores: self._cargar_ejemplo(v))
        boton_ejemplos.configure(menu=menu)
        boton_ejemplos.pack(side=tk.LEFT, padx=(16, 0))

        _crear_casilla(
            barra, "Celdas vacías = 0", self.var_vacias_cero, self._al_cambiar_vacias,
        ).pack(side=tk.RIGHT)
        _crear_casilla(
            barra, "Resultados exactos (fracciones y radicales)", self.var_exacto,
            self._programar_recalculo,
        ).pack(side=tk.RIGHT, padx=(0, 16))

    def _crear_panel_entrada(self, parent):
        panel = tk.LabelFrame(
            parent, text="  Matrices  ",
            font=FUENTES["subtitulo"], fg=COLORES["texto"],
            bg=COLORES["fondo_claro"], bd=2, relief="groove", labelanchor="n",
        )
        panel.grid(row=0, column=0, sticky="ns", padx=(0, 12), pady=5)

        pestanas = tk.Frame(panel, bg=COLORES["fondo_claro"])
        pestanas.pack(pady=(6, 0))
        for nombre in ("A", "B"):
            _crear_selector(
                pestanas, f"Matriz {nombre}", nombre, self.var_editor,
                self._al_cambiar_pestana,
            ).pack(side=tk.LEFT, padx=2)

        contenedor = tk.Frame(panel, bg=COLORES["fondo_claro"])
        contenedor.pack(padx=15, pady=(8, 4))
        self.editor_a = EditorMatriz(contenedor, "A", self._programar_recalculo, self._pegar)
        self.editor_b = EditorMatriz(contenedor, "B", self._programar_recalculo, self._pegar)
        self.editor_activo = self.editor_a
        self.editor_a.pack()

        self.lbl_estado = tk.Label(
            panel, text="", font=FUENTES["pequena"], fg=COLORES["texto_sec"],
            bg=COLORES["fondo_claro"], justify="left", anchor="w",
        )
        self.lbl_estado.pack(fill=tk.X, padx=15)

        self.lbl_ayuda = tk.Label(
            panel, font=("Segoe UI", 8), fg=COLORES["texto_sec"],
            bg=COLORES["fondo_claro"], justify="left",
        )
        self.lbl_ayuda.pack(side=tk.BOTTOM, anchor="w", padx=15, pady=(6, 10))
        self._actualizar_ayuda()

    def _crear_panel_resultados(self, parent):
        panel = tk.LabelFrame(
            parent, text="  Resultados  ",
            font=FUENTES["subtitulo"], fg=COLORES["texto"],
            bg=COLORES["fondo_claro"], bd=2, relief="groove", labelanchor="n",
        )
        panel.grid(row=0, column=1, sticky="nsew", pady=5)

        self.lbl_desactualizado = tk.Label(
            panel,
            text="Los datos cambiaron y hay celdas inválidas o vacías: "
                 "estos resultados no corresponden a la matriz actual.",
            font=FUENTES["etiqueta"], fg=COLORES["fondo"], bg=COLORES["advertencia"],
            justify="left", anchor="w", padx=8, pady=4,
        )
        panel.bind(
            "<Configure>",
            lambda e: self.lbl_desactualizado.configure(wraplength=max(200, e.width - 40)),
        )

        self.scroll = ScrollableFrame(panel, bg=COLORES["fondo_claro"])
        self.scroll.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        self.scroll.canvas.bind("<Configure>", lambda e: self._ajustar_tarjetas(), add="+")
        self.panel_resultados = self.scroll.interior
        self._mostrar_placeholder()

    def _crear_botones_operaciones(self, parent):
        etiquetas = {clave: etiqueta for clave, etiqueta, _ in OPERACIONES}
        estilo = dict(bg=COLORES["acento"], padx=8, pady=6)

        panel = tk.Frame(parent, bg=COLORES["fondo"])
        panel.pack(fill=tk.X, pady=(10, 0))
        claves_a = [c for c in CLAVES if c not in CLAVES_CON_B and c != "potencia"]
        for i, clave in enumerate(claves_a + ["potencia"]):
            fila, col = divmod(i, 4)
            if clave == "potencia":
                celda = tk.Frame(panel, bg=COLORES["fondo"])
                _crear_boton(
                    celda, etiquetas[clave], lambda: self._mostrar_operacion("potencia"), **estilo,
                ).pack(side=tk.LEFT, fill=tk.X, expand=True)
                tk.Label(
                    celda, text="k =", font=FUENTES["normal"],
                    fg=COLORES["texto"], bg=COLORES["fondo"],
                ).pack(side=tk.LEFT, padx=(6, 2))
                self.spin_exponente = tk.Spinbox(
                    celda, from_=EXPONENTE_MIN, to=EXPONENTE_MAX, width=3,
                    textvariable=self.var_exponente, font=FUENTES["entrada"],
                    bg=COLORES["entrada_bg"], fg=COLORES["entrada_fg"],
                    buttonbackground=COLORES["acento"], insertbackground=COLORES["texto"],
                    relief="flat", justify="center",
                )
                self.spin_exponente.pack(side=tk.LEFT)
                self.var_exponente.trace_add("write", lambda *_: self._programar_recalculo())
            else:
                celda = _crear_boton(
                    panel, etiquetas[clave], lambda c=clave: self._mostrar_operacion(c), **estilo,
                )
            celda.grid(row=fila, column=col, padx=3, pady=3, sticky="ew")
            panel.columnconfigure(col, weight=1, uniform="operaciones")

        panel_b = tk.Frame(parent, bg=COLORES["fondo"])
        panel_b.pack(fill=tk.X, pady=(2, 0))
        tk.Label(
            panel_b, text="Con la matriz B:", font=FUENTES["normal"],
            fg=COLORES["texto_sec"], bg=COLORES["fondo"],
        ).pack(side=tk.LEFT, padx=(3, 6))
        for clave in CLAVES_CON_B:
            _crear_boton(
                panel_b, etiquetas[clave], lambda c=clave: self._mostrar_operacion(c), **estilo,
            ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=3, pady=3)

    def _configurar_atajos(self):
        self.root.bind("<Return>", lambda e: self._calcular_todo())
        self.root.bind("<KP_Enter>", lambda e: self._calcular_todo())
        self.root.bind("<Control-l>", lambda e: self._limpiar())
        self.root.bind("<Control-L>", lambda e: self._limpiar())
        self.root.bind("<Control-C>", lambda e: self._copiar_todo())    # Ctrl+Shift+C
        for k in range(DIM_MIN, DIM_MAX + 1):
            self.root.bind(f"<Control-Key-{k}>", lambda e, k=k: self._cambiar_dimension(k))

    def _centrar_ventana(self):
        self.root.update_idletasks()
        ancho = min(max(self.root.winfo_reqwidth(), 1060), self.root.winfo_screenwidth() - 40)
        alto = min(max(self.root.winfo_reqheight(), 720), self.root.winfo_screenheight() - 80)
        x = max(0, (self.root.winfo_screenwidth() - ancho) // 2)
        y = max(0, (self.root.winfo_screenheight() - alto) // 3)
        self.root.geometry(f"{ancho}x{alto}+{x}+{y}")

    def _ajustar_ventana(self):
        """Agranda la ventana si la cuadrícula nueva no cabe (sin salirse de
        la pantalla)."""
        self.root.update_idletasks()
        req_ancho = min(self.root.winfo_reqwidth(), self.root.winfo_screenwidth() - 40)
        req_alto = min(self.root.winfo_reqheight(), self.root.winfo_screenheight() - 80)
        self.root.minsize(req_ancho, req_alto)
        ancho, alto = self.root.winfo_width(), self.root.winfo_height()
        if ancho > 1 and (ancho < req_ancho or alto < req_alto):
            self.root.geometry(f"{max(ancho, req_ancho)}x{max(alto, req_alto)}")

    # ── Matrices ──

    @property
    def editores(self):
        return (self.editor_a, self.editor_b)

    def _cambiar_dimension(self, n, valores=None):
        """Reconstruye las cuadrículas n×n. `valores` es un dict editor → filas
        de textos; los editores que no aparecen conservan lo que cabe."""
        n = max(DIM_MIN, min(DIM_MAX, n))
        self.var_dimension.set(n)
        if n == self.n and not valores:
            return
        self.n = n
        for editor in self.editores:
            editor.construir(n, (valores or {}).get(editor))
        self.editor_activo.ir_a_celda(0, 0)
        self.root.update_idletasks()
        ancho_texto = max(240, self.editor_activo.winfo_reqwidth())
        self.lbl_estado.configure(wraplength=ancho_texto)
        self.lbl_ayuda.configure(wraplength=ancho_texto)
        self._ajustar_ventana()
        self._programar_recalculo()

    def _mostrar_editor(self, editor):
        if editor is self.editor_activo:
            return
        self.editor_activo.pack_forget()
        editor.pack()
        self.editor_activo = editor
        self.var_editor.set(editor.nombre)
        self._actualizar_ayuda()

    def _al_cambiar_pestana(self):
        self._mostrar_editor(self.editor_a if self.var_editor.get() == "A" else self.editor_b)
        self.editor_activo.ir_a_celda(0, 0)

    def _actualizar_ayuda(self):
        if self.editor_activo is self.editor_b:
            primera = "B se usa en A + B, A − B, A · B y B · A."
        else:
            primera = "Admite 0,5 · 1/2 · -3 · 1e3."
        self.lbl_ayuda.configure(
            text=f"{primera} Flechas: moverse. Ctrl+V: pegar una matriz (Excel, texto o lista)."
        )

    def _cargar_textos(self, editor, filas):
        """Carga filas de textos en un editor; cambia la dimensión si hace falta."""
        if len(filas) != self.n:
            self._cambiar_dimension(len(filas), {editor: filas})
        else:
            editor.cargar(filas)

    def _pegar(self, editor, i, j):
        """Ctrl+V: si el portapapeles contiene varias celdas, las reparte por la
        cuadrícula (y cambia la dimensión si es una matriz cuadrada)."""
        try:
            texto = self.root.clipboard_get()
        except tk.TclError:
            return "break"
        filas = parsear_texto_matriz(texto)
        if not filas or (len(filas) == 1 and len(filas[0]) <= 1):
            return None                      # un único valor: pegado normal

        alto, ancho = len(filas), max(len(f) for f in filas)
        cabe = i + alto <= self.n and j + ancho <= self.n
        cuadrada = alto == ancho and DIM_MIN <= alto <= DIM_MAX

        if cuadrada and ((i, j) == (0, 0) or not cabe):
            self._cargar_textos(editor, filas)
            self._mostrar_estado(f"Se pegó una matriz {alto}×{ancho} en {editor.nombre}.")
        elif cabe:
            editor.cargar(filas, desde=(i, j))
            self._mostrar_estado(
                f"Se pegaron {alto}×{ancho} valores desde Fila {i + 1}, Col {j + 1}."
            )
        else:
            self._mostrar_estado(
                f"El texto pegado tiene {alto} {_plural(alto, 'fila', 'filas')} y "
                f"{ancho} {_plural(ancho, 'columna', 'columnas')}: no cabe en la "
                f"matriz {self.n}×{self.n} desde esta celda.",
                tipo="error",
            )
        return "break"

    # ── Lectura y validación ──

    def _leer_exponente(self):
        """El exponente k, o None si no es un entero válido (marca el campo)."""
        try:
            k = int(self.var_exponente.get().strip().replace("−", "-"))
        except ValueError:
            k = None
        if k is not None and not EXPONENTE_MIN <= k <= EXPONENTE_MAX:
            k = None
        self.spin_exponente.configure(
            bg=COLORES["entrada_bg"] if k is not None else COLORES["celda_error_bg"]
        )
        return k

    def _analizar(self, claves):
        """Lee lo que necesitan las operaciones `claves`.

        Devuelve (entrada o None, errores, celdas vacías). entrada es
        (A, B o None, k) con A y B en fracciones. Cada error es
        (editor o None, i, j, texto, mensaje); editor None indica el exponente.
        """
        vacias_cero = self.var_vacias_cero.get()
        necesarios = [self.editor_a]
        if any(c in CLAVES_CON_B for c in claves):
            necesarios.append(self.editor_b)

        matrices, errores, vacias = {}, [], 0
        for editor in necesarios:
            matriz, errores_editor, vacias_editor = editor.analizar(vacias_cero)
            matrices[editor] = matriz
            errores += [(editor,) + e for e in errores_editor]
            vacias += vacias_editor

        k = self._leer_exponente()
        if "potencia" in claves and k is None:
            errores.append((None, None, None, self.var_exponente.get(),
                            f"debe ser un entero entre {EXPONENTE_MIN} y {EXPONENTE_MAX}"))
        if errores:
            return None, errores, vacias
        return (matrices[self.editor_a], matrices.get(self.editor_b), k), errores, vacias

    def _resumen_errores(self, errores):
        k = len(errores)
        lineas = [f"Hay {k} {_plural(k, 'error', 'errores')}:"]
        for editor, i, j, texto, mensaje in errores[:3]:
            if editor is None:
                lugar = "Exponente k"
            elif editor is self.editor_b:
                lugar = f"Matriz B, Fila {i + 1}, Col {j + 1}"
            else:
                lugar = f"Fila {i + 1}, Col {j + 1}"
            detalle = f"'{texto.strip()}' {mensaje}" if texto.strip() else mensaje
            lineas.append(f"• {lugar}: {detalle}")
        if k > 3:
            lineas.append(f"… y {k - 3} más")
        return "\n".join(lineas)

    def _resumen_vacias(self, vacias):
        if not vacias:
            return ""
        return (f"{vacias} {_plural(vacias, 'celda vacía se tomó', 'celdas vacías se tomaron')}"
                " como 0.")

    def _mostrar_estado(self, texto, tipo="info"):
        """Mensaje bajo la cuadrícula. tipo: "info", "vacias" (aviso de celdas
        vacías tomadas como 0, se actualiza al editar) o "error"."""
        self._estado_tipo = tipo
        self.lbl_estado.configure(
            text=texto, fg=COLORES["primario"] if tipo == "error" else COLORES["texto_sec"]
        )

    def _leer_para_calcular(self, claves):
        """Lee los datos; si hay errores los marca, los resume y enfoca el
        primero. Devuelve la entrada (A, B, k) o None.

        Si falla, el cálculo queda pendiente y se completa solo en cuanto los
        datos se corrijan."""
        entrada, errores, vacias = self._analizar(claves)
        self._pendiente = list(claves) if errores else None
        if errores:
            for editor, i, j, _, _ in errores:
                if editor is not None:
                    editor.marcar_celda(i, j, True)
            self._mostrar_estado(self._resumen_errores(errores), tipo="error")
            editor, i, j = errores[0][:3]
            if editor is None:
                self.spin_exponente.focus_set()
            else:
                self._mostrar_editor(editor)
                editor.ir_a_celda(i, j)
            return None
        self._mostrar_estado(self._resumen_vacias(vacias), tipo="vacias")
        return entrada

    def _firma(self, entrada, claves):
        A, B, k = entrada
        return (
            tuple(map(tuple, A)), None if B is None else tuple(map(tuple, B)),
            k, self.var_exacto.get(), tuple(claves),
        )

    # ── Eventos de edición ──

    def _al_cambiar_vacias(self):
        for editor in self.editores:
            editor.marcar_todas(self.var_vacias_cero.get())
        self._programar_recalculo()

    def _programar_recalculo(self):
        if self._recalculo is not None:
            self.root.after_cancel(self._recalculo)
        self._recalculo = self.root.after(RETARDO_RECALCULO_MS, self._tras_editar)

    def _tras_editar(self):
        """Tras una pausa al editar: actualiza el mensaje de estado y recalcula
        los resultados visibles (o los marca como desactualizados)."""
        self._recalculo = None
        entrada, errores, vacias = self._analizar(self._pendiente or self.claves_visibles)

        if self._estado_tipo == "error":
            if errores:
                self._mostrar_estado(self._resumen_errores(errores), tipo="error")
            else:
                self._mostrar_estado(self._resumen_vacias(vacias), tipo="vacias")
        elif self.tarjetas and entrada is not None and (vacias or self._estado_tipo == "vacias"):
            self._mostrar_estado(self._resumen_vacias(vacias), tipo="vacias")

        if self._pendiente:
            if entrada is not None:
                self.claves_visibles, self._pendiente = self._pendiente, None
                self._renderizar(entrada, self.claves_visibles)
            elif self.tarjetas:
                self._marcar_desactualizado(True)
            return
        if not self.tarjetas:
            return
        if entrada is None:
            self._marcar_desactualizado(True)
        elif self._firma(entrada, self.claves_visibles) != self._firma_resultados:
            self._renderizar(entrada, self.claves_visibles)
        else:
            self._marcar_desactualizado(False)

    # ── Resultados ──

    def _mostrar_operacion(self, clave):
        """Añade (o actualiza) la tarjeta de una operación sin borrar las demás."""
        claves = [c for c in CLAVES if c in self.claves_visibles or c == clave]
        entrada = self._leer_para_calcular(claves)
        if entrada is None:
            return
        self.claves_visibles = claves
        self._renderizar(entrada, claves)
        tarjeta = self.tarjetas[clave]
        self.scroll.ir_a(tarjeta)
        tarjeta.resaltar()

    def _calcular_todo(self):
        entrada = self._leer_para_calcular(CLAVES_TODO)
        if entrada is None:
            return
        self.claves_visibles = list(CLAVES_TODO)
        self._renderizar(entrada, CLAVES_TODO)
        self.scroll.ir_al_inicio()

    def _renderizar(self, entrada, claves):
        A, B, k = entrada
        resultados = calcular(A, claves, matriz_b=B, exponente=k if k is not None else 2,
                              exacto=self.var_exacto.get())
        if [r.clave for r in resultados] != list(self.tarjetas):
            self._borrar_tarjetas()
            for r in resultados:
                tarjeta = Tarjeta(self.panel_resultados, lambda c=r.clave: self._cerrar_tarjeta(c))
                tarjeta.pack(anchor="w", padx=8, pady=4)
                self.tarjetas[r.clave] = tarjeta
        for r in resultados:
            self.tarjetas[r.clave].mostrar(r)
        self.entrada_resultados = entrada
        self._firma_resultados = self._firma(entrada, claves)
        self._marcar_desactualizado(False)
        self._ajustar_tarjetas()

    def _ajustar_tarjetas(self):
        ancho_visible = max(200, self.scroll.canvas.winfo_width() - 18)
        for tarjeta in self.tarjetas.values():
            tarjeta.ajustar(ancho_visible)
        self.root.update_idletasks()
        self.scroll.ajustar_ancho()

    def _marcar_desactualizado(self, desactualizado):
        if desactualizado:
            self.lbl_desactualizado.pack(fill=tk.X, padx=6, pady=(6, 0), before=self.scroll)
        else:
            self.lbl_desactualizado.pack_forget()
        for tarjeta in self.tarjetas.values():
            tarjeta.atenuar(desactualizado)

    def _cerrar_tarjeta(self, clave):
        self.claves_visibles.remove(clave)
        self.tarjetas.pop(clave).destroy()
        if self.entrada_resultados is not None:
            self._firma_resultados = self._firma(self.entrada_resultados, self.claves_visibles)
        if not self.tarjetas:
            self._marcar_desactualizado(False)
            self._mostrar_placeholder()

    def _borrar_tarjetas(self):
        for tarjeta in self.tarjetas.values():
            tarjeta.destroy()
        self.tarjetas.clear()
        if self.placeholder is not None:
            self.placeholder.destroy()
            self.placeholder = None

    def _mostrar_placeholder(self):
        self.placeholder = tk.Label(
            self.panel_resultados,
            text="Los resultados aparecerán aquí.\n\n"
                 "Escribe la matriz y pulsa Enter para calcular todo,\n"
                 "o elige una operación con los botones de abajo.\n\n"
                 "Los resultados se actualizan solos al editar la matriz.",
            font=FUENTES["normal"], fg=COLORES["texto_sec"],
            bg=COLORES["fondo_claro"], justify="center",
        )
        self.placeholder.pack(fill=tk.X, padx=20, pady=40)

    # ── Acciones ──

    def _limpiar(self):
        for editor in self.editores:
            editor.cargar([])
        self.claves_visibles = []
        self._pendiente = None
        self.entrada_resultados = None
        self._firma_resultados = None
        self._borrar_tarjetas()
        self._marcar_desactualizado(False)
        self._mostrar_placeholder()
        self._mostrar_estado("")
        self._mostrar_editor(self.editor_a)
        self.editor_a.ir_a_celda(0, 0)

    def _copiar_todo(self):
        if not self.tarjetas:
            self._mostrar_estado("No hay resultados para copiar.")
            return

        def texto_matriz(M):
            return formatear_matriz_exacta(M) or formatear_matriz(np.array(M, dtype=float))

        A, B, k = self.entrada_resultados
        partes = ["A =\n" + texto_matriz(A)]
        if B is not None:
            partes.append("B =\n" + texto_matriz(B))
        if "potencia" in self.tarjetas:
            partes.append(f"k = {k}")
        partes += [f"{t.resultado.titulo}\n{t.resultado.texto}" for t in self.tarjetas.values()]
        self.root.clipboard_clear()
        self.root.clipboard_append("\n\n".join(partes))
        self.btn_copiar_todo.configure(text="✓ Resultados copiados")
        self.root.after(1200, lambda: self.btn_copiar_todo.configure(text=TEXTO_COPIAR_TODO))

    def _cargar_ejemplo(self, valores):
        """Carga el ejemplo en la matriz visible; si es A, calcula todo."""
        filas = [[v if isinstance(v, str) else formatear_numero(v) for v in fila] for fila in valores]
        editor = self.editor_activo
        self._cargar_textos(editor, filas)
        if editor is self.editor_a:
            self._calcular_todo()
        else:
            self._mostrar_estado(f"Ejemplo cargado en la matriz {editor.nombre}.")

    def _cargar_identidad(self):
        self._cargar_ejemplo(np.eye(self.n))

    def _cargar_aleatoria(self):
        self._cargar_ejemplo([[random.randint(-9, 9) for _ in range(self.n)] for _ in range(self.n)])

    def _error_inesperado(self, tipo, valor, tb):
        traceback.print_exception(tipo, valor, tb)
        messagebox.showerror(
            "Error inesperado",
            f"Ocurrió un error inesperado:\n{valor}\n\nLos detalles se muestran en la consola.",
            parent=self.root,
        )

    def ejecutar(self):
        """Inicia el loop principal de la aplicación."""
        self.root.mainloop()


# ──────────────────────────────────────────────────────────────────────
# Punto de entrada
# ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = CalculadoraApp()
    app.ejecutar()
