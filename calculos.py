"""Lógica de cálculo, interpretación de entradas y formato de matrices.

Este módulo no depende de la interfaz gráfica: todo lo que hay aquí se puede
usar y probar desde la consola o desde los tests.
"""
import math
import re
from dataclasses import dataclass
from fractions import Fraction
from functools import cached_property

import numpy as np


DECIMALES = 4
COND_MAXIMA = 1e8      # por encima, la inversa se considera poco fiable
_EPS = np.finfo(float).eps


# ──────────────────────────────────────────────────────────────────────
# Interpretación de entradas
# ──────────────────────────────────────────────────────────────────────
_NUMERO = re.compile(r"^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$")


def _parsear_decimal(texto):
    texto = texto.strip()
    if not _NUMERO.match(texto):
        raise ValueError("no es un número válido")
    valor = float(texto)
    if not math.isfinite(valor):
        raise ValueError("el número es demasiado grande")
    return valor


def parsear_valor(texto):
    """Convierte el texto de una celda en float.

    Acepta coma o punto decimal ("0,5"), fracciones ("1/2", "-3/4"),
    notación científica ("1e3") y el signo menos Unicode ("−2").
    Rechaza nan, inf y separadores como "1_000". Lanza ValueError con un
    mensaje legible si el texto no es válido.
    """
    t = texto.strip().replace("−", "-").replace(",", ".")
    if not t:
        raise ValueError("está vacía")

    partes = t.split("/")
    if len(partes) > 2:
        raise ValueError("no es un número válido")
    if len(partes) == 2:
        numerador = _parsear_decimal(partes[0])
        denominador = _parsear_decimal(partes[1])
        if denominador == 0:
            raise ValueError("división por cero")
        valor = numerador / denominador
    else:
        valor = _parsear_decimal(t)

    if not math.isfinite(valor):
        raise ValueError("el número es demasiado grande")
    return valor


def parsear_texto_matriz(texto):
    """Interpreta un texto pegado como filas de celdas (textos sin convertir).

    Formatos admitidos:
      - Celdas separadas por tabuladores (copiado desde Excel o Sheets).
      - Filas separadas por saltos de línea o ';' y celdas por espacios
        o por ", " (coma seguida de espacio): "1 2; 3 4", "1, 2\\n3, 4".
      - Listas de Python o NumPy: "[[1, 2], [3, 4]]", "array([[1, 2], ...])".
      - La salida de formatear_matriz: "[ 1  2 ]\\n[ 3  4 ]".

    Una coma sin espacio detrás se considera coma decimal ("0,5").
    """
    t = texto.strip()
    m = re.match(r"^(?:np\.)?array\s*\((.*)\)$", t, re.S)
    if m:
        t = m.group(1)
    t = re.sub(r"\]\s*,", ";", t)        # "[1, 2], [3, 4]" → filas
    t = re.sub(r"[\[\]]", " ", t)

    filas = []
    for linea in re.split(r"[;\n]", t):
        if not linea.strip():
            continue
        if "\t" in linea:
            celdas = [c.strip() for c in linea.rstrip("\r\t ").split("\t")]
        else:
            celdas = [c for c in re.split(r",\s+|\s+", linea.strip()) if c]
        filas.append(celdas)
    return filas


# ──────────────────────────────────────────────────────────────────────
# Formato
# ──────────────────────────────────────────────────────────────────────
_SUPERINDICES = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")
_SUBINDICES = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")


def superindice(n):
    """Convierte un entero a superíndice Unicode (3 → ³)."""
    return str(n).translate(_SUPERINDICES)


def subindice(n):
    """Convierte un entero a subíndice Unicode (3 → ₃)."""
    return str(n).translate(_SUBINDICES)


def _formatear_real(x, decimales=DECIMALES):
    x = float(x)
    if not math.isfinite(x):
        return "∞" if x > 0 else "-∞" if x < 0 else "NaN"
    if x == 0:
        return "0"     # también cubre -0.0

    redondeado = round(x, decimales)
    if redondeado == 0 or abs(x) >= 1e12:
        # Demasiado pequeño o grande para la notación fija: científica
        mantisa, exponente = f"{x:.{decimales}e}".split("e")
        mantisa = mantisa.rstrip("0").rstrip(".")
        return f"{mantisa}e{int(exponente)}"

    return f"{redondeado:.{decimales}f}".rstrip("0").rstrip(".")


def formatear_numero(z, decimales=DECIMALES):
    """Formatea un número real o complejo de forma legible.

    Nunca muestra "-0", no recorta cifras de la parte entera y usa notación
    científica solo para valores muy pequeños (|x| < 0.00005) o muy grandes.
    """
    if not isinstance(z, (complex, np.complexfloating)):
        return _formatear_real(z, decimales)

    real, imag = float(z.real), float(z.imag)
    # Partes despreciables frente a la otra (ruido numérico)
    escala = max(abs(real), abs(imag))
    if abs(imag) <= 1e-12 * escala:
        imag = 0.0
    if abs(real) <= 1e-12 * escala:
        real = 0.0

    if imag == 0:
        return _formatear_real(real, decimales)

    texto_imag = _formatear_real(abs(imag), decimales)
    texto_imag = "i" if texto_imag == "1" else f"{texto_imag}i"
    if real == 0:
        return f"-{texto_imag}" if imag < 0 else texto_imag
    signo = "+" if imag > 0 else "-"
    return f"{_formatear_real(real, decimales)} {signo} {texto_imag}"


def formatear_vector(v, decimales=DECIMALES):
    """Formatea un vector como "[a, b, c]"."""
    return "[" + ", ".join(formatear_numero(c, decimales) for c in v) + "]"


def formatear_matriz(matriz, decimales=DECIMALES):
    """Formatea una matriz con las columnas alineadas a la derecha.

    El resultado se puede volver a pegar en la calculadora.
    """
    celdas = [[formatear_numero(v, decimales) for v in fila] for fila in matriz]
    anchos = [max(len(fila[j]) for fila in celdas) for j in range(len(celdas[0]))]
    return "\n".join(
        "[ " + "  ".join(c.rjust(anchos[j]) for j, c in enumerate(fila)) + " ]"
        for fila in celdas
    )


def formatear_polinomio(coeficientes, variable="λ", decimales=DECIMALES):
    """Formatea los coeficientes (de mayor a menor grado) como polinomio."""
    n = len(coeficientes) - 1
    partes = []

    for i, coef in enumerate(coeficientes):
        coef = float(np.real(coef))
        if coef == 0:
            continue
        grado = n - i
        texto_abs = _formatear_real(abs(coef), decimales)

        if partes:
            signo = " + " if coef > 0 else " − "
        else:
            signo = "" if coef > 0 else "−"

        if grado == 0:
            termino = texto_abs
        else:
            potencia = variable if grado == 1 else variable + superindice(grado)
            termino = potencia if texto_abs == "1" else texto_abs + potencia
        partes.append(signo + termino)

    return "".join(partes) if partes else "0"


# ──────────────────────────────────────────────────────────────────────
# Utilidades numéricas
# ──────────────────────────────────────────────────────────────────────
def limpiar(valores, escala=1.0, tol=1e-10):
    """Pone a cero el ruido numérico: partes (real e imaginaria por separado)
    menores que tol·max(1, escala). Si no queda parte imaginaria, devuelve
    un array real."""
    arr = np.asarray(valores)
    umbral = tol * max(1.0, float(escala))
    if np.iscomplexobj(arr):
        real = np.where(np.abs(arr.real) < umbral, 0.0, arr.real)
        imag = np.where(np.abs(arr.imag) < umbral, 0.0, arr.imag)
        if not np.any(imag):
            return real
        return real + 1j * imag
    return np.where(np.abs(arr) < umbral, 0.0, arr.astype(float))


def es_entera(matriz):
    """True si todos los elementos son enteros (resultados exactos enteros)."""
    return bool(np.all(matriz == np.round(matriz)) and np.all(np.abs(matriz) < 1e9))


def _redondear_si_entero(valores):
    """Redondea al entero más cercano los valores que ya están a ~1e-6 de él."""
    arr = np.asarray(valores, dtype=float)
    redondos = np.round(arr)
    cerca = np.abs(arr - redondos) <= 1e-6 * np.maximum(1.0, np.abs(arr))
    return np.where(cerca, redondos, arr)


def _escala(matriz):
    return max(1.0, float(np.linalg.norm(matriz, 2)))


# ──────────────────────────────────────────────────────────────────────
# Cálculos básicos
# ──────────────────────────────────────────────────────────────────────
def calcular_polinomio(matriz):
    """Coeficientes de P(λ) = det(λI − A), de mayor a menor grado."""
    coefs = np.real_if_close(np.poly(matriz), tol=1e6)
    coefs = np.real(coefs).astype(float)
    escala = _escala(matriz)
    # El coeficiente de λ^(n−k) es del orden de escala^k
    coefs = np.array([
        0.0 if abs(c) < 1e-10 * escala ** k else c for k, c in enumerate(coefs)
    ])
    if es_entera(matriz):
        coefs = _redondear_si_entero(coefs)
    return coefs


def calcular_determinante(matriz):
    """Determinante; exactamente 0 si la matriz es singular y entero si la
    matriz es entera."""
    if calcular_rango(matriz) < len(matriz):
        return 0.0
    det = float(np.linalg.det(matriz))
    if es_entera(matriz):
        det = float(_redondear_si_entero(det))
    return det


def calcular_rango(matriz):
    """Rango (con la tolerancia relativa estándar de NumPy)."""
    return int(np.linalg.matrix_rank(matriz))


def calcular_traza(matriz):
    """Traza de la matriz."""
    return float(np.trace(matriz))


def calcular_inversa(matriz):
    """Devuelve (inversa, número de condición).

    La inversa es None si la matriz es singular. Se decide por el rango
    (independiente de la escala), no comparando el determinante con un
    umbral fijo: 1e-6·I es invertible aunque su determinante sea 1e-12.
    """
    if calcular_rango(matriz) < len(matriz):
        return None, math.inf
    cond = float(np.linalg.cond(matriz))
    inv = np.linalg.inv(matriz)
    inv = limpiar(inv, escala=np.max(np.abs(inv)), tol=1e-12)
    return inv, cond


# ──────────────────────────────────────────────────────────────────────
# Valores y vectores propios
# ──────────────────────────────────────────────────────────────────────
@dataclass
class EspacioPropio:
    """Un valor propio distinto con su multiplicidad algebraica y una base
    de su espacio propio (los vectores ya escalados para leerse mejor)."""
    valor: complex
    multiplicidad: int
    vectores: list

    @property
    def multiplicidad_geometrica(self):
        return len(self.vectores)

    @property
    def defectivo(self):
        return self.multiplicidad_geometrica < self.multiplicidad


def _agrupar_valores(valores, escala):
    """Agrupa los valores propios numéricamente repetidos.

    Un valor propio de multiplicidad m se separa numéricamente en m valores
    a distancia ~ε^(1/m) (p. ej. ~1e-5 para m=3), pero su media es exacta.
    Se forman grupos candidatos y se acepta cada uno si su dispersión es
    compatible con esa separación; si no, se separa.
    """
    n = len(valores)
    pendientes = list(valores)
    candidatos = []
    enlace = 10 * _EPS ** (1 / n) * escala
    while pendientes:
        grupo = [pendientes.pop()]
        cambiado = True
        while cambiado:
            cambiado = False
            for v in pendientes[:]:
                if min(abs(v - g) for g in grupo) <= enlace:
                    grupo.append(v)
                    pendientes.remove(v)
                    cambiado = True
        candidatos.append(grupo)

    grupos = []
    for grupo in candidatos:
        m = len(grupo)
        dispersion = max(abs(a - b) for a in grupo for b in grupo)
        if m == 1 or dispersion <= 10 * _EPS ** (1 / m) * escala:
            grupos.append(grupo)
        else:
            grupos.extend([v] for v in grupo)
    return grupos


def _base_nucleo(M, dimension, tol):
    """Base del núcleo de M con `dimension` vectores.

    Usa la forma escalonada reducida (como se hace a mano: una variable libre
    vale 1 y las demás 0), que da vectores "bonitos". Si el resultado numérico
    no es fiable, recurre a la SVD.
    """
    R = M.astype(complex if np.iscomplexobj(M) else float)
    filas, cols = R.shape
    pivotes = []
    f = 0
    for c in range(cols):
        if f >= filas:
            break
        p = f + int(np.argmax(np.abs(R[f:, c])))
        if abs(R[p, c]) <= tol:
            R[f:, c] = 0
            continue
        R[[f, p]] = R[[p, f]]
        R[f] = R[f] / R[f, c]
        for i in range(filas):
            if i != f:
                R[i] = R[i] - R[i, c] * R[f]
        pivotes.append(c)
        f += 1

    libres = [c for c in range(cols) if c not in pivotes]
    if len(libres) == dimension:
        base = []
        for libre in libres:
            v = np.zeros(cols, dtype=R.dtype)
            v[libre] = 1
            for i, p in enumerate(pivotes):
                v[p] = -R[i, libre]
            base.append(v)
        residuo = max(np.linalg.norm(M @ v) / np.linalg.norm(v) for v in base)
        if residuo <= 1e3 * tol:
            return base

    _, _, Vh = np.linalg.svd(M)
    return [Vh[-k].conj() for k in range(dimension, 0, -1)]


def _como_enteros(w, max_denominador=12, max_valor=100):
    """Si w es proporcional a un vector de enteros pequeños, lo devuelve
    escalado a esos enteros; si no, None."""
    partes = np.concatenate([np.real(w), np.imag(w)])
    fracciones = [Fraction(float(x)).limit_denominator(max_denominador) for x in partes]
    for x, fr in zip(partes, fracciones):
        if abs(float(fr) - x) > 1e-6 * max(1.0, abs(x)):
            return None
    mcm = 1
    for fr in fracciones:
        mcm = mcm * fr.denominator // math.gcd(mcm, fr.denominator)
    resultado = np.round(w * mcm, 9)
    if np.max(np.abs(resultado)) > max_valor:
        return None
    return resultado


def escalar_vector(v, tol=1e-9):
    """Escala un vector propio para que se lea mejor.

    Prefiere componentes enteras pequeñas ([0.447, 0.894] → [1, 2]); si no
    es posible, divide por la componente de mayor módulo (que queda en 1).
    La primera componente no nula queda positiva cuando es real.
    """
    v = np.asarray(v)
    norma = np.max(np.abs(v))
    if norma == 0:
        return v
    v = np.where(np.abs(v) < tol * norma, 0, v)
    no_nulas = [c for c in v if c != 0]

    mejor = None
    for c in no_nulas:
        candidato = _como_enteros(v / c)
        if candidato is not None and (
            mejor is None or np.max(np.abs(candidato)) < np.max(np.abs(mejor))
        ):
            mejor = candidato
    if mejor is None:
        mejor = v / max(no_nulas, key=abs)

    mejor = limpiar(mejor, tol=1e-9)
    primera = next(c for c in mejor if c != 0)
    if np.isreal(primera) and np.real(primera) < 0:
        mejor = -mejor
    return limpiar(mejor, tol=1e-9)


def calcular_espacios_propios(matriz):
    """Valores propios distintos, con multiplicidades y base de vectores.

    Ordenados por parte real y luego imaginaria, de mayor a menor. Las
    matrices defectivas (no diagonalizables) devuelven menos vectores que la
    multiplicidad algebraica, en lugar de vectores linealmente dependientes.
    """
    matriz = np.asarray(matriz, dtype=float)
    n = len(matriz)
    escala = _escala(matriz)

    espacios = []
    for grupo in _agrupar_valores(list(np.linalg.eigvals(matriz)), escala):
        valor = complex(np.mean(grupo))
        if abs(valor.imag) <= 1e-10 * escala:
            valor = complex(valor.real, 0.0)
        if abs(valor.real) <= 1e-10 * escala:
            valor = complex(0.0, valor.imag)
        if es_entera(matriz) and valor.imag == 0:
            valor = complex(float(_redondear_si_entero(valor.real)), 0.0)

        m = len(grupo)
        M = matriz - (valor.real if valor.imag == 0 else valor) * np.eye(n)
        singulares = np.linalg.svd(M, compute_uv=False)
        tol = 1e-8 * escala
        geometrica = min(m, max(1, int(np.sum(singulares <= tol))))

        vectores = [escalar_vector(v) for v in _base_nucleo(M, geometrica, tol)]
        espacios.append(EspacioPropio(
            valor=valor.real if valor.imag == 0 else valor,
            multiplicidad=m,
            vectores=vectores,
        ))

    espacios.sort(key=lambda e: (-np.real(e.valor), -np.imag(e.valor)))
    return espacios


def calcular_valores_propios(matriz):
    """Valores propios con repetición (cada uno tantas veces como su
    multiplicidad algebraica), en el mismo orden que calcular_espacios_propios."""
    return [e.valor for e in calcular_espacios_propios(matriz) for _ in range(e.multiplicidad)]


# ──────────────────────────────────────────────────────────────────────
# Operaciones listas para mostrar
# ──────────────────────────────────────────────────────────────────────
@dataclass
class Resultado:
    """Resultado de una operación, listo para mostrar.

    tipo: "ok", "aviso" (resultado válido con advertencia o caso especial)
    o "error" (no se pudo calcular).
    preformateado: el texto tiene columnas alineadas (una matriz) y no debe
    partirse en varias líneas al mostrarlo.
    """
    clave: str
    titulo: str
    texto: str
    tipo: str = "ok"
    preformateado: bool = False


class Analisis:
    """Calcula bajo demanda (y una sola vez) lo que comparten varias
    operaciones sobre la misma matriz."""

    def __init__(self, matriz):
        self.matriz = np.asarray(matriz, dtype=float)

    @cached_property
    def espacios(self):
        return calcular_espacios_propios(self.matriz)


def _res_polinomio(an):
    return Resultado(
        "polinomio", TITULOS["polinomio"],
        "P(λ) = " + formatear_polinomio(calcular_polinomio(an.matriz)),
    )


def _res_valores(an):
    lineas = []
    for i, e in enumerate(an.espacios, start=1):
        linea = f"λ{subindice(i)} = {formatear_numero(e.valor)}"
        if e.multiplicidad > 1:
            linea += f"   (multiplicidad {e.multiplicidad})"
        lineas.append(linea)
    return Resultado("valores", TITULOS["valores"], "\n".join(lineas))


def _res_vectores(an):
    lineas, avisos = [], []
    k = 1
    for i, e in enumerate(an.espacios, start=1):
        lineas.append(f"λ{subindice(i)} = {formatear_numero(e.valor)}")
        for v in e.vectores:
            lineas.append(f"   v{subindice(k)} = {formatear_vector(v)}")
            k += 1
        if e.defectivo:
            g = e.multiplicidad_geometrica
            vectores = "vector propio independiente" if g == 1 else "vectores propios independientes"
            avisos.append(
                f"λ{subindice(i)} tiene multiplicidad algebraica {e.multiplicidad} "
                f"pero solo {g} {vectores}."
            )
    if avisos:
        lineas.append("")
        lineas.extend("Aviso: " + a for a in avisos)
        lineas.append("La matriz no es diagonalizable.")
        return Resultado("vectores", TITULOS["vectores"], "\n".join(lineas), "aviso")
    return Resultado("vectores", TITULOS["vectores"], "\n".join(lineas))


def _res_determinante(an):
    det = calcular_determinante(an.matriz)
    return Resultado("determinante", TITULOS["determinante"], f"det(A) = {formatear_numero(det)}")


def _res_inversa(an):
    inv, cond = calcular_inversa(an.matriz)
    if inv is None:
        return Resultado(
            "inversa", TITULOS["inversa"],
            "La matriz es singular (rango < n): no tiene inversa.", "aviso",
        )
    texto = formatear_matriz(inv)
    if cond > COND_MAXIMA:
        texto += (
            f"\n\nAviso: la matriz está mal condicionada (cond ≈ {cond:.1e}).\n"
            "El resultado puede ser poco preciso."
        )
        return Resultado("inversa", TITULOS["inversa"], texto, "aviso", preformateado=True)
    return Resultado("inversa", TITULOS["inversa"], texto, preformateado=True)


def _res_transpuesta(an):
    return Resultado(
        "transpuesta", TITULOS["transpuesta"], formatear_matriz(an.matriz.T), preformateado=True
    )


def _res_rango(an):
    return Resultado(
        "rango", TITULOS["rango"],
        f"rango(A) = {calcular_rango(an.matriz)}  (de {len(an.matriz)})",
    )


def _res_traza(an):
    return Resultado("traza", TITULOS["traza"], f"tr(A) = {formatear_numero(calcular_traza(an.matriz))}")


# Orden canónico de las operaciones: (clave, etiqueta del botón, función)
OPERACIONES = [
    ("polinomio",    "Polinomio característico", _res_polinomio),
    ("valores",      "Valores propios",          _res_valores),
    ("vectores",     "Vectores propios",         _res_vectores),
    ("determinante", "Determinante",             _res_determinante),
    ("inversa",      "Inversa",                  _res_inversa),
    ("transpuesta",  "Transpuesta",              _res_transpuesta),
    ("rango",        "Rango",                    _res_rango),
    ("traza",        "Traza",                    _res_traza),
]

TITULOS = {
    "polinomio":    "Polinomio característico   det(λI − A)",
    "valores":      "Valores propios",
    "vectores":     "Vectores propios",
    "determinante": "Determinante",
    "inversa":      "Matriz inversa   A⁻¹",
    "transpuesta":  "Transpuesta   Aᵀ",
    "rango":        "Rango",
    "traza":        "Traza",
}

CLAVES = [clave for clave, _, _ in OPERACIONES]


def calcular(matriz, claves=None):
    """Calcula las operaciones pedidas (todas por defecto) en orden canónico.

    Nunca lanza excepciones: un fallo se devuelve como Resultado de tipo
    "error" para esa operación.
    """
    pedidas = set(CLAVES if claves is None else claves)
    analisis = Analisis(matriz)
    resultados = []
    for clave, _, funcion in OPERACIONES:
        if clave not in pedidas:
            continue
        try:
            resultados.append(funcion(analisis))
        except (np.linalg.LinAlgError, ValueError, FloatingPointError) as e:
            resultados.append(Resultado(clave, TITULOS[clave], f"No se pudo calcular: {e}", "error"))
    return resultados
