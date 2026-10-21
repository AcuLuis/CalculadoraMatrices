"""Álgebra exacta con fracciones para matrices pequeñas.

Las matrices son listas de filas de fractions.Fraction. Todo es exacto: no
hay redondeo, así que los resultados coinciden con los que se obtienen a mano.
"""
import math
from fractions import Fraction

import numpy as np


def _mcm(a, b):
    return a * b // math.gcd(a, b)


# ──────────────────────────────────────────────────────────────────────
# Operaciones básicas
# ──────────────────────────────────────────────────────────────────────
def a_fracciones(matriz):
    """Convierte cualquier matriz de números (int, float, Fraction) a fracciones."""
    return [[x if isinstance(x, Fraction) else Fraction(x) for x in fila] for fila in matriz]


def identidad(n):
    return [[Fraction(int(i == j)) for j in range(n)] for i in range(n)]


def transpuesta(A):
    return [list(columna) for columna in zip(*A)]


def sumar(A, B, factor=1):
    """A + factor·B."""
    return [[a + factor * b for a, b in zip(fa, fb)] for fa, fb in zip(A, B)]


def multiplicar(A, B):
    columnas = transpuesta(B)
    return [[sum((a * b for a, b in zip(fila, col)), Fraction(0)) for col in columnas] for fila in A]


def restar_escalar(A, valor):
    """A − valor·I."""
    return sumar(A, identidad(len(A)), -valor)


def traza(A):
    return sum((A[i][i] for i in range(len(A))), Fraction(0))


def potencia(A, k):
    """A^k para k ≥ 0 (exponenciación binaria)."""
    resultado, base = identidad(len(A)), A
    while k:
        if k & 1:
            resultado = multiplicar(resultado, base)
        base = multiplicar(base, base)
        k >>= 1
    return resultado


# ──────────────────────────────────────────────────────────────────────
# Eliminación de Gauss-Jordan
# ──────────────────────────────────────────────────────────────────────
def escalonar(A, es_cero=lambda x: x == 0, pivote_parcial=False):
    """Forma escalonada reducida por Gauss-Jordan, registrando los pasos.

    Funciona con fracciones (exacto, pivote = primera fila no nula, como a
    mano) o con floats (pasar es_cero con tolerancia y pivote_parcial=True).

    Devuelve (R, pivotes, pasos). Cada paso es (columna, operaciones, matriz
    tras la columna o None si la columna no tiene pivote). Operaciones:
      ("intercambiar", i, j)      Fᵢ ↔ Fⱼ
      ("escalar", i, factor)      Fᵢ → factor·Fᵢ
      ("sumar", i, factor, j)     Fᵢ → Fᵢ + factor·Fⱼ
    """
    R = [list(fila) for fila in A]
    filas, columnas = len(R), len(R[0])
    pivotes, pasos = [], []
    f = 0
    for c in range(columnas):
        if f >= filas:
            break
        candidatas = [i for i in range(f, filas) if not es_cero(R[i][c])]
        if not candidatas:
            for i in range(f, filas):
                R[i][c] = R[i][c] - R[i][c]       # cero del mismo tipo
            pasos.append((c, [], None))
            continue

        p = max(candidatas, key=lambda i: abs(R[i][c])) if pivote_parcial else candidatas[0]
        operaciones = []
        if p != f:
            R[f], R[p] = R[p], R[f]
            operaciones.append(("intercambiar", f, p))
        pivote = R[f][c]
        if pivote != 1:
            factor = 1 / pivote
            R[f] = [x * factor for x in R[f]]
            operaciones.append(("escalar", f, factor))
        R[f][c] = R[f][c] / R[f][c]                # exactamente 1
        for i in range(filas):
            if i != f and not es_cero(R[i][c]):
                factor = -R[i][c]
                R[i] = [a + factor * b for a, b in zip(R[i], R[f])]
                R[i][c] = R[i][c] - R[i][c]        # exactamente 0
                operaciones.append(("sumar", i, factor, f))
        pivotes.append(c)
        pasos.append((c, operaciones, [list(fila) for fila in R]))
        f += 1
    return R, pivotes, pasos


def rango(A):
    return len(escalonar(A)[1])


def determinante(A):
    n = len(A)
    M = [list(fila) for fila in A]
    det = Fraction(1)
    for c in range(n):
        p = next((i for i in range(c, n) if M[i][c] != 0), None)
        if p is None:
            return Fraction(0)
        if p != c:
            M[c], M[p] = M[p], M[c]
            det = -det
        det *= M[c][c]
        for i in range(c + 1, n):
            if M[i][c] != 0:
                factor = M[i][c] / M[c][c]
                M[i] = [a - factor * b for a, b in zip(M[i], M[c])]
    return det


def inversa(A):
    """Inversa exacta, o None si A es singular."""
    n = len(A)
    ampliada = [fila + fila_i for fila, fila_i in zip(A, identidad(n))]
    R, pivotes, _ = escalonar(ampliada)
    if sum(1 for p in pivotes if p < n) < n:
        return None
    return [fila[n:] for fila in R]


def a_enteros(v):
    """Escala un vector de fracciones al vector de enteros proporcional más
    pequeño, con la primera componente no nula positiva."""
    mcm = 1
    for x in v:
        mcm = _mcm(mcm, x.denominator)
    enteros = [int(x * mcm) for x in v]
    divisor = 0
    for e in enteros:
        divisor = math.gcd(divisor, e)
    if divisor > 1:
        enteros = [e // divisor for e in enteros]
    primero = next((e for e in enteros if e != 0), 0)
    if primero < 0:
        enteros = [-e for e in enteros]
    return enteros


def nucleo(A):
    """Base del núcleo de A: una variable libre vale 1 y las demás 0 (como a
    mano); cada vector se escala a enteros."""
    R, pivotes, _ = escalonar(A)
    columnas = len(A[0])
    base = []
    for libre in (c for c in range(columnas) if c not in pivotes):
        v = [Fraction(0)] * columnas
        v[libre] = Fraction(1)
        for fila, p in enumerate(pivotes):
            v[p] = -R[fila][libre]
        base.append(a_enteros(v))
    return base


# ──────────────────────────────────────────────────────────────────────
# Polinomios
# ──────────────────────────────────────────────────────────────────────
def polinomio_caracteristico(A):
    """Coeficientes de det(λI − A), de mayor a menor grado (Faddeev-LeVerrier)."""
    n = len(A)
    I = identidad(n)
    M = [[Fraction(0)] * n for _ in range(n)]
    coeficiente = Fraction(1)
    coeficientes = [coeficiente]
    for k in range(1, n + 1):
        M = sumar(multiplicar(A, M), I, coeficiente)
        coeficiente = -traza(multiplicar(A, M)) / k
        coeficientes.append(coeficiente)
    return coeficientes


def evaluar(coeficientes, x):
    resultado = Fraction(0)
    for c in coeficientes:
        resultado = resultado * x + c
    return resultado


def _dividir_por_raiz(coeficientes, raiz):
    """Cociente de dividir el polinomio entre (x − raiz) (división sintética)."""
    cociente, acumulado = [], Fraction(0)
    for c in coeficientes[:-1]:
        acumulado = acumulado * raiz + c
        cociente.append(acumulado)
    return cociente


def factorizar(coeficientes):
    """Separa las raíces racionales de un polinomio mónico.

    Devuelve (raices, resto): raices es una lista de (raíz, multiplicidad)
    ordenada de mayor a menor, y resto los coeficientes del factor que queda
    (sin raíces racionales). Las raíces se buscan cerca de las aproximaciones
    numéricas y se verifican de forma exacta, así que nunca hay falsos positivos.
    """
    coefs = [Fraction(c) for c in coeficientes]
    multiplicidades = {}
    while len(coefs) > 1 and coefs[-1] == 0:
        coefs.pop()
        multiplicidades[Fraction(0)] = multiplicidades.get(Fraction(0), 0) + 1

    encontrada = True
    while encontrada and len(coefs) > 1:
        encontrada = False
        # Una raíz racional p/q de un polinomio entero cumple que q divide al
        # coeficiente principal, que aquí es el mcm de los denominadores.
        principal = 1
        for c in coefs:
            principal = _mcm(principal, c.denominator)
        for z in np.roots([float(c) for c in coefs]):
            if abs(z.imag) > 1e-3 * max(1.0, abs(z)):
                continue
            candidatos = {Fraction(float(z.real)).limit_denominator(principal)}
            candidatos.update(
                Fraction(round(z.real * q), q)
                for q in range(1, min(principal, 50) + 1) if principal % q == 0
            )
            raiz = next((r for r in candidatos if evaluar(coefs, r) == 0), None)
            if raiz is not None:
                coefs = _dividir_por_raiz(coefs, raiz)
                multiplicidades[raiz] = multiplicidades.get(raiz, 0) + 1
                encontrada = True
                break

    raices = sorted(multiplicidades.items(), key=lambda par: -par[0])
    return raices, coefs


def extraer_cuadrado(s, limite=10**5):
    """Escribe el entero s ≥ 0 como k²·m con m lo más pequeño posible
    (buscando factores hasta `limite`). Devuelve (k, m)."""
    k, m, p = 1, s, 2
    while p * p <= m and p <= limite:
        while m % (p * p) == 0:
            m //= p * p
            k *= p
        p += 1
    return k, m


def raices_cuadratica(a, b, c):
    """Raíces de a·x² + b·x + c como u ± v·√m (o u ± v·√m·i si son complejas).

    Devuelve (u, v, m, compleja) con u, v fracciones (v > 0) y m entero sin
    factores cuadrados (al menos los pequeños).
    """
    discriminante = b * b - 4 * a * c
    u = -b / (2 * a)
    # √(p/q) = √(p·q)/q
    k, m = extraer_cuadrado(abs(discriminante.numerator) * discriminante.denominator)
    v = Fraction(k, discriminante.denominator) / abs(2 * a)
    return u, v, m, discriminante < 0
