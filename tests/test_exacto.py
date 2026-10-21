from fractions import Fraction as F

import numpy as np
import pytest

import exacto as ex
from calculos import calcular_espacios_propios, formatear_radical


def _matrices_aleatorias(cantidad=40, semilla=0):
    rng = np.random.default_rng(semilla)
    for _ in range(cantidad):
        n = int(rng.integers(2, 7))
        yield rng.integers(-6, 7, (n, n))


def test_operaciones_basicas():
    A = ex.a_fracciones([[1, 2], [3, 4]])
    assert ex.multiplicar(A, ex.identidad(2)) == A
    assert ex.transpuesta(A) == [[1, 3], [2, 4]]
    assert ex.sumar(A, A, -1) == [[0, 0], [0, 0]]
    assert ex.traza(A) == 5
    assert ex.potencia(ex.a_fracciones([[1, 1], [1, 0]]), 10) == [[89, 55], [55, 34]]


def test_determinante_inversa_y_rango():
    A = ex.a_fracciones([[F(1, 2), F(1, 3)], [F(1, 4), F(1, 5)]])
    assert ex.determinante(A) == F(1, 60)
    assert ex.inversa(A) == [[12, -20], [-15, 30]]
    singular = ex.a_fracciones([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    assert ex.determinante(singular) == 0
    assert ex.inversa(singular) is None
    assert ex.rango(singular) == 2


@pytest.mark.parametrize("A", list(_matrices_aleatorias()))
def test_coincide_con_numpy(A):
    exacta = ex.a_fracciones(A.tolist())
    n = len(A)
    assert ex.determinante(exacta) == round(np.linalg.det(A))
    assert ex.rango(exacta) == np.linalg.matrix_rank(A)
    coefs = ex.polinomio_caracteristico(exacta)
    assert np.allclose([float(c) for c in coefs], np.poly(A), rtol=1e-6, atol=1e-6)
    inv = ex.inversa(exacta)
    if inv is not None:
        assert ex.multiplicar(exacta, inv) == ex.identidad(n)


@pytest.mark.parametrize("A", list(_matrices_aleatorias(semilla=1)))
def test_espacios_propios_exactos_son_correctos(A):
    espacios = calcular_espacios_propios(A.astype(float), ex.a_fracciones(A.tolist()))
    assert sum(e.multiplicidad for e in espacios) == len(A)
    for e in espacios:
        for v in e.vectores:
            assert np.allclose(A @ v, e.valor * v, atol=1e-6 * max(1.0, np.max(np.abs(A))))


def test_escalonar_registra_los_pasos():
    R, pivotes, pasos = ex.escalonar(ex.a_fracciones([[1, 2, 3], [4, 5, 6], [7, 8, 9]]))
    assert R == [[1, 0, -1], [0, 1, 2], [0, 0, 0]]
    assert pivotes == [0, 1]
    assert pasos[0][1] == [("sumar", 1, -4, 0), ("sumar", 2, -7, 0)]
    assert pasos[1][1] == [("escalar", 1, F(-1, 3)), ("sumar", 0, -2, 1), ("sumar", 2, 6, 1)]
    assert pasos[2] == (2, [], None)          # columna sin pivote


def test_escalonar_intercambia_filas():
    _, _, pasos = ex.escalonar(ex.a_fracciones([[0, 1], [1, 0]]))
    assert pasos[0][1][0] == ("intercambiar", 0, 1)


def test_nucleo_a_enteros():
    assert ex.nucleo(ex.a_fracciones([[1, 2], [2, 4]])) == [[2, -1]]
    assert ex.a_enteros([F(1, 2), F(-1, 3)]) == [3, -2]
    assert ex.a_enteros([F(-2), F(4)]) == [1, -2]


def test_factorizar():
    # (x − 1)²·(x + 1/2)·(x² − 2) = x⁵ − (3/2)x⁴ − 2x³ + (7/2)x² − 1
    coefs = [1, F(-3, 2), -2, F(7, 2), 0, -1]
    raices, resto = ex.factorizar(coefs)
    assert raices == [(1, 2), (F(-1, 2), 1)]
    assert resto == [1, 0, -2]


def test_factorizar_raiz_cero_y_sin_raices_racionales():
    raices, resto = ex.factorizar([1, 0, 1, 0])          # x³ + x
    assert raices == [(0, 1)]
    assert resto == [1, 0, 1]


def test_extraer_cuadrado():
    assert ex.extraer_cuadrado(72) == (6, 2)
    assert ex.extraer_cuadrado(33) == (1, 33)
    assert ex.extraer_cuadrado(16) == (4, 1)


@pytest.mark.parametrize("coefs, esperado", [
    ((1, -5, -2), ["(5 + √33)/2", "(5 - √33)/2"]),
    ((1, 0, 1), ["i", "-i"]),
    ((1, 2, 5), ["-1 + 2i", "-1 - 2i"]),
    ((1, 0, -2), ["√2", "-√2"]),
    ((1, 0, 3), ["i√3", "-i√3"]),
    ((4, -4, -1), ["(1 + √2)/2", "(1 - √2)/2"]),
])
def test_radicales(coefs, esperado):
    u, v, m, compleja = ex.raices_cuadratica(*map(F, coefs))
    assert [formatear_radical(u, v, m, compleja, s) for s in (1, -1)] == esperado
