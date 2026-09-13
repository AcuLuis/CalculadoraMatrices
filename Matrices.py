import tkinter as tk
from tkinter import messagebox
import numpy as np


# ──────────────────────────────────────────────────────────────────────
# Constantes de estilo
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
}

FUENTES = {
    "titulo":     ("Segoe UI", 16, "bold"),
    "subtitulo":  ("Segoe UI", 12, "bold"),
    "normal":     ("Segoe UI", 10),
    "entrada":    ("Consolas", 12),
    "resultado":  ("Consolas", 11),
    "boton":      ("Segoe UI", 10, "bold"),
}


# ──────────────────────────────────────────────────────────────────────
# Funciones de cálculo (puras, sin dependencia de UI)
# ──────────────────────────────────────────────────────────────────────
def formatear_polinomio(coeficientes):
    """Formatea los coeficientes del polinomio característico como string
    legible, utilizando caracteres Unicode para superíndices."""
    superscripts = {
        '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴',
        '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹',
    }

    def to_superscript(num):
        return ''.join(superscripts[d] for d in str(num))

    n = len(coeficientes) - 1
    partes = []

    for i, coef in enumerate(coeficientes):
        coef = round(coef, 4)
        grado = n - i

        if abs(coef) < 1e-10:
            continue

        # Signo
        if partes:
            signo = " + " if coef > 0 else " − "
        else:
            signo = "" if coef >= 0 else "−"

        valor_abs = abs(coef)

        if grado == 0:
            partes.append(f"{signo}{valor_abs:g}")
        elif grado == 1:
            if valor_abs == 1.0:
                partes.append(f"{signo}λ")
            else:
                partes.append(f"{signo}{valor_abs:g}λ")
        else:
            exp = to_superscript(grado)
            if valor_abs == 1.0:
                partes.append(f"{signo}λ{exp}")
            else:
                partes.append(f"{signo}{valor_abs:g}λ{exp}")

    return "".join(partes) if partes else "0"


def formatear_numero_complejo(z, decimales=4):
    """Formatea un número (real o complejo) de forma legible."""
    if isinstance(z, (complex, np.complexfloating)):
        real = round(z.real, decimales)
        imag = round(z.imag, decimales)
        if abs(imag) < 1e-10:
            return f"{real:g}"
        elif abs(real) < 1e-10:
            return f"{imag:g}i"
        else:
            signo = "+" if imag >= 0 else "−"
            return f"{real:g} {signo} {abs(imag):g}i"
    else:
        return f"{round(float(z), decimales):g}"


def formatear_matriz(matriz, decimales=4):
    """Formatea una matriz numpy como texto con filas alineadas."""
    lineas = []
    for fila in matriz:
        componentes = [f"{round(float(v), decimales):g}" for v in fila]
        lineas.append(f"  [{', '.join(componentes)}]")
    return "\n".join(lineas)


def calcular_valores_propios(matriz):
    """Calcula valores propios de la matriz."""
    return np.linalg.eigvals(matriz)


def calcular_vectores_propios(matriz):
    """Calcula valores y vectores propios de la matriz."""
    return np.linalg.eig(matriz)


def calcular_determinante(matriz):
    """Calcula el determinante de la matriz."""
    return np.linalg.det(matriz)


def calcular_inversa(matriz):
    """Calcula la inversa de la matriz, o None si es singular."""
    det = np.linalg.det(matriz)
    if abs(det) < 1e-10:
        return None
    return np.linalg.inv(matriz)


def calcular_rango(matriz):
    """Calcula el rango de la matriz."""
    return np.linalg.matrix_rank(matriz)


def calcular_traza(matriz):
    """Calcula la traza de la matriz."""
    return np.trace(matriz)


# ──────────────────────────────────────────────────────────────────────
# Utilidad: subíndice Unicode
# ──────────────────────────────────────────────────────────────────────
_SUBSCRIPTS = {
    '0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄',
    '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉',
}


def subscript(n):
    """Convierte un entero a su representación en subíndice Unicode."""
    return ''.join(_SUBSCRIPTS.get(d, d) for d in str(n))


# ──────────────────────────────────────────────────────────────────────
# Frame con scroll vertical (para resultados)
# ──────────────────────────────────────────────────────────────────────
class ScrollableFrame(tk.Frame):
    """Frame con barra de scroll vertical integrada."""

    def __init__(self, parent, **kwargs):
        bg = kwargs.pop("bg", COLORES["fondo_claro"])
        super().__init__(parent, bg=bg, **kwargs)

        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0)
        self.scrollbar = tk.Scrollbar(
            self, orient=tk.VERTICAL, command=self.canvas.yview
        )
        self.interior = tk.Frame(self.canvas, bg=bg)

        self.interior.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.interior, anchor="nw"
        )

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Ajustar ancho del interior al canvas
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # Scroll con rueda del ratón (solo cuando el cursor está sobre este widget)
        self.canvas.bind("<Enter>", self._bind_mousewheel)
        self.canvas.bind("<Leave>", self._unbind_mousewheel)

        # Limpiar binding al destruir
        self.bind("<Destroy>", self._on_destroy)

    def _bind_mousewheel(self, event=None):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbind_mousewheel(self, event=None):
        self.canvas.unbind_all("<MouseWheel>")

    def _on_destroy(self, event):
        if event.widget is self:
            self._unbind_mousewheel()

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        if self.canvas.winfo_exists():
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


# ──────────────────────────────────────────────────────────────────────
# Clase: Ventana de cálculo de matriz (genérica para N×N)
# ──────────────────────────────────────────────────────────────────────
class VentanaMatriz:
    """Ventana para ingresar y calcular propiedades de una matriz N×N."""

    def __init__(self, parent, dimension):
        self.parent = parent
        self.n = dimension
        self.entries = []
        self.resultado_widgets = []
        self.placeholder = None

        # Crear ventana secundaria (Toplevel, NO un nuevo Tk())
        self.ventana = tk.Toplevel(parent)
        self.ventana.title(f"Matriz {self.n}×{self.n} — Calculadora")
        self.ventana.configure(bg=COLORES["fondo"])
        self.ventana.protocol("WM_DELETE_WINDOW", self._volver)

        # Tamaño adaptado a la dimensión
        ancho = max(780, 480 + self.n * 60)
        alto = max(600, 480 + self.n * 25)
        self.ventana.geometry(f"{ancho}x{alto}")
        self.ventana.minsize(700, 550)

        self._crear_interfaz()
        self._configurar_atajos()

    # ── Construcción de la interfaz ──

    def _crear_interfaz(self):
        """Construye toda la interfaz de la ventana."""
        main = tk.Frame(self.ventana, bg=COLORES["fondo"])
        main.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        # Título
        titulo = tk.Label(
            main, text=f"Matriz {self.n}×{self.n}",
            font=FUENTES["titulo"], fg=COLORES["primario"],
            bg=COLORES["fondo"]
        )
        titulo.pack(pady=(0, 12))

        # Contenedor horizontal: Entrada | Resultados
        contenido = tk.Frame(main, bg=COLORES["fondo"])
        contenido.pack(fill=tk.BOTH, expand=True)
        contenido.columnconfigure(1, weight=1)
        contenido.rowconfigure(0, weight=1)

        # — Panel izquierdo: Entrada —
        panel_entrada = tk.LabelFrame(
            contenido, text="  Entrada de Matriz  ",
            font=FUENTES["subtitulo"], fg=COLORES["texto"],
            bg=COLORES["fondo_claro"], bd=2, relief="groove",
            labelanchor="n"
        )
        panel_entrada.grid(row=0, column=0, sticky="n", padx=(0, 12), pady=5)
        self._crear_grid_matriz(panel_entrada)

        # — Panel derecho: Resultados (con scroll) —
        panel_resultados_ext = tk.LabelFrame(
            contenido, text="  Resultados  ",
            font=FUENTES["subtitulo"], fg=COLORES["texto"],
            bg=COLORES["fondo_claro"], bd=2, relief="groove",
            labelanchor="n"
        )
        panel_resultados_ext.grid(
            row=0, column=1, sticky="nsew", pady=5
        )

        self.scroll_frame = ScrollableFrame(
            panel_resultados_ext, bg=COLORES["fondo_claro"]
        )
        self.scroll_frame.pack(fill=tk.BOTH, expand=True)
        self.panel_resultados = self.scroll_frame.interior

        # Placeholder
        self._mostrar_placeholder()

        # — Botones de cálculo —
        panel_botones = tk.Frame(main, bg=COLORES["fondo"])
        panel_botones.pack(fill=tk.X, pady=(12, 0))

        botones_calculo = [
            ("📐 Polinomio Característico", self._calc_polinomio),
            ("λ  Valores Propios",          self._calc_valores_propios),
            ("→  Vectores Propios",         self._calc_vectores_propios),
            ("⊞  Determinante",             self._calc_determinante),
            ("⁻¹ Inversa",                  self._calc_inversa),
            ("ᵀ  Transpuesta",              self._calc_transpuesta),
            ("#  Rango",                     self._calc_rango),
            ("Σ  Traza",                     self._calc_traza),
        ]

        for i, (texto, comando) in enumerate(botones_calculo):
            fila, col = divmod(i, 4)
            btn = tk.Button(
                panel_botones, text=texto, command=comando,
                font=FUENTES["boton"], fg=COLORES["texto"],
                bg=COLORES["acento"],
                activebackground=COLORES["primario"],
                activeforeground=COLORES["texto"],
                relief="flat", bd=0, padx=10, pady=8, cursor="hand2"
            )
            btn.grid(row=fila, column=col, padx=3, pady=3, sticky="ew")
            panel_botones.columnconfigure(col, weight=1)

        # — Botones de acción —
        panel_acciones = tk.Frame(main, bg=COLORES["fondo"])
        panel_acciones.pack(fill=tk.X, pady=(10, 0))

        tk.Button(
            panel_acciones, text="⚡ Calcular Todo  (Enter)",
            command=self._calcular_todo,
            font=FUENTES["boton"], fg=COLORES["fondo"],
            bg=COLORES["exito"], activebackground="#00b894",
            relief="flat", bd=0, padx=18, pady=10, cursor="hand2"
        ).pack(side=tk.LEFT, padx=(0, 6))

        tk.Button(
            panel_acciones, text="🗑 Limpiar  (Ctrl+L)",
            command=self._limpiar,
            font=FUENTES["boton"], fg=COLORES["fondo"],
            bg=COLORES["advertencia"], activebackground="#ff9800",
            relief="flat", bd=0, padx=18, pady=10, cursor="hand2"
        ).pack(side=tk.LEFT, padx=(0, 6))

        tk.Button(
            panel_acciones, text="← Volver  (Esc)",
            command=self._volver,
            font=FUENTES["boton"], fg=COLORES["texto"],
            bg=COLORES["primario"], activebackground="#c0392b",
            relief="flat", bd=0, padx=18, pady=10, cursor="hand2"
        ).pack(side=tk.RIGHT)

    def _crear_grid_matriz(self, parent):
        """Crea el grid de entradas para la matriz N×N con etiquetas."""
        frame = tk.Frame(parent, bg=COLORES["fondo_claro"])
        frame.pack(padx=15, pady=15)

        # Etiquetas de columna
        for j in range(self.n):
            tk.Label(
                frame, text=f"Col {j+1}",
                font=("Segoe UI", 9, "bold"), fg=COLORES["texto_sec"],
                bg=COLORES["fondo_claro"]
            ).grid(row=0, column=j + 1, padx=4, pady=(0, 4))

        # Filas con etiqueta + celdas de entrada
        self.entries = []
        for i in range(self.n):
            tk.Label(
                frame, text=f"Fila {i+1}",
                font=("Segoe UI", 9, "bold"), fg=COLORES["texto_sec"],
                bg=COLORES["fondo_claro"]
            ).grid(row=i + 1, column=0, padx=(0, 8), pady=3, sticky="e")

            for j in range(self.n):
                entry = tk.Entry(
                    frame, width=8, font=FUENTES["entrada"],
                    bg=COLORES["entrada_bg"], fg=COLORES["entrada_fg"],
                    insertbackground=COLORES["texto"],
                    relief="flat", justify="center",
                    highlightthickness=2,
                    highlightbackground=COLORES["borde"],
                    highlightcolor=COLORES["primario"]
                )
                entry.grid(row=i + 1, column=j + 1, padx=4, pady=3)
                self.entries.append(entry)

        # Enfocar primer campo
        if self.entries:
            self.entries[0].focus_set()

    def _configurar_atajos(self):
        """Configura atajos de teclado."""
        self.ventana.bind("<Return>", lambda e: self._calcular_todo())
        self.ventana.bind("<Control-l>", lambda e: self._limpiar())
        self.ventana.bind("<Control-L>", lambda e: self._limpiar())
        self.ventana.bind("<Escape>", lambda e: self._volver())

    # ── Validación ──

    def _validar_y_leer_matriz(self):
        """Valida las entradas y retorna np.ndarray o None si hay error."""
        valores = []
        for idx, entry in enumerate(self.entries):
            texto = entry.get().strip()
            fila = idx // self.n + 1
            col = idx % self.n + 1

            if not texto:
                messagebox.showerror(
                    "Campo vacío",
                    f"La celda (Fila {fila}, Col {col}) está vacía.\n"
                    "Complete todos los campos.",
                    parent=self.ventana
                )
                entry.focus_set()
                return None

            try:
                valores.append(float(texto))
            except ValueError:
                messagebox.showerror(
                    "Valor inválido",
                    f"'{texto}' en (Fila {fila}, Col {col}) no es un número válido.",
                    parent=self.ventana
                )
                entry.focus_set()
                return None

        return np.array(valores).reshape(self.n, self.n)

    # ── Gestión de resultados ──

    def _mostrar_placeholder(self):
        """Muestra el mensaje de placeholder en el panel de resultados."""
        self.placeholder = tk.Label(
            self.panel_resultados,
            text="Los resultados aparecerán aquí\n\n"
                 "Ingrese valores y presione\n"
                 "un botón o use Enter\n"
                 "para calcular todo",
            font=FUENTES["normal"], fg=COLORES["texto_sec"],
            bg=COLORES["fondo_claro"], justify="center"
        )
        self.placeholder.pack(expand=True, fill=tk.BOTH, padx=20, pady=40)

    def _limpiar_resultados(self):
        """Elimina todos los widgets de resultado anteriores."""
        for widget in self.resultado_widgets:
            widget.destroy()
        self.resultado_widgets.clear()
        if self.placeholder is not None:
            self.placeholder.destroy()
            self.placeholder = None

    def _agregar_resultado(self, titulo, contenido, color=None):
        """Agrega una tarjeta de resultado al panel."""
        if color is None:
            color = COLORES["exito"]

        tarjeta = tk.Frame(
            self.panel_resultados, bg=COLORES["tarjeta_bg"],
            highlightbackground=color, highlightthickness=1
        )
        tarjeta.pack(fill=tk.X, padx=8, pady=4)
        self.resultado_widgets.append(tarjeta)

        tk.Label(
            tarjeta, text=titulo,
            font=("Segoe UI", 10, "bold"), fg=color,
            bg=COLORES["tarjeta_bg"], anchor="w"
        ).pack(fill=tk.X, padx=10, pady=(6, 2))

        tk.Label(
            tarjeta, text=contenido,
            font=FUENTES["resultado"], fg=COLORES["texto"],
            bg=COLORES["tarjeta_bg"], anchor="w", justify="left"
        ).pack(fill=tk.X, padx=10, pady=(0, 6))

    # ── Cálculos individuales ──

    def _calc_polinomio(self):
        matriz = self._validar_y_leer_matriz()
        if matriz is None:
            return
        self._limpiar_resultados()
        coefs = np.poly(matriz)
        self._agregar_resultado(
            "Polinomio Característico  P(λ)", formatear_polinomio(coefs)
        )

    def _calc_valores_propios(self):
        matriz = self._validar_y_leer_matriz()
        if matriz is None:
            return
        self._limpiar_resultados()
        vals = calcular_valores_propios(matriz)
        lineas = [
            f"λ{subscript(i+1)} = {formatear_numero_complejo(v)}"
            for i, v in enumerate(vals)
        ]
        self._agregar_resultado("Valores Propios", "\n".join(lineas))

    def _calc_vectores_propios(self):
        matriz = self._validar_y_leer_matriz()
        if matriz is None:
            return
        self._limpiar_resultados()
        vals, vecs = calcular_vectores_propios(matriz)
        lineas = []
        for i in range(len(vals)):
            comps = [formatear_numero_complejo(c) for c in vecs[:, i]]
            lineas.append(f"v{subscript(i+1)} = [{', '.join(comps)}]")
        self._agregar_resultado("Vectores Propios", "\n".join(lineas))

    def _calc_determinante(self):
        matriz = self._validar_y_leer_matriz()
        if matriz is None:
            return
        self._limpiar_resultados()
        det = calcular_determinante(matriz)
        self._agregar_resultado("Determinante", f"det(A) = {round(det, 4):g}")

    def _calc_inversa(self):
        matriz = self._validar_y_leer_matriz()
        if matriz is None:
            return
        self._limpiar_resultados()
        inv = calcular_inversa(matriz)
        if inv is None:
            self._agregar_resultado(
                "Inversa",
                "La matriz es singular (det ≈ 0).\nNo tiene inversa.",
                color=COLORES["primario"]
            )
        else:
            self._agregar_resultado(
                "Matriz Inversa  A⁻¹", formatear_matriz(inv)
            )

    def _calc_transpuesta(self):
        matriz = self._validar_y_leer_matriz()
        if matriz is None:
            return
        self._limpiar_resultados()
        self._agregar_resultado(
            "Transpuesta  Aᵀ", formatear_matriz(matriz.T)
        )

    def _calc_rango(self):
        matriz = self._validar_y_leer_matriz()
        if matriz is None:
            return
        self._limpiar_resultados()
        self._agregar_resultado(
            "Rango", f"rango(A) = {calcular_rango(matriz)}"
        )

    def _calc_traza(self):
        matriz = self._validar_y_leer_matriz()
        if matriz is None:
            return
        self._limpiar_resultados()
        traza = calcular_traza(matriz)
        self._agregar_resultado("Traza", f"tr(A) = {round(traza, 4):g}")

    # ── Calcular todo ──

    def _calcular_todo(self):
        """Calcula todas las propiedades de la matriz de una vez."""
        matriz = self._validar_y_leer_matriz()
        if matriz is None:
            return
        self._limpiar_resultados()

        # Polinomio característico
        coefs = np.poly(matriz)
        self._agregar_resultado(
            "Polinomio Característico  P(λ)", formatear_polinomio(coefs)
        )

        # Valores propios
        vals = calcular_valores_propios(matriz)
        lineas_v = [
            f"λ{subscript(i+1)} = {formatear_numero_complejo(v)}"
            for i, v in enumerate(vals)
        ]
        self._agregar_resultado("Valores Propios", "\n".join(lineas_v))

        # Vectores propios
        _, vecs = calcular_vectores_propios(matriz)
        lineas_vec = []
        for i in range(len(vals)):
            comps = [formatear_numero_complejo(c) for c in vecs[:, i]]
            lineas_vec.append(f"v{subscript(i+1)} = [{', '.join(comps)}]")
        self._agregar_resultado("Vectores Propios", "\n".join(lineas_vec))

        # Determinante
        det = calcular_determinante(matriz)
        self._agregar_resultado("Determinante", f"det(A) = {round(det, 4):g}")

        # Rango y Traza
        rango = calcular_rango(matriz)
        traza = calcular_traza(matriz)
        self._agregar_resultado(
            "Rango y Traza",
            f"rango(A) = {rango}\ntr(A) = {round(traza, 4):g}"
        )

        # Transpuesta
        self._agregar_resultado("Transpuesta  Aᵀ", formatear_matriz(matriz.T))

        # Inversa
        inv = calcular_inversa(matriz)
        if inv is None:
            self._agregar_resultado(
                "Inversa",
                "Singular (det ≈ 0) — no tiene inversa",
                color=COLORES["primario"]
            )
        else:
            self._agregar_resultado(
                "Matriz Inversa  A⁻¹", formatear_matriz(inv)
            )

    # ── Acciones de UI ──

    def _limpiar(self):
        """Limpia campos de entrada y resultados."""
        for entry in self.entries:
            entry.delete(0, tk.END)
        self._limpiar_resultados()
        self._mostrar_placeholder()
        if self.entries:
            self.entries[0].focus_set()

    def _volver(self):
        """Cierra esta ventana y restaura la principal."""
        self.ventana.destroy()
        self.parent.deiconify()


# ──────────────────────────────────────────────────────────────────────
# Clase: Aplicación principal
# ──────────────────────────────────────────────────────────────────────
class CalculadoraApp:
    """Ventana principal de la calculadora de matrices."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Calculadora de Matrices")
        self.root.geometry("560x620+300+100")
        self.root.configure(bg=COLORES["fondo"])
        self.root.resizable(width=False, height=False)

        self._crear_interfaz()

    def _crear_interfaz(self):
        """Construye la interfaz de la ventana principal."""
        # ── Título ──
        frame_titulo = tk.Frame(self.root, bg=COLORES["fondo"])
        frame_titulo.pack(fill=tk.X, pady=(35, 5))

        tk.Label(
            frame_titulo, text="🔢  Calculadora de Matrices",
            font=("Segoe UI", 20, "bold"), fg=COLORES["primario"],
            bg=COLORES["fondo"]
        ).pack()

        tk.Label(
            frame_titulo,
            text="Polinomio Característico · Valores Propios · Vectores Propios",
            font=("Segoe UI", 10), fg=COLORES["texto_sec"],
            bg=COLORES["fondo"]
        ).pack(pady=(4, 0))

        # ── Separador ──
        tk.Frame(
            self.root, bg=COLORES["primario"], height=2
        ).pack(fill=tk.X, padx=60, pady=20)

        # ── Instrucción ──
        tk.Label(
            self.root,
            text="Seleccione la dimensión de la matriz",
            font=FUENTES["subtitulo"], fg=COLORES["texto"],
            bg=COLORES["fondo"]
        ).pack(pady=(0, 20))

        # ── Botones de dimensión ──
        frame_botones = tk.Frame(self.root, bg=COLORES["fondo"])
        frame_botones.pack(expand=True)

        self._crear_boton_dimension(frame_botones, 2, fila=0)
        self._crear_boton_dimension(frame_botones, 3, fila=1)

    def _crear_boton_dimension(self, parent, n, fila):
        """Crea una tarjeta‐botón para seleccionar dimensión N×N."""
        card = tk.Frame(
            parent, bg=COLORES["fondo_claro"],
            highlightbackground=COLORES["borde"],
            highlightthickness=2
        )
        card.grid(row=fila, column=0, pady=8, ipadx=40, ipady=12)

        tk.Label(
            card, text=f"Matriz {n}×{n}",
            font=("Segoe UI", 16, "bold"), fg=COLORES["texto"],
            bg=COLORES["fondo_claro"]
        ).pack(pady=(10, 2))

        tk.Label(
            card,
            text=f"Calcular propiedades de una matriz {n}×{n}",
            font=("Segoe UI", 9), fg=COLORES["texto_sec"],
            bg=COLORES["fondo_claro"]
        ).pack(pady=(0, 5))

        tk.Button(
            card, text="Abrir →",
            font=FUENTES["boton"], fg=COLORES["texto"],
            bg=COLORES["primario"],
            activebackground="#c0392b", activeforeground=COLORES["texto"],
            relief="flat", bd=0, padx=30, pady=8, cursor="hand2",
            command=lambda: self._abrir_dimension(n)
        ).pack(pady=(4, 12))

    def _abrir_dimension(self, n):
        """Oculta la ventana principal y abre la de cálculo."""
        self.root.withdraw()
        VentanaMatriz(self.root, n)

    def ejecutar(self):
        """Inicia el loop principal de la aplicación."""
        self.root.mainloop()


# ──────────────────────────────────────────────────────────────────────
# Punto de entrada
# ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = CalculadoraApp()
    app.ejecutar()