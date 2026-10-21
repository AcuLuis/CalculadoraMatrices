import random
import tkinter as tk
import traceback
from tkinter import messagebox, ttk

import numpy as np

from calculos import (
    CLAVES,
    OPERACIONES,
    calcular,
    formatear_matriz,
    formatear_numero,
    parsear_texto_matriz,
    parsear_valor,
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
RETARDO_RECALCULO_MS = 350
TEXTO_COPIAR_TODO = "Copiar resultados  (Ctrl+Shift+C)"

EJEMPLOS = [
    ("Ejemplo 2×2", [[1, 2], [3, 4]]),
    ("Ejemplo 3×3 singular (1 … 9)", [[1, 2, 3], [4, 5, 6], [7, 8, 9]]),
    ("Simétrica 3×3", [[2, -1, 0], [-1, 2, -1], [0, -1, 2]]),
    ("Valor propio repetido (diagonalizable)", [[3, 1, 1], [1, 3, 1], [1, 1, 3]]),
    ("No diagonalizable", [[1, 1], [0, 1]]),
    ("Rotación 90° (valores propios complejos)", [[0, -1], [1, 0]]),
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


# ──────────────────────────────────────────────────────────────────────
# Frame con scroll (para resultados)
# ──────────────────────────────────────────────────────────────────────
class ScrollableFrame(tk.Frame):
    """Frame con scroll vertical y horizontal (las barras se ocultan cuando
    no hacen falta). La rueda del ratón funciona sobre cualquier widget
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

        cabecera = tk.Frame(self, bg=bg)
        cabecera.pack(fill=tk.X, padx=10, pady=(6, 2))

        self.lbl_titulo = tk.Label(cabecera, font=("Segoe UI", 10, "bold"), bg=bg, anchor="w")
        self.lbl_titulo.pack(side=tk.LEFT)

        estilo = dict(
            font=FUENTES["pequena"], fg=COLORES["texto_sec"], bg=bg,
            activebackground=COLORES["acento"], activeforeground=COLORES["texto"],
            relief="flat", bd=0, padx=6, pady=0, cursor="hand2",
        )
        tk.Button(cabecera, text="✕", command=al_cerrar, **estilo).pack(side=tk.RIGHT)
        self.btn_copiar = tk.Button(cabecera, text="Copiar", command=self._copiar, **estilo)
        self.btn_copiar.pack(side=tk.RIGHT, padx=(0, 2))

        self.lbl_texto = tk.Label(
            self, font=FUENTES["resultado"], fg=COLORES["texto"],
            bg=bg, anchor="w", justify="left",
        )
        self.lbl_texto.pack(fill=tk.X, padx=10, pady=(0, 8))

        # Fija el ancho mínimo de la tarjeta (el visible del panel)
        self._puntal = tk.Frame(self, bg=bg, height=1, width=1)
        self._puntal.pack()

    def mostrar(self, resultado):
        self.resultado = resultado
        self.lbl_titulo.configure(text=resultado.titulo)
        self.lbl_texto.configure(text=resultado.texto)
        self.atenuar(False)

    def ajustar(self, ancho_visible):
        """La tarjeta ocupa el ancho visible y parte ahí las líneas largas.
        Las matrices (texto preformateado) no se parten: si no caben, solo esa
        tarjeta es más ancha y se usa el scroll horizontal."""
        self._puntal.configure(width=ancho_visible)
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
# Aplicación principal
# ──────────────────────────────────────────────────────────────────────
class CalculadoraApp:
    """Ventana única: entrada de la matriz, operaciones y resultados."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Calculadora de Matrices")
        self.root.configure(bg=COLORES["fondo"])
        self.root.report_callback_exception = self._error_inesperado
        _configurar_estilos_ttk(self.root)

        self.n = 0
        self.celdas = []                 # filas de tk.Entry
        self.textos = []                 # filas de tk.StringVar
        self.var_dimension = tk.IntVar(value=DIM_INICIAL)
        self.var_vacias_cero = tk.BooleanVar(value=True)

        self.claves_visibles = []        # operaciones mostradas (orden canónico)
        self.tarjetas = {}               # clave → Tarjeta
        self.placeholder = None
        self.matriz_resultados = None    # matriz con la que se calcularon
        self._recalculo = None           # id del after() pendiente
        self._estado_tipo = "info"       # "info", "vacias" o "error"

        self._crear_interfaz()
        self._cambiar_dimension(DIM_INICIAL)
        self._configurar_atajos()
        self._centrar_ventana()

    # ── Construcción de la interfaz ──

    def _crear_interfaz(self):
        main = tk.Frame(self.root, bg=COLORES["fondo"])
        main.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        tk.Label(
            main, text="Calculadora de Matrices",
            font=FUENTES["titulo"], fg=COLORES["primario"], bg=COLORES["fondo"],
        ).pack(anchor="w")
        tk.Label(
            main,
            text="Polinomio característico · valores y vectores propios · determinante · "
                 "inversa · transpuesta · rango · traza",
            font=FUENTES["pequena"], fg=COLORES["texto_sec"], bg=COLORES["fondo"],
        ).pack(anchor="w")

        self._crear_barra(main)

        contenido = tk.Frame(main, bg=COLORES["fondo"])
        contenido.pack(fill=tk.BOTH, expand=True)
        contenido.columnconfigure(1, weight=1)
        contenido.rowconfigure(0, weight=1)
        self._crear_panel_entrada(contenido)
        self._crear_panel_resultados(contenido)

        # — Botones de operaciones —
        panel_botones = tk.Frame(main, bg=COLORES["fondo"])
        panel_botones.pack(fill=tk.X, pady=(12, 0))
        for i, (clave, etiqueta, _) in enumerate(OPERACIONES):
            fila, col = divmod(i, 4)
            _crear_boton(
                panel_botones, etiqueta, lambda c=clave: self._mostrar_operacion(c),
                bg=COLORES["acento"], padx=10, pady=8,
            ).grid(row=fila, column=col, padx=3, pady=3, sticky="ew")
            panel_botones.columnconfigure(col, weight=1, uniform="operaciones")

        # — Botones de acción —
        acciones = tk.Frame(main, bg=COLORES["fondo"])
        acciones.pack(fill=tk.X, pady=(10, 0))
        _crear_boton(
            acciones, "Calcular todo  (Enter)", self._calcular_todo,
            bg=COLORES["exito"], fg=COLORES["fondo"], activo="#00b894",
        ).pack(side=tk.LEFT, padx=(0, 6))
        _crear_boton(
            acciones, "Limpiar  (Ctrl+L)", self._limpiar,
            bg=COLORES["advertencia"], fg=COLORES["fondo"], activo="#ff9800",
        ).pack(side=tk.LEFT)
        self.btn_copiar_todo = _crear_boton(
            acciones, TEXTO_COPIAR_TODO, self._copiar_todo,
            bg=COLORES["acento"],
        )
        self.btn_copiar_todo.pack(side=tk.RIGHT)

    def _crear_barra(self, parent):
        barra = tk.Frame(parent, bg=COLORES["fondo"])
        barra.pack(fill=tk.X, pady=(12, 10))

        tk.Label(
            barra, text="Dimensión:", font=FUENTES["normal"],
            fg=COLORES["texto"], bg=COLORES["fondo"],
        ).pack(side=tk.LEFT, padx=(0, 6))

        for k in range(DIM_MIN, DIM_MAX + 1):
            tk.Radiobutton(
                barra, text=f"{k}×{k}", value=k, variable=self.var_dimension,
                command=lambda: self._cambiar_dimension(self.var_dimension.get()),
                indicatoron=False, font=FUENTES["boton"],
                fg=COLORES["texto"], bg=COLORES["acento"],
                selectcolor=COLORES["primario"],
                activebackground=COLORES["primario"], activeforeground=COLORES["texto"],
                relief="flat", bd=0, padx=10, pady=4, cursor="hand2",
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

        tk.Checkbutton(
            barra, text="Celdas vacías = 0", variable=self.var_vacias_cero,
            command=self._al_cambiar_vacias, font=FUENTES["normal"],
            fg=COLORES["texto"], bg=COLORES["fondo"],
            selectcolor=COLORES["entrada_bg"],
            activebackground=COLORES["fondo"], activeforeground=COLORES["texto"],
            cursor="hand2",
        ).pack(side=tk.RIGHT)

    def _crear_panel_entrada(self, parent):
        panel = tk.LabelFrame(
            parent, text="  Matriz A  ",
            font=FUENTES["subtitulo"], fg=COLORES["texto"],
            bg=COLORES["fondo_claro"], bd=2, relief="groove", labelanchor="n",
        )
        panel.grid(row=0, column=0, sticky="ns", padx=(0, 12), pady=5)

        self.frame_grid = tk.Frame(panel, bg=COLORES["fondo_claro"])
        self.frame_grid.pack(padx=15, pady=(15, 8))

        self.lbl_estado = tk.Label(
            panel, text="", font=FUENTES["pequena"], fg=COLORES["texto_sec"],
            bg=COLORES["fondo_claro"], justify="left", anchor="w",
        )
        self.lbl_estado.pack(fill=tk.X, padx=15)

        tk.Label(
            panel,
            text="Admite 0,5 · 1/2 · -3 · 1e3\n"
                 "Flechas: moverse entre celdas\n"
                 "Ctrl+V: pegar una matriz (Excel, texto o lista)",
            font=("Segoe UI", 8), fg=COLORES["texto_sec"],
            bg=COLORES["fondo_claro"], justify="left",
        ).pack(side=tk.BOTTOM, anchor="w", padx=15, pady=(8, 12))

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
        ancho = min(max(self.root.winfo_reqwidth(), 1040), self.root.winfo_screenwidth() - 40)
        alto = min(max(self.root.winfo_reqheight(), 700), self.root.winfo_screenheight() - 100)
        x = max(0, (self.root.winfo_screenwidth() - ancho) // 2)
        y = max(0, (self.root.winfo_screenheight() - alto) // 3)
        self.root.geometry(f"{ancho}x{alto}+{x}+{y}")

    def _ajustar_ventana(self):
        """Agranda la ventana si la cuadrícula nueva no cabe."""
        self.root.update_idletasks()
        req_ancho, req_alto = self.root.winfo_reqwidth(), self.root.winfo_reqheight()
        self.root.minsize(req_ancho, req_alto)
        ancho, alto = self.root.winfo_width(), self.root.winfo_height()
        if ancho > 1 and (ancho < req_ancho or alto < req_alto):
            self.root.geometry(f"{max(ancho, req_ancho)}x{max(alto, req_alto)}")

    # ── Cuadrícula de entrada ──

    def _cambiar_dimension(self, n, valores=None):
        """Reconstruye la cuadrícula n×n con `valores` (filas de textos) o,
        si no se dan, conservando los valores anteriores que caben."""
        n = max(DIM_MIN, min(DIM_MAX, n))
        self.var_dimension.set(n)
        if n == self.n and valores is None:
            return
        if valores is None:
            valores = [[v.get() for v in fila] for fila in self.textos]

        for widget in self.frame_grid.winfo_children():
            widget.destroy()
        self.n = n
        self.celdas, self.textos = [], []
        ancho = 8 if n <= 4 else 6

        for j in range(n):
            tk.Label(
                self.frame_grid, text=f"Col {j + 1}", font=FUENTES["etiqueta"],
                fg=COLORES["texto_sec"], bg=COLORES["fondo_claro"],
            ).grid(row=0, column=j + 1, padx=4, pady=(0, 4))

        for i in range(n):
            tk.Label(
                self.frame_grid, text=f"Fila {i + 1}", font=FUENTES["etiqueta"],
                fg=COLORES["texto_sec"], bg=COLORES["fondo_claro"],
            ).grid(row=i + 1, column=0, padx=(0, 8), pady=3, sticky="e")

            fila_celdas, fila_textos = [], []
            for j in range(n):
                inicial = valores[i][j] if i < len(valores) and j < len(valores[i]) else ""
                var = tk.StringVar(value=inicial)
                entry = tk.Entry(
                    self.frame_grid, textvariable=var, width=ancho,
                    font=FUENTES["entrada"], fg=COLORES["entrada_fg"],
                    insertbackground=COLORES["texto"],
                    relief="flat", justify="center", highlightthickness=2,
                )
                entry.grid(row=i + 1, column=j + 1, padx=4, pady=3)

                var.trace_add("write", lambda *_, i=i, j=j: self._al_editar_celda(i, j))
                entry.bind("<Up>", lambda e, i=i, j=j: self._ir_a_celda(i - 1, j))
                entry.bind("<Down>", lambda e, i=i, j=j: self._ir_a_celda(i + 1, j))
                entry.bind("<Left>", lambda e, i=i, j=j: self._mover_horizontal(e, i, j, -1))
                entry.bind("<Right>", lambda e, i=i, j=j: self._mover_horizontal(e, i, j, 1))
                entry.bind("<<Paste>>", lambda e, i=i, j=j: self._pegar(i, j))

                fila_celdas.append(entry)
                fila_textos.append(var)
            self.celdas.append(fila_celdas)
            self.textos.append(fila_textos)

        self._marcar_todas_las_celdas()
        self._ir_a_celda(0, 0)
        self.root.update_idletasks()
        self.lbl_estado.configure(wraplength=max(240, self.frame_grid.winfo_reqwidth()))
        self._ajustar_ventana()
        self._programar_recalculo()

    def _cargar_textos(self, filas):
        """Carga filas de textos; cambia la dimensión si hace falta."""
        k = len(filas)
        if k != self.n:
            self._cambiar_dimension(k, valores=filas)
            return
        for i in range(k):
            for j in range(k):
                self.textos[i][j].set(filas[i][j] if j < len(filas[i]) else "")

    def _ir_a_celda(self, i, j):
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
            todo = celda.index("sel.first") == 0 and celda.index("sel.last") == largo
            en_borde = todo
        if en_borde:
            return self._ir_a_celda(i, j + direccion)
        return None

    def _pegar(self, i, j):
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
            self._cargar_textos(filas)
            self._mostrar_estado(f"Se pegó una matriz {alto}×{ancho}.")
        elif cabe:
            for di, fila in enumerate(filas):
                for dj, valor in enumerate(fila):
                    self.textos[i + di][j + dj].set(valor)
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

    # ── Validación ──

    def _error_celda(self, i, j):
        """Mensaje de error de la celda, o None si es válida."""
        texto = self.textos[i][j].get()
        if not texto.strip():
            return None if self.var_vacias_cero.get() else "está vacía"
        try:
            parsear_valor(texto)
        except ValueError as e:
            return str(e)
        return None

    def _marcar_celda(self, i, j, con_error):
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

    def _marcar_todas_las_celdas(self, incluir_vacias=False):
        for i in range(self.n):
            for j in range(self.n):
                vacia = not self.textos[i][j].get().strip()
                error = self._error_celda(i, j) if incluir_vacias or not vacia else None
                self._marcar_celda(i, j, error is not None)

    def _analizar_celdas(self):
        """Devuelve (matriz o None, errores, número de celdas vacías)."""
        matriz = np.zeros((self.n, self.n))
        errores, vacias = [], 0
        for i in range(self.n):
            for j in range(self.n):
                texto = self.textos[i][j].get()
                error = self._error_celda(i, j)
                if error is not None:
                    errores.append((i, j, texto, error))
                elif not texto.strip():
                    vacias += 1
                else:
                    matriz[i, j] = parsear_valor(texto)
        return (None if errores else matriz), errores, vacias

    def _resumen_errores(self, errores):
        k = len(errores)
        lineas = [
            f"Hay {k} {_plural(k, 'celda con error', 'celdas con errores')}:"
        ]
        for i, j, texto, mensaje in errores[:3]:
            detalle = f"'{texto.strip()}' {mensaje}" if texto.strip() else mensaje
            lineas.append(f"• Fila {i + 1}, Col {j + 1}: {detalle}")
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

    def _leer_para_calcular(self):
        """Lee la matriz; si hay errores los marca, los resume y enfoca la
        primera celda con error. Devuelve np.ndarray o None."""
        matriz, errores, vacias = self._analizar_celdas()
        if errores:
            for i, j, _, _ in errores:
                self._marcar_celda(i, j, True)
            self._mostrar_estado(self._resumen_errores(errores), tipo="error")
            self._ir_a_celda(*errores[0][:2])
            return None
        self._mostrar_estado(self._resumen_vacias(vacias), tipo="vacias")
        return matriz

    # ── Eventos de edición ──

    def _al_editar_celda(self, i, j):
        error = self.textos[i][j].get().strip() and self._error_celda(i, j)
        self._marcar_celda(i, j, bool(error))
        self._programar_recalculo()

    def _al_cambiar_vacias(self):
        self._marcar_todas_las_celdas()
        self._programar_recalculo()

    def _programar_recalculo(self):
        if self._recalculo is not None:
            self.root.after_cancel(self._recalculo)
        self._recalculo = self.root.after(RETARDO_RECALCULO_MS, self._tras_editar)

    def _tras_editar(self):
        """Tras una pausa al editar: actualiza el mensaje de estado y recalcula
        los resultados visibles (o los marca como desactualizados)."""
        self._recalculo = None
        matriz, errores, vacias = self._analizar_celdas()

        if self._estado_tipo == "error":
            if errores:
                self._mostrar_estado(self._resumen_errores(errores), tipo="error")
            else:
                self._mostrar_estado(self._resumen_vacias(vacias), tipo="vacias")
        elif self.tarjetas and matriz is not None and (vacias or self._estado_tipo == "vacias"):
            self._mostrar_estado(self._resumen_vacias(vacias), tipo="vacias")

        if not self.tarjetas:
            return
        if matriz is None:
            self._marcar_desactualizado(True)
        elif not np.array_equal(matriz, self.matriz_resultados):
            self._renderizar(matriz, calcular(matriz, self.claves_visibles))
        else:
            self._marcar_desactualizado(False)

    # ── Resultados ──

    def _mostrar_operacion(self, clave):
        """Añade (o actualiza) la tarjeta de una operación sin borrar las demás."""
        matriz = self._leer_para_calcular()
        if matriz is None:
            return
        if clave not in self.claves_visibles:
            self.claves_visibles = [c for c in CLAVES if c in self.claves_visibles or c == clave]
        self._renderizar(matriz, calcular(matriz, self.claves_visibles))
        tarjeta = self.tarjetas[clave]
        self.scroll.ir_a(tarjeta)
        tarjeta.resaltar()

    def _calcular_todo(self):
        matriz = self._leer_para_calcular()
        if matriz is None:
            return
        self.claves_visibles = list(CLAVES)
        self._renderizar(matriz, calcular(matriz, CLAVES))
        self.scroll.ir_al_inicio()

    def _renderizar(self, matriz, resultados):
        claves = [r.clave for r in resultados]
        if claves != list(self.tarjetas):
            self._borrar_tarjetas()
            for r in resultados:
                tarjeta = Tarjeta(self.panel_resultados, lambda c=r.clave: self._cerrar_tarjeta(c))
                tarjeta.pack(anchor="w", padx=8, pady=4)
                self.tarjetas[r.clave] = tarjeta
        for r in resultados:
            self.tarjetas[r.clave].mostrar(r)
        self.matriz_resultados = matriz
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
        for fila in self.textos:
            for var in fila:
                var.set("")
        self.claves_visibles = []
        self.matriz_resultados = None
        self._borrar_tarjetas()
        self._marcar_desactualizado(False)
        self._mostrar_placeholder()
        self._mostrar_estado("")
        self._ir_a_celda(0, 0)

    def _copiar_todo(self):
        if not self.tarjetas:
            self._mostrar_estado("No hay resultados para copiar.")
            return
        partes = ["A =\n" + formatear_matriz(self.matriz_resultados)]
        partes += [f"{t.resultado.titulo}\n{t.resultado.texto}" for t in self.tarjetas.values()]
        self.root.clipboard_clear()
        self.root.clipboard_append("\n\n".join(partes))
        self.btn_copiar_todo.configure(text="✓ Resultados copiados")
        self.root.after(1200, lambda: self.btn_copiar_todo.configure(text=TEXTO_COPIAR_TODO))

    def _cargar_ejemplo(self, valores):
        self._cargar_textos([[formatear_numero(v) for v in fila] for fila in valores])
        self._calcular_todo()

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
