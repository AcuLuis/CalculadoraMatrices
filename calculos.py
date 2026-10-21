"""Lógica de cálculo, interpretación de entradas y formato de matrices.

Este módulo no depende de la interfaz gráfica: todo lo que hay aquí se puede
usar y probar desde la consola o desde los tests.

Hay dos modos de cálculo:
  - numérico (NumPy, con decimales), siempre disponible;
  - exacto (fracciones, módulo `exacto`), que da resultados como 3/2 o
    (5 + √33)/2. Si un resultado exacto tiene fracciones demasiado grandes
    para leerse, ese resultado se muestra en decimales.
"""
import math
import re
from dataclasses import dataclass
from fractions import Fraction
from functools import cached_property

import numpy as np

import exacto as ex


DECIMALES = 4
COND_MAXIMA = 1e8              # por encima, la inversa se considera poco fiable
MAX_DENOMINADOR_EXACTO = 10_000
MAX_NUMERADOR_EXACTO = 10**12
NOTA_DECIMALES = "Nota: en decimales, porque las fracciones exactas serían demasiado grandes."
_EPS = np.finfo(float).eps


# ──────────────────────────────────────────────────────────────────────
# Interpretación de entradas
# ──────────────────────────────────────────────────────────────────────
_NUMERO = re.compile(r"^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$")


def _parsear_decimal(texto):
    texto = texto.strip()
    if not _NUMERO.match(texto):
        raise ValueError("no es un número válido")
    valor = Fraction(texto)
    try:
        float(valor)
    except OverflowError:
        raise ValueError("el número es demasiado grande") from None
    return valor


def parsear_fraccion(texto):
    """Convierte el texto de una celda en una fracción exacta.

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
        try:
            float(valor)
        except OverflowError:
            raise ValueError("el número es demasiado grande") from None
        return valor
    return _parsear_decimal(t)


def parsear_valor(texto):
    """Como parsear_fraccion, pero devuelve un float."""
    return float(parsear_fraccion(texto))


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
_SUPERINDICES = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")
_SUBINDICES = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")


def superindice(n):
    """Convierte un entero a superíndice Unicode (3 → ³, -2 → ⁻²)."""
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


def formatear_fraccion(f):
    """Formatea una fracción como "p" o "p/q"."""
    return str(f)


def fracciones_legibles(valores):
    """True si todas las fracciones son lo bastante pequeñas para leerse."""
    return all(
        f.denominator <= MAX_DENOMINADOR_EXACTO and abs(f.numerator) < MAX_NUMERADOR_EXACTO
        for f in valores
    )


def formatear_vector(v, decimales=DECIMALES):
    """Formatea un vector como "[a, b, c]"."""
    return "[" + ", ".join(formatear_numero(c, decimales) for c in v) + "]"


def formatear_tabla(celdas):
    """Formatea una matriz de textos con las columnas alineadas a la derecha."""
    anchos = [max(len(fila[j]) for fila in celdas) for j in range(len(celdas[0]))]
    return "\n".join(
        "[ " + "  ".join(c.rjust(anchos[j]) for j, c in enumerate(fila)) + " ]"
        for fila in celdas
    )


def formatear_matriz(matriz, decimales=DECIMALES):
    """Formatea una matriz numérica con las columnas alineadas a la derecha.

    El resultado se puede volver a pegar en la calculadora.
    """
    return formatear_tabla([[formatear_numero(v, decimales) for v in fila] for fila in matriz])


def formatear_matriz_exacta(matriz):
    """Formatea una matriz de fracciones, o devuelve None si no es legible."""
    if not fracciones_legibles(x for fila in matriz for x in fila):
        return None
    return formatear_tabla([[formatear_fraccion(x) for x in fila] for fila in matriz])


def formatear_polinomio(coeficientes, variable="λ", decimales=DECIMALES):
    """Formatea los coeficientes (de mayor a menor grado) como polinomio.

    Admite floats o fracciones: (5/6)λ, λ² − 1/2.
    """
    n = len(coeficientes) - 1
    partes = []

    for i, coef in enumerate(coeficientes):
        if isinstance(coef, Fraction):
            fraccionario = coef.denominator != 1
            texto_abs = formatear_fraccion(abs(coef))
        else:
            coef = float(np.real(coef))
            fraccionario = False
            texto_abs = _formatear_real(abs(coef), decimales)
        if coef == 0:
            continue
        grado = n - i

        if partes:
            signo = " + " if coef > 0 else " − "
        else:
            signo = "" if coef > 0 else "−"

        if grado == 0:
            termino = texto_abs
        else:
            potencia = variable if grado == 1 else variable + superindice(grado)
            if texto_abs == "1":
                termino = potencia
            elif fraccionario:
                termino = f"({texto_abs}){potencia}"
            else:
                termino = texto_abs + potencia
        partes.append(signo + termino)

    return "".join(partes) if partes else "0"


def formatear_radical(u, v, m, compleja, signo):
    """Formatea u ± v·√m (o u ± v·i·√m) con denominador común: (P ± Q√m)/R."""
    comun = u.denominator * v.denominator // math.gcd(u.denominator, v.denominator)
    P, Q = int(u * comun), int(v * comun)
    raiz = f"√{m}" if m != 1 else ""
    if compleja:
        termino = ("" if Q == 1 else str(Q)) + "i" + raiz
    else:
        termino = ("" if Q == 1 and raiz else str(Q)) + raiz

    if P == 0:
        cuerpo = termino if signo > 0 else "-" + termino
        return cuerpo if comun == 1 else f"{cuerpo}/{comun}"
    cuerpo = f"{P} {'+' if signo > 0 else '-'} {termino}"
    return cuerpo if comun == 1 else f"({cuerpo})/{comun}"


def _texto_escalar(exacto, numerico):
    """"3/2 ≈ 1.5" si hay valor exacto legible y difiere del decimal; si no,
    solo el decimal."""
    decimal = formatear_numero(numerico)
    if exacto is None or not fracciones_legibles([exacto]):
        return decimal
    texto = formatear_fraccion(exacto)
    return texto if texto == decimal else f"{texto} ≈ {decimal}"


def _comprobacion(nombre, error, exacta, escala):
    """Línea que informa de la verificación de un resultado."""
    if exacta:
        return f"Comprobación {nombre}: correcta (exacta)"
    if error <= 1e-8 * escala:
        detalle = "" if error == 0 else f" (error máximo {error:.1e})"
        return f"Comprobación {nombre}: correcta{detalle}"
    return f"Comprobación {nombre}: FALLA (error máximo {error:.1e})"


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
# Cálculos básicos (numéricos)
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
    de su espacio propio (los vectores ya escalados para leerse mejor).

    texto: forma exacta del valor ("3/2", "(5 + √33)/2"), si se conoce.
    exacto: los vectores se calcularon de forma exacta.
    """
    valor: complex
    multiplicidad: int
    vectores: list
    texto: str = None
    exacto: bool = False

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


def _espacio_numerico(matriz, grupo, escala, texto=None):
    """Espacio propio de un grupo de aproximaciones de un mismo valor propio."""
    n = len(matriz)
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

    return EspacioPropio(
        valor=valor.real if valor.imag == 0 else valor,
        multiplicidad=m,
        vectores=[escalar_vector(v) for v in _base_nucleo(M, geometrica, tol)],
        texto=texto,
    )


def calcular_espacios_propios(matriz, exacta=None):
    """Valores propios distintos, con multiplicidades y base de vectores.

    Ordenados por parte real y luego imaginaria, de mayor a menor. Las
    matrices defectivas (no diagonalizables) devuelven menos vectores que la
    multiplicidad algebraica, en lugar de vectores linealmente dependientes.

    Con `exacta` (la misma matriz en fracciones), los valores propios
    racionales y sus vectores se calculan de forma exacta, y las raíces de un
    factor cuadrático se expresan con radicales.
    """
    matriz = np.asarray(matriz, dtype=float)
    escala = _escala(matriz)

    if exacta is None:
        grupos = _agrupar_valores(list(np.linalg.eigvals(matriz)), escala)
        espacios = [_espacio_numerico(matriz, g, escala) for g in grupos]
    else:
        espacios = []
        racionales, resto = ex.factorizar(ex.polinomio_caracteristico(exacta))
        for raiz, multiplicidad in racionales:
            base = ex.nucleo(ex.restar_escalar(exacta, raiz))
            espacios.append(EspacioPropio(
                valor=float(raiz),
                multiplicidad=multiplicidad,
                vectores=[np.array(v, dtype=float) for v in base],
                texto=formatear_fraccion(raiz) if fracciones_legibles([raiz]) else None,
                exacto=True,
            ))
        if len(resto) == 3:
            u, v, m, compleja = ex.raices_cuadratica(*resto)
            legible = fracciones_legibles([u, v]) and m < MAX_NUMERADOR_EXACTO
            for signo in (1, -1):
                desplazamiento = signo * float(v) * math.sqrt(m)
                valor = complex(float(u), desplazamiento) if compleja else float(u) + desplazamiento
                texto = formatear_radical(u, v, m, compleja, signo) if legible else None
                espacios.append(_espacio_numerico(matriz, [valor], escala, texto))
        elif len(resto) > 3:
            raices = list(np.roots([float(c) for c in resto]))
            espacios += [_espacio_numerico(matriz, g, escala) for g in _agrupar_valores(raices, escala)]

    espacios.sort(key=lambda e: (-np.real(e.valor), -np.imag(e.valor)))
    return espacios


def calcular_valores_propios(matriz):
    """Valores propios con repetición (cada uno tantas veces como su
    multiplicidad algebraica), en el mismo orden que calcular_espacios_propios."""
    return [e.valor for e in calcular_espacios_propios(matriz) for _ in range(e.multiplicidad)]


def _texto_valor(espacio):
    """"(5 + √33)/2 ≈ 5.3723", "3/2 ≈ 1.5" o solo el decimal."""
    decimal = formatear_numero(espacio.valor)
    if espacio.texto is None or espacio.texto == decimal:
        return decimal
    return f"{espacio.texto} ≈ {decimal}"


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
    """Datos de entrada de las operaciones, y lo que comparten varias de
    ellas, calculado bajo demanda y una sola vez.

    exacta / exacta_b: las matrices en fracciones (modo exacto) o None.
    """

    def __init__(self, matriz, matriz_b=None, exponente=2, exacto=False):
        self.matriz = np.array(matriz, dtype=float)
        self.matriz_b = None if matriz_b is None else np.array(matriz_b, dtype=float)
        self.exponente = int(exponente)
        self.exacta = ex.a_fracciones(matriz) if exacto else None
        self.exacta_b = ex.a_fracciones(matriz_b) if exacto and matriz_b is not None else None
        self.n = len(self.matriz)

    @cached_property
    def escala(self):
        return _escala(self.matriz)

    @cached_property
    def espacios(self):
        return calcular_espacios_propios(self.matriz, self.exacta)

    def texto_matriz(self, exacta, numerica):
        """(texto, es_exacto): la matriz exacta si es legible; si no, la
        numérica (con una nota si se pidió el modo exacto)."""
        if exacta is not None:
            texto = formatear_matriz_exacta(exacta)
            if texto is not None:
                return texto, True
            numerica = np.array(exacta, dtype=float)
        texto = formatear_matriz(limpiar(numerica, np.max(np.abs(numerica)), tol=1e-12))
        if self.exacta is not None:
            texto += "\n\n" + NOTA_DECIMALES
        return texto, False


def _res_polinomio(an):
    if an.exacta is not None:
        coefs = ex.polinomio_caracteristico(an.exacta)
        if fracciones_legibles(coefs):
            return Resultado("polinomio", TITULOS["polinomio"], "P(λ) = " + formatear_polinomio(coefs))
    return Resultado(
        "polinomio", TITULOS["polinomio"],
        "P(λ) = " + formatear_polinomio(calcular_polinomio(an.matriz)),
    )


def _res_valores(an):
    lineas = []
    for i, e in enumerate(an.espacios, start=1):
        linea = f"λ{subindice(i)} = {_texto_valor(e)}"
        if e.multiplicidad > 1:
            linea += f"   (multiplicidad {e.multiplicidad})"
        lineas.append(linea)
    return Resultado("valores", TITULOS["valores"], "\n".join(lineas))


def _texto_defectivo(i, e):
    g = e.multiplicidad_geometrica
    vectores = "vector propio independiente" if g == 1 else "vectores propios independientes"
    return (f"λ{subindice(i)} tiene multiplicidad algebraica {e.multiplicidad} "
            f"pero solo {g} {vectores}.")


def _res_vectores(an):
    lineas, avisos = [], []
    k, error = 1, 0.0
    for i, e in enumerate(an.espacios, start=1):
        lineas.append(f"λ{subindice(i)} = {_texto_valor(e)}")
        for v in e.vectores:
            lineas.append(f"   v{subindice(k)} = {formatear_vector(v)}")
            residuo = np.max(np.abs(an.matriz @ v - e.valor * v)) / max(1.0, np.max(np.abs(v)))
            error = max(error, float(residuo))
            k += 1
        if e.defectivo:
            avisos.append(_texto_defectivo(i, e))

    lineas.append("")
    exacta = all(e.exacto for e in an.espacios)
    lineas.append(_comprobacion("A·v = λ·v", error, exacta, an.escala))
    if avisos:
        lineas.append("")
        lineas.extend("Aviso: " + a for a in avisos)
        lineas.append("La matriz no es diagonalizable.")
        return Resultado("vectores", TITULOS["vectores"], "\n".join(lineas), "aviso")
    return Resultado("vectores", TITULOS["vectores"], "\n".join(lineas))


def _res_diagonalizacion(an):
    espacios = an.espacios
    defectivos = [(i, e) for i, e in enumerate(espacios, start=1) if e.defectivo]
    if defectivos:
        lineas = ["No es diagonalizable:"]
        lineas += ["• " + _texto_defectivo(i, e) for i, e in defectivos]
        lineas.append(f"Hacen falta {an.n} vectores propios independientes y solo hay "
                      f"{sum(e.multiplicidad_geometrica for e in espacios)}.")
        return Resultado("diagonalizacion", TITULOS["diagonalizacion"], "\n".join(lineas), "aviso")

    valores = [e for e in espacios for _ in e.vectores]
    P = np.column_stack([v for e in espacios for v in e.vectores])
    D = np.diag([e.valor for e in valores])
    celdas_d = [
        [(e.texto or formatear_numero(e.valor)) if i == j else "0" for j in range(an.n)]
        for i, e in enumerate(valores)
    ]
    error = float(np.max(np.abs(an.matriz @ P - P @ D)))
    exacta = all(e.exacto for e in espacios)

    lineas = [
        "A = P·D·P⁻¹", "",
        "P (vectores propios en columnas) =", formatear_matriz(limpiar(P)), "",
        "D (valores propios en la diagonal) =", formatear_tabla(celdas_d), "",
        _comprobacion("A·P = P·D", error, exacta, an.escala),
    ]
    if any(np.imag(e.valor) != 0 for e in espacios):
        lineas.append("Diagonalizable en ℂ: hay valores propios complejos.")
    return Resultado("diagonalizacion", TITULOS["diagonalizacion"], "\n".join(lineas),
                     preformateado=True)


def _res_determinante(an):
    if an.exacta is not None:
        det = ex.determinante(an.exacta)
        texto = _texto_escalar(det, float(det))
    else:
        texto = formatear_numero(calcular_determinante(an.matriz))
    return Resultado("determinante", TITULOS["determinante"], f"det(A) = {texto}")


def _res_inversa(an):
    singular = Resultado(
        "inversa", TITULOS["inversa"],
        "La matriz es singular (rango < n): no tiene inversa.", "aviso",
    )
    if an.exacta is not None:
        inv = ex.inversa(an.exacta)
        if inv is None:
            return singular
        texto, es_exacto = an.texto_matriz(inv, None)
        if es_exacto:
            texto += "\n\n" + _comprobacion("A·A⁻¹ = I", 0, True, an.escala)
            return Resultado("inversa", TITULOS["inversa"], texto, preformateado=True)

    inv, cond = calcular_inversa(an.matriz)
    if inv is None:
        return singular
    error = float(np.max(np.abs(an.matriz @ inv - np.eye(an.n))))
    texto = formatear_matriz(inv) + "\n\n" + _comprobacion("A·A⁻¹ = I", error, False, 1.0)
    if an.exacta is not None:
        texto += "\n" + NOTA_DECIMALES
    if cond > COND_MAXIMA:
        texto += (
            f"\n\nAviso: la matriz está mal condicionada (cond ≈ {cond:.1e}).\n"
            "El resultado puede ser poco preciso."
        )
        return Resultado("inversa", TITULOS["inversa"], texto, "aviso", preformateado=True)
    return Resultado("inversa", TITULOS["inversa"], texto, preformateado=True)


def _res_transpuesta(an):
    exacta = None if an.exacta is None else ex.transpuesta(an.exacta)
    texto, _ = an.texto_matriz(exacta, an.matriz.T)
    return Resultado("transpuesta", TITULOS["transpuesta"], texto, preformateado=True)


def _res_rango(an):
    rango = ex.rango(an.exacta) if an.exacta is not None else calcular_rango(an.matriz)
    return Resultado("rango", TITULOS["rango"], f"rango(A) = {rango}  (de {an.n})")


def _res_traza(an):
    if an.exacta is not None:
        traza = ex.traza(an.exacta)
        texto = _texto_escalar(traza, float(traza))
    else:
        texto = formatear_numero(calcular_traza(an.matriz))
    return Resultado("traza", TITULOS["traza"], f"tr(A) = {texto}")


def _texto_coeficiente(x, formato):
    """Coeficiente que multiplica a una fila: "", "−", "4·", "(1/3)·"."""
    texto = formato(x)
    if texto == "1":
        return ""
    if texto == "-1":
        return "−"
    if "/" in texto:
        return f"({texto})·"
    return f"{texto}·"


def _texto_operacion(operacion, formato):
    def F(i):
        return f"F{subindice(i + 1)}"

    if operacion[0] == "intercambiar":
        return f"{F(operacion[1])} ↔ {F(operacion[2])}"
    if operacion[0] == "escalar":
        _, i, factor = operacion
        return f"{F(i)} → {_texto_coeficiente(factor, formato)}{F(i)}"
    _, i, factor, j = operacion
    signo = "+" if factor > 0 else "−"
    return f"{F(i)} → {F(i)} {signo} {_texto_coeficiente(abs(factor), formato)}{F(j)}"


def _texto_escalonada(pasos, R, pivotes, formato, formato_matriz):
    lineas = []
    for c, operaciones, M in pasos:
        if M is None:
            lineas += [f"Columna {c + 1}: sin pivote (variable libre)", ""]
        elif not operaciones:
            lineas += [f"Columna {c + 1}: ya está reducida", ""]
        else:
            lineas.append(f"Columna {c + 1}:")
            lineas += ["   " + _texto_operacion(op, formato) for op in operaciones]
            lineas += [formato_matriz(M), ""]
    columnas = ", ".join(str(p + 1) for p in pivotes) or "ninguna"
    lineas += [
        "Forma escalonada reducida:", formato_matriz(R), "",
        f"Columnas pivote: {columnas}   ·   rango = {len(pivotes)}",
    ]
    return "\n".join(lineas)


def _res_escalonada(an):
    if an.exacta is not None:
        R, pivotes, pasos = ex.escalonar(an.exacta)
        valores = [x for fila in R for x in fila]
        for _, operaciones, M in pasos:
            valores += [op[2] for op in operaciones if op[0] != "intercambiar"]
            valores += [x for fila in (M or []) for x in fila]
        if fracciones_legibles(valores):
            texto = _texto_escalonada(pasos, R, pivotes, formatear_fraccion, formatear_matriz_exacta)
            return Resultado("escalonada", TITULOS["escalonada"], texto, preformateado=True)

    tol = 1e-10 * an.escala
    R, pivotes, pasos = ex.escalonar(
        an.matriz.tolist(), es_cero=lambda x: abs(x) <= tol, pivote_parcial=True
    )
    texto = _texto_escalonada(
        pasos, R, pivotes, formatear_numero,
        lambda M: formatear_matriz(limpiar(np.array(M), an.escala)),
    )
    if an.exacta is not None:
        texto = NOTA_DECIMALES + "\n\n" + texto
    return Resultado("escalonada", TITULOS["escalonada"], texto, preformateado=True)


def _res_propiedades(an):
    n = an.n
    if an.exacta is not None:
        A, T, I = an.exacta, ex.transpuesta(an.exacta), ex.identidad(n)
        multiplicar = ex.multiplicar

        def igual(X, Y):
            return X == Y

        def es_cero(x):
            return x == 0

        def opuesta(X):
            return [[-x for x in fila] for fila in X]
        invertible = ex.rango(A) == n
    else:
        A, T, I = an.matriz, an.matriz.T, np.eye(n)
        multiplicar, opuesta = np.matmul, np.negative
        tol = 1e-9 * an.escala

        def igual(X, Y):
            return np.allclose(X, Y, rtol=0, atol=tol)

        def es_cero(x):
            return abs(x) <= tol
        invertible = calcular_rango(A) == n

    fuera = [(i, j) for i in range(n) for j in range(n) if i != j]
    simetrica = igual(T, A)
    filas = [
        ("Simétrica (Aᵀ = A)", simetrica),
        ("Antisimétrica (Aᵀ = −A)", igual(T, opuesta(A))),
        ("Diagonal", all(es_cero(A[i][j]) for i, j in fuera)),
        ("Triangular superior", all(es_cero(A[i][j]) for i, j in fuera if i > j)),
        ("Triangular inferior", all(es_cero(A[i][j]) for i, j in fuera if i < j)),
        ("Ortogonal (AᵀA = I)", igual(multiplicar(T, A), I)),
        ("Idempotente (A² = A)", igual(multiplicar(A, A), A)),
        ("Invertible", invertible),
    ]
    textos = [(nombre, "sí" if valor else "no") for nombre, valor in filas]

    espacios = an.espacios
    if any(e.defectivo for e in espacios):
        diagonalizable = "no"
    elif any(np.imag(e.valor) != 0 for e in espacios):
        diagonalizable = "sí (en ℂ)"
    else:
        diagonalizable = "sí"
    if simetrica:
        definida = "sí" if all(np.real(e.valor) > 0 for e in espacios) else "no"
    else:
        definida = "no aplica (no es simétrica)"
    textos += [("Diagonalizable", diagonalizable), ("Definida positiva", definida)]

    ancho = max(len(nombre) for nombre, _ in textos)
    texto = "\n".join(f"{nombre.ljust(ancho)}   {valor}" for nombre, valor in textos)
    return Resultado("propiedades", TITULOS["propiedades"], texto, preformateado=True)


def _res_potencia(an):
    k = an.exponente
    titulo = f"Potencia   A{superindice(k)}"
    if k < 0 and calcular_rango(an.matriz) < an.n:
        return Resultado(
            "potencia", titulo,
            f"A no es invertible, así que A{superindice(k)} no existe para exponentes negativos.",
            "aviso",
        )
    exacta = None
    if an.exacta is not None:
        base = an.exacta if k >= 0 else ex.inversa(an.exacta)
        exacta = ex.potencia(base, abs(k))
        numerica = None
    else:
        base = an.matriz if k >= 0 else np.linalg.inv(an.matriz)
        numerica = np.linalg.matrix_power(base, abs(k))
    texto, _ = an.texto_matriz(exacta, numerica)
    return Resultado("potencia", titulo, texto, preformateado=True)


def _conmutan(an):
    if an.exacta is not None:
        return ex.multiplicar(an.exacta, an.exacta_b) == ex.multiplicar(an.exacta_b, an.exacta)
    A, B = an.matriz, an.matriz_b
    return np.allclose(A @ B, B @ A, rtol=0, atol=1e-9 * an.escala * _escala(B))


def _binaria(an, clave, exacta, numerica, nota_conmutan=False):
    """Operación entre A y B: exacta(A, B) con fracciones o numerica(A, B)."""
    if an.matriz_b is None:
        return Resultado(clave, TITULOS[clave], "Falta la matriz B.", "error")
    if an.matriz_b.shape != an.matriz.shape:
        return Resultado(clave, TITULOS[clave], "A y B deben tener la misma dimensión.", "error")
    if an.exacta is not None:
        texto, _ = an.texto_matriz(exacta(an.exacta, an.exacta_b), None)
    else:
        texto, _ = an.texto_matriz(None, numerica(an.matriz, an.matriz_b))
    if nota_conmutan and _conmutan(an):
        texto += "\n\nA y B conmutan: A·B = B·A."
    return Resultado(clave, TITULOS[clave], texto, preformateado=True)


def _res_suma(an):
    return _binaria(an, "suma", ex.sumar, np.add)


def _res_resta(an):
    return _binaria(an, "resta", lambda X, Y: ex.sumar(X, Y, -1), np.subtract)


def _res_producto(an):
    return _binaria(an, "producto", ex.multiplicar, np.matmul, nota_conmutan=True)


def _res_producto_ba(an):
    return _binaria(an, "producto_ba", lambda X, Y: ex.multiplicar(Y, X),
                    lambda X, Y: Y @ X, nota_conmutan=True)


# Orden canónico de las operaciones: (clave, etiqueta del botón, función)
OPERACIONES = [
    ("polinomio",       "Polinomio característico", _res_polinomio),
    ("valores",         "Valores propios",          _res_valores),
    ("vectores",        "Vectores propios",         _res_vectores),
    ("diagonalizacion", "Diagonalización",          _res_diagonalizacion),
    ("determinante",    "Determinante",             _res_determinante),
    ("inversa",         "Inversa",                  _res_inversa),
    ("transpuesta",     "Transpuesta",              _res_transpuesta),
    ("rango",           "Rango",                    _res_rango),
    ("traza",           "Traza",                    _res_traza),
    ("escalonada",      "Gauss-Jordan",             _res_escalonada),
    ("propiedades",     "Propiedades",              _res_propiedades),
    ("potencia",        "Potencia Aᵏ",              _res_potencia),
    ("suma",            "A + B",                    _res_suma),
    ("resta",           "A − B",                    _res_resta),
    ("producto",        "A · B",                    _res_producto),
    ("producto_ba",     "B · A",                    _res_producto_ba),
]

TITULOS = {
    "polinomio":       "Polinomio característico   det(λI − A)",
    "valores":         "Valores propios",
    "vectores":        "Vectores propios",
    "diagonalizacion": "Diagonalización",
    "determinante":    "Determinante",
    "inversa":         "Matriz inversa   A⁻¹",
    "transpuesta":     "Transpuesta   Aᵀ",
    "rango":           "Rango",
    "traza":           "Traza",
    "escalonada":      "Forma escalonada reducida (Gauss-Jordan)",
    "propiedades":     "Propiedades",
    "potencia":        "Potencia   Aᵏ",
    "suma":            "Suma   A + B",
    "resta":           "Resta   A − B",
    "producto":        "Producto   A·B",
    "producto_ba":     "Producto   B·A",
}

CLAVES = [clave for clave, _, _ in OPERACIONES]
CLAVES_CON_B = ["suma", "resta", "producto", "producto_ba"]
# "Calcular todo": todas las propiedades de A (sin potencia ni operaciones con B)
CLAVES_TODO = [c for c in CLAVES if c not in CLAVES_CON_B and c != "potencia"]


def calcular(matriz, claves=None, *, matriz_b=None, exponente=2, exacto=False):
    """Calcula las operaciones pedidas (por defecto, CLAVES_TODO) en orden
    canónico.

    matriz y matriz_b pueden contener floats o fracciones; con exacto=True
    los resultados se calculan con fracciones exactas. Nunca lanza
    excepciones: un fallo se devuelve como Resultado de tipo "error".
    """
    pedidas = set(CLAVES_TODO if claves is None else claves)
    analisis = Analisis(matriz, matriz_b, exponente, exacto)
    resultados = []
    for clave, _, funcion in OPERACIONES:
        if clave not in pedidas:
            continue
        try:
            resultados.append(funcion(analisis))
        except (np.linalg.LinAlgError, ValueError, FloatingPointError,
                OverflowError, ZeroDivisionError) as e:
            resultados.append(Resultado(clave, TITULOS[clave], f"No se pudo calcular: {e}", "error"))
    return resultados
